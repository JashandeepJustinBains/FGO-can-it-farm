"""
Servant Parser - Extract ascension-aware canonical data from servant JSONs

This module provides utilities to parse servant data from example_servant_data files
and convert them into ascension-aware canonical format with human-readable summaries.
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    filename='./outputs/parser.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Transform relationships (collectionNo -> transform_collectionNo)
TRANSFORM_MAPPING = {
    413: 4132,  # Aozaki Aoko -> Super Aozaki Aoko
}


def _unwrap_mongo_int(value: Any) -> Any:
    """Unwrap MongoDB $numberInt format to regular integers."""
    if isinstance(value, dict) and '$numberInt' in value:
        return int(value['$numberInt'])
    return value


def _unwrap_mongo_data(data: Any) -> Any:
    """Recursively unwrap MongoDB format data."""
    if isinstance(data, dict):
        if '$numberInt' in data:
            return int(data['$numberInt'])
        return {k: _unwrap_mongo_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_unwrap_mongo_data(item) for item in data]
    return data


def select_ascension_data(servant_json: dict, ascension: int) -> dict:
    """
    Extract ascension-aware canonical data from servant JSON.
    
    Args:
        servant_json: Raw servant data from example_servant_data
        ascension: Desired ascension level (1-based indexing)
        
    Returns:
        Canonical ascension data with standardized format
    """
    # Unwrap MongoDB format
    data = _unwrap_mongo_data(servant_json)
    
    collection_no = data.get('collectionNo', 0)
    name = data.get('name', 'Unknown')
    
    logging.info(f"Processing servant {collection_no} ({name}) for ascension {ascension}")
    
    # Extract basic metadata
    meta = {
        'collectionNo': collection_no,
        'name': name,
        'rarity': data.get('rarity', 0),
        'classId': data.get('classId', 0),
        'className': data.get('className', 'unknown'),
        'attribute': data.get('attribute', 'unknown')
    }
    
    # Extract global traits
    global_traits = []
    if 'traits' in data:
        for trait in data['traits']:
            global_traits.append({
                'id': trait.get('id', 0),
                'name': trait.get('name', 'unknown')
            })
    
    # Handle different input shapes for skills and noblePhantasms
    skills_data = data.get('skills', [])
    nps_data = data.get('noblePhantasms', [])
    passives_data = data.get('classPassive', [])
    
    # Determine the shape and extract ascension-specific data
    ascension_data = _extract_ascension_specific_data(
        skills_data, nps_data, passives_data, ascension, collection_no
    )
    
    # Check for transforms
    transforms = _detect_transforms(collection_no, data)
    
    # Build canonical structure
    canonical = {
        'meta': meta,
        'ascensions': [ascension_data],
        'global_traits': global_traits,
        'raw_keys': {
            'skills_path': 'skills',
            'noblePhantasms_path': 'noblePhantasms',
            'classPassive_path': 'classPassive',
            'source_format': 'legacy_single_list'
        }
    }
    
    if transforms:
        canonical['transforms'] = transforms
    
    return canonical


def _extract_ascension_specific_data(skills_data: List, nps_data: List, 
                                   passives_data: List, ascension: int, 
                                   collection_no: int) -> dict:
    """Extract data for specific ascension, handling different input shapes."""
    
    # For now, treat all as legacy single-list since that's what we see in examples
    # In the future, this would detect list-of-lists or ascensions arrays
    
    logging.info(f"Using legacy single-list format for servant {collection_no}")
    
    # Extract skills
    skills = []
    for i, skill in enumerate(skills_data):
        if i < 3:  # Most servants have 3 skills
            skills.append(extract_skill_summary(skill))
    
    # Extract noble phantasms
    noble_phantasms = []
    for np in nps_data:
        noble_phantasms.append(extract_np_summary(np))
    
    # Extract passives
    passives = []
    for passive in passives_data:
        passives.append(_extract_passive_summary(passive))
    
    return {
        'ascension_index': ascension,
        'skills': skills,
        'noblePhantasms': noble_phantasms,
        'passives': passives,
        'stat_overrides': {},  # Would be populated if found in data
        'transforms': [],
        'special_flags': [],
        'raw_keys': {
            'skills_index': 'direct',
            'np_index': 'direct',
            'passives_index': 'direct'
        }
    }


def extract_skill_summary(skill_obj: dict) -> dict:
    """
    Extract canonical skill summary from skill object.
    
    Args:
        skill_obj: Raw skill data
        
    Returns:
        Canonical skill descriptor
    """
    skill_id = skill_obj.get('id', 0)
    name = skill_obj.get('name', 'Unknown Skill')
    
    # Extract cooldown (usually at index 9 for max level)
    cooldown_data = skill_obj.get('coolDown', [])
    if isinstance(cooldown_data, list) and len(cooldown_data) > 9:
        cooldown = cooldown_data[9]
    else:
        cooldown = cooldown_data[0] if cooldown_data else 0
    
    # Check if this is an upgraded skill
    strength_status = skill_obj.get('strengthStatus', 0)
    upgraded = strength_status > 0
    
    # Extract functions/effects
    functions = skill_obj.get('functions', [])
    
    return {
        'id': skill_id,
        'display_name': name,
        'cooldown': cooldown,
        'upgraded': upgraded,
        'raw_effects': functions,
        'original_data': skill_obj  # Preserve original for debugging
    }


def extract_np_summary(np_obj: dict) -> dict:
    """
    Extract canonical noble phantasm summary from NP object.
    
    Args:
        np_obj: Raw noble phantasm data
        
    Returns:
        Canonical NP descriptor
    """
    name = np_obj.get('name', 'Unknown Noble Phantasm')
    card_type = np_obj.get('card', 'unknown')
    
    # Extract hit distribution
    hits = []
    damage_figures = np_obj.get('npDistribution', [])
    if damage_figures:
        hits = damage_figures
    
    # Extract functions/effects
    functions = np_obj.get('functions', [])
    
    # Extract overcharge matrix/map
    oc_matrix = None
    # Look for OC data in functions
    for func in functions:
        if 'svals' in func:
            # This represents the base values
            if 'svals2' in func or 'svals3' in func:
                # Has overcharge levels
                oc_matrix = {
                    'svals1': func.get('svals', []),
                    'svals2': func.get('svals2', []),
                    'svals3': func.get('svals3', []),
                    'svals4': func.get('svals4', []),
                    'svals5': func.get('svals5', [])
                }
                break
    
    # Determine scope
    scope = 'unknown'
    for func in functions:
        target_type = func.get('funcTargetType', '')
        if 'enemy' in target_type.lower():
            scope = 'enemy'
            break
        elif 'self' in target_type.lower():
            scope = 'self'
            break
        elif 'ptall' in target_type.lower():
            scope = 'ptAll'
            break
    
    result = {
        'name': name,
        'card_type': card_type,
        'hits': hits,
        'effects': functions,
        'scope': scope,
        'se_flags': [],  # Special effect flags
        'raw': np_obj
    }
    
    if oc_matrix:
        result['oc_matrix'] = oc_matrix
    
    return result


def _extract_passive_summary(passive_obj: dict) -> dict:
    """Extract summary from passive skill object."""
    return {
        'id': passive_obj.get('id', 0),
        'name': passive_obj.get('name', 'Unknown Passive'),
        'detail': passive_obj.get('detail', ''),
        'raw': passive_obj
    }


def _detect_transforms(collection_no: int, data: dict) -> List[dict]:
    """
    Detect transform relationships for the servant.
    
    Args:
        collection_no: Current servant's collection number
        data: Servant data
        
    Returns:
        List of transform descriptors
    """
    transforms = []
    
    # Check if this servant transforms into another
    if collection_no in TRANSFORM_MAPPING:
        target_collection_no = TRANSFORM_MAPPING[collection_no]
        transforms.append({
            'trigger': 'first_np_use',
            'type': 'full_transform',
            'target_collection_no': target_collection_no,
            'preserve_cooldowns': True,
            'description': f"Transforms into collectionNo {target_collection_no}"
        })
        logging.info(f"Detected transform: {collection_no} -> {target_collection_no}")
    
    return transforms


def generate_markdown_summary(canonical_data: dict, ascension: int) -> str:
    """
    Generate human-readable markdown summary for ascension.
    
    Args:
        canonical_data: Canonical servant data
        ascension: Ascension level
        
    Returns:
        Markdown formatted summary
    """
    meta = canonical_data['meta']
    ascension_data = canonical_data['ascensions'][0]
    
    lines = [
        f"# {meta['name']} (Collection No. {meta['collectionNo']}) - Ascension {ascension}",
        "",
        f"**Class:** {meta['className']} (ID: {meta['classId']})",
        f"**Rarity:** {meta['rarity']}★",
        f"**Attribute:** {meta['attribute']}",
        "",
        "## Skills",
        ""
    ]
    
    # Add skills
    for i, skill in enumerate(ascension_data['skills'], 1):
        upgraded_text = " (upgraded)" if skill['upgraded'] else ""
        lines.extend([
            f"### Skill {i}: {skill['display_name']}{upgraded_text}",
            f"- **Cooldown:** {skill['cooldown']} turns",
            f"- **ID:** {skill['id']}",
            f"- **Effects:** {len(skill['raw_effects'])} function(s)",
            ""
        ])
    
    # Add noble phantasms
    lines.extend([
        "## Noble Phantasms",
        ""
    ])
    
    for i, np in enumerate(ascension_data['noblePhantasms'], 1):
        lines.extend([
            f"### NP {i}: {np['name']}",
            f"- **Card Type:** {np['card_type']}",
            f"- **Hits:** {len(np['hits'])} hits with distribution {np['hits']}",
            f"- **Scope:** {np['scope']}",
            f"- **Effects:** {len(np['effects'])} function(s)",
            ""
        ])
        
        if 'oc_matrix' in np:
            lines.append("- **Has Overcharge scaling**")
            lines.append("")
    
    # Add transforms if any
    if 'transforms' in canonical_data and canonical_data['transforms']:
        lines.extend([
            "## Transforms",
            ""
        ])
        
        for transform in canonical_data['transforms']:
            lines.extend([
                f"- **Trigger:** {transform['trigger']}",
                f"- **Type:** {transform['type']}",
                f"- **Target:** Collection No. {transform['target_collection_no']}",
                f"- **Preserve Cooldowns:** {transform['preserve_cooldowns']}",
                ""
            ])
    
    # Add passive skills
    if ascension_data['passives']:
        lines.extend([
            "## Class Passives",
            ""
        ])
        
        for passive in ascension_data['passives']:
            lines.extend([
                f"- **{passive['name']}** (ID: {passive['id']})",
                ""
            ])
    
    return "\n".join(lines)


def process_servant_file(file_path: str, output_dir: str = "parsed") -> None:
    """
    Process a single servant file and generate all ascension outputs.
    
    Args:
        file_path: Path to servant JSON file
        output_dir: Directory to save parsed outputs
    """
    os.makedirs(output_dir, exist_ok=True)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        servant_data = json.load(f)
    
    collection_no = _unwrap_mongo_int(servant_data.get('collectionNo', 0))
    
    # Process multiple ascensions (typically 1-4)
    for ascension in range(1, 5):
        try:
            canonical_data = select_ascension_data(servant_data, ascension)
            
            # Generate markdown summary
            markdown_content = generate_markdown_summary(canonical_data, ascension)
            
            # Save markdown file
            md_filename = f"{collection_no}-asc{ascension}.md"
            md_path = os.path.join(output_dir, md_filename)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Save JSON file
            json_filename = f"{collection_no}-asc{ascension}.json"
            json_path = os.path.join(output_dir, json_filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(canonical_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Generated {md_filename} and {json_filename}")
            
        except Exception as e:
            logging.error(f"Error processing {file_path} ascension {ascension}: {e}")


if __name__ == "__main__":
    # Process all example files
    example_dir = "example_servant_data"
    if os.path.exists(example_dir):
        for filename in os.listdir(example_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(example_dir, filename)
                print(f"Processing {filename}...")
                process_servant_file(file_path)
        print("Processing complete. Check the 'parsed' directory for outputs.")
    else:
        print(f"Example directory '{example_dir}' not found.")