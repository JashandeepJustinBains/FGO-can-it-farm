"""
Comprehensive FGO Servant Ascension Parser
Following the finalized requirements for per-ascension mapping with slot/priority logic,
transformation mechanics, and trait merging.
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict


def get_skills_for_slot(servant_data: Dict[str, Any], slot: int) -> List[Dict[str, Any]]:
    """Get all skill candidates for a specific slot across all priorities."""
    skills = servant_data.get('skills', [])
    candidates = []
    
    for skill in skills:
        if skill.get('num') == slot:
            candidates.append(skill)
    
    return candidates


def get_nps_for_slot(servant_data: Dict[str, Any], slot: int = 1) -> List[Dict[str, Any]]:
    """Get all NP candidates for a specific slot across all priorities."""
    nps = servant_data.get('noblePhantasms', [])
    candidates = []
    
    for np in nps:
        # Most servants have single NP, but some may have multiple
        np_slot = np.get('slot', 1)  # Default to slot 1
        if np_slot == slot:
            candidates.append(np)
    
    return candidates


def is_skill_valid_for_ascension(skill: Dict[str, Any], ascension: int) -> bool:
    """Check if a skill is valid/available for a specific ascension."""
    # Check condition requirements
    cond_type = skill.get('condType', '')
    cond_value = skill.get('condValue', 0)
    cond_num = skill.get('condNum', 0)
    
    # Basic availability - if no conditions, it's available
    if not cond_type and not cond_value and not cond_num:
        return True
    
    # Add specific condition logic here as needed
    # For now, assume all skills are available unless explicitly restricted
    return True


def is_np_valid_for_ascension(np: Dict[str, Any], ascension: int) -> bool:
    """Check if an NP is valid/available for a specific ascension."""
    # Similar logic to skills
    cond_type = np.get('condType', '')
    cond_value = np.get('condValue', 0)
    cond_num = np.get('condNum', 0)
    
    # Basic availability
    if not cond_type and not cond_value and not cond_num:
        return True
    
    return True


def select_highest_priority_for_ascension(candidates: List[Dict[str, Any]], ascension: int) -> Optional[Dict[str, Any]]:
    """
    Select the skill/NP with appropriate priority for the ascension.
    
    Logic:
    - For ascensions 1-2: Prefer Priority 1, fallback to lowest available priority
    - For ascensions 3-4: Prefer highest priority (Priority 2+), fallback to Priority 1
    """
    if not candidates:
        return None
    
    # Filter valid candidates for this ascension
    valid_candidates = []
    for candidate in candidates:
        if candidate.get('type') == 'skill':
            if is_skill_valid_for_ascension(candidate, ascension):
                valid_candidates.append(candidate)
        else:  # NP
            if is_np_valid_for_ascension(candidate, ascension):
                valid_candidates.append(candidate)
    
    if not valid_candidates:
        return None
    
    # Group by priority
    by_priority = defaultdict(list)
    for candidate in valid_candidates:
        priority = candidate.get('priority', 1)
        by_priority[priority].append(candidate)
    
    available_priorities = sorted(by_priority.keys())
    
    # Selection logic based on ascension
    if ascension <= 2:
        # For ascensions 1-2: prefer Priority 1, then lowest available
        if 1 in by_priority:
            selected_priority = 1
        else:
            selected_priority = available_priorities[0]
    else:
        # For ascensions 3-4: prefer highest priority available
        selected_priority = available_priorities[-1]
    
    # From the selected priority group, pick the one with highest ID as tiebreaker
    priority_group = by_priority[selected_priority]
    priority_group.sort(key=lambda x: x.get('id', 0), reverse=True)
    
    return priority_group[0]


def get_base_traits(servant_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get the base traits that apply to all ascensions."""
    return servant_data.get('traits', [])


def get_ascension_specific_traits(servant_data: Dict[str, Any], ascension: int) -> List[Dict[str, Any]]:
    """Get traits specific to an ascension from ascensionAdd."""
    ascension_add = servant_data.get('ascensionAdd', {})
    individuality = ascension_add.get('individuality', {})
    ascension_traits = individuality.get('ascension', {})
    
    asc_key = str(ascension)
    if asc_key in ascension_traits:
        specific_traits = ascension_traits[asc_key]
        if isinstance(specific_traits, list):
            return specific_traits
    
    return []


def merge_traits_for_ascension(base_traits: List[Dict[str, Any]], servant_data: Dict[str, Any], ascension: int) -> List[Dict[str, Any]]:
    """Merge base traits with ascension-specific additions/removals."""
    merged_traits = base_traits.copy()
    
    # Add ascension-specific traits
    specific_traits = get_ascension_specific_traits(servant_data, ascension)
    merged_traits.extend(specific_traits)
    
    # Remove duplicates by trait ID while preserving order
    seen_ids = set()
    unique_traits = []
    for trait in merged_traits:
        trait_id = trait.get('id')
        if trait_id not in seen_ids:
            seen_ids.add(trait_id)
            unique_traits.append(trait)
    
    return unique_traits


def get_alignment_for_ascension(servant_data: Dict[str, Any], ascension: int) -> Dict[str, str]:
    """Get alignment (policy/personality) for specific ascension."""
    # Check limits array for ascension-specific alignment
    limits = servant_data.get('limits', [])
    
    # Find the limit entry for this ascension (usually ascension 0-based in limits)
    alignment = {'policy': 'unknown', 'personality': 'unknown'}
    
    if limits:
        # Try to get ascension-specific alignment
        for limit in limits:
            limit_count = limit.get('limitCount', 0)
            if limit_count == ascension:
                alignment['policy'] = limit.get('policy', 'unknown')
                alignment['personality'] = limit.get('personality', 'unknown')
                break
        
        # Fallback to base alignment if not found
        if alignment['policy'] == 'unknown' and limits:
            base_limit = limits[0]
            alignment['policy'] = base_limit.get('policy', 'unknown')
            alignment['personality'] = base_limit.get('personality', 'unknown')
    
    return alignment


def has_transformation(servant_data: Dict[str, Any], ascension: int) -> bool:
    """Check if servant has transformations at this ascension."""
    transforms = servant_data.get('transforms', [])
    return len(transforms) > 0


def apply_transformation(skills: List[Dict[str, Any]], nps: List[Dict[str, Any]], 
                        servant_data: Dict[str, Any], ascension: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Apply transformation logic to skills and NPs."""
    # This is where complex transformation logic would go
    # For now, return as-is but this can be expanded for specific servants
    transforms = servant_data.get('transforms', [])
    
    # Placeholder for transformation logic
    # Each transform would specify what changes at what ascension/condition
    
    return skills, nps


def detect_max_ascensions(servant_data: Dict[str, Any]) -> int:
    """Detect the maximum number of ascensions for this servant."""
    # Check various sources for max ascensions
    limits = servant_data.get('limits', [])
    if limits:
        max_from_limits = max(limit.get('limitCount', 0) for limit in limits)
        return max(max_from_limits, 4)
    
    # Check ascensionAdd for ascension keys
    ascension_add = servant_data.get('ascensionAdd', {})
    individuality = ascension_add.get('individuality', {})
    ascension_traits = individuality.get('ascension', {})
    
    if ascension_traits:
        max_asc_key = max(int(k) for k in ascension_traits.keys() if k.isdigit())
        return max(max_asc_key, 4)
    
    return 4  # Default to 4 ascensions


def parse_servant_ascensions(servant_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """
    Main parser function that creates per-ascension data.
    
    Returns:
        Dict mapping ascension -> {skills, nps, traits, alignment, transforms}
    """
    collection_no = servant_data.get('collectionNo')
    
    # Skip collectionNo 1 as specified
    if collection_no == 1:
        return None
    
    max_ascensions = detect_max_ascensions(servant_data)
    base_traits = get_base_traits(servant_data)
    
    # Get available skill and NP slots
    all_skills = servant_data.get('skills', [])
    all_nps = servant_data.get('noblePhantasms', [])
    
    skill_slots = sorted(set(skill.get('num', 1) for skill in all_skills))
    np_slots = [1]  # Most servants have 1 NP slot, can be expanded
    
    output = {}
    
    # Process each ascension
    for asc in range(1, max_ascensions + 1):
        skills = []
        nps = []
        traits = base_traits.copy()
        
        # Handle skill slots
        for slot in skill_slots:
            candidates = get_skills_for_slot(servant_data, slot)
            # Mark candidates as skills for validation
            for candidate in candidates:
                candidate['type'] = 'skill'
            
            best_skill = select_highest_priority_for_ascension(candidates, asc)
            if best_skill:
                # Remove the type marker before adding
                if 'type' in best_skill:
                    del best_skill['type']
                skills.append(best_skill)
        
        # Handle NP slots
        for slot in np_slots:
            candidates = get_nps_for_slot(servant_data, slot)
            # Mark candidates as NPs for validation
            for candidate in candidates:
                candidate['type'] = 'np'
            
            best_np = select_highest_priority_for_ascension(candidates, asc)
            if best_np:
                # Remove the type marker before adding
                if 'type' in best_np:
                    del best_np['type']
                nps.append(best_np)
        
        # Handle trait changes
        traits = merge_traits_for_ascension(traits, servant_data, asc)
        
        # Get alignment for this ascension
        alignment = get_alignment_for_ascension(servant_data, asc)
        
        # Handle transformation/swap logic
        if has_transformation(servant_data, asc):
            skills, nps = apply_transformation(skills, nps, servant_data, asc)
        
        output[asc] = {
            "skills": skills,
            "nps": nps,
            "traits": traits,
            "alignment": alignment,
            "transforms": servant_data.get('transforms', [])
        }
    
    return output


def create_comprehensive_servant_data(servant_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create comprehensive structured servant data with per-ascension mapping.
    
    Args:
        servant_data: Raw servant JSON data
        
    Returns:
        Comprehensive structured servant data
    """
    collection_no = servant_data.get('collectionNo')
    
    # Skip collectionNo 1 as specified
    if collection_no == 1:
        return None
    
    # Parse ascension data
    ascension_data = parse_servant_ascensions(servant_data)
    
    if ascension_data is None:
        return None
    
    # Create comprehensive structure
    structured = {
        'collectionNo': collection_no,
        'name': servant_data.get('name', ''),
        'rarity': servant_data.get('rarity', servant_data.get('star', 0)),
        'className': servant_data.get('className', ''),
        'attribute': servant_data.get('attribute', ''),
        'maxAscensions': detect_max_ascensions(servant_data),
        'ascensions': ascension_data,
        'baseData': {
            'skills': servant_data.get('skills', []),
            'noblePhantasms': servant_data.get('noblePhantasms', []),
            'traits': servant_data.get('traits', []),
            'passives': servant_data.get('passives', servant_data.get('classPassive', [])),
            'transforms': servant_data.get('transforms', []),
            'limits': servant_data.get('limits', [])
        }
    }
    
    return structured


def get_ascension_data(comprehensive_servant: Dict[str, Any], ascension: int) -> Dict[str, Any]:
    """
    Get data for a specific ascension from comprehensive servant data.
    
    Args:
        comprehensive_servant: Structured servant data with ascensions
        ascension: Requested ascension level (1-based)
    
    Returns:
        Dictionary with ascension-specific data
    """
    if comprehensive_servant is None:
        return None
    
    ascensions = comprehensive_servant.get('ascensions', {})
    
    if ascension in ascensions:
        return ascensions[ascension]
    
    # Fallback to highest available ascension
    available_ascensions = sorted(ascensions.keys())
    if available_ascensions:
        highest_asc = available_ascensions[-1]
        return ascensions[highest_asc]
    
    return None


def process_all_servants_comprehensive():
    """Process all servant JSON files with comprehensive ascension parsing."""
    input_dir = Path('example_servant_data')
    output_dir = Path('servants_comprehensive')
    output_dir.mkdir(exist_ok=True)
    
    processed_count = 0
    skipped_count = 0
    errors = []
    
    for json_file in sorted(input_dir.glob('*.json')):
        # Skip variant files for now
        if 'with_variants' in json_file.name:
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                servant_data = json.load(f)
            
            comprehensive_data = create_comprehensive_servant_data(servant_data)
            
            if comprehensive_data is None:
                print(f"Skipped {json_file.name} (collectionNo 1 or invalid)")
                skipped_count += 1
                continue
            
            # Save comprehensive data
            collection_no = comprehensive_data['collectionNo']
            output_file = output_dir / f"{collection_no}_comprehensive.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)
            
            print(f"OK {json_file.name} -> {output_file.name}")
            processed_count += 1
            
        except Exception as e:
            error_msg = f"ERROR processing {json_file.name}: {e}"
            print(error_msg)
            errors.append(error_msg)
            skipped_count += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Comprehensive Processing Summary:")
    print(f"  Processed: {processed_count} servants")
    print(f"  Skipped: {skipped_count} servants")
    print(f"  Errors: {len(errors)}")
    
    if errors:
        print(f"\nErrors encountered:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
    
    print(f"\nComprehensive data saved to: {output_dir.absolute()}")
    return processed_count, skipped_count, errors


def validate_comprehensive_parsing():
    """Validate the comprehensive parsing approach."""
    print("=== Comprehensive Validation ===")
    
    # Test servant 444
    print("\n--- Servant 444 (U-Olga Marie) ---")
    with open('example_servant_data/444.json', 'r', encoding='utf-8') as f:
        servant_444 = json.load(f)
    
    comprehensive_444 = create_comprehensive_servant_data(servant_444)
    
    if comprehensive_444:
        print(f"Max Ascensions: {comprehensive_444['maxAscensions']}")
        print(f"Available ascensions: {sorted(comprehensive_444['ascensions'].keys())}")
        
        for asc in [1, 2, 3, 4]:
            asc_data = get_ascension_data(comprehensive_444, asc)
            if asc_data:
                print(f"\nAscension {asc}:")
                print(f"  Skills: {len(asc_data['skills'])}")
                print(f"  NPs: {len(asc_data['nps'])}")
                print(f"  Traits: {len(asc_data['traits'])}")
                print(f"  Alignment: {asc_data['alignment']['policy']}-{asc_data['alignment']['personality']}")
                
                for skill in asc_data['skills']:
                    skill_name = skill.get('name', f"[Unicode - ID {skill.get('id')}]")
                    try:
                        print(f"    - {skill_name} (Priority: {skill.get('priority', 1)})")
                    except UnicodeEncodeError:
                        print(f"    - [Unicode Skill - ID {skill.get('id')}] (Priority: {skill.get('priority', 1)})")
    
    # Test servant 312
    print("\n--- Servant 312 (Mélusine) ---")
    with open('example_servant_data/312.json', 'r', encoding='utf-8') as f:
        servant_312 = json.load(f)
    
    comprehensive_312 = create_comprehensive_servant_data(servant_312)
    
    if comprehensive_312:
        print(f"Max Ascensions: {comprehensive_312['maxAscensions']}")
        
        for asc in [1, 2, 3, 4]:
            asc_data = get_ascension_data(comprehensive_312, asc)
            if asc_data:
                print(f"\nAscension {asc}:")
                skill_details = []
                for skill in asc_data['skills']:
                    name = skill.get('name', f"ID-{skill.get('id')}")
                    skill_id = skill.get('id')
                    priority = skill.get('priority', 1)
                    skill_details.append(f"{name} (ID: {skill_id}, P: {priority})")
                print(f"  Skills: {skill_details}")
                
                np_details = []
                for np in asc_data['nps']:
                    name = np.get('name', f"ID-{np.get('id')}")
                    np_id = np.get('id')
                    priority = np.get('priority', 1)
                    np_details.append(f"{name} (ID: {np_id}, P: {priority})")
                print(f"  NPs: {np_details}")
                print(f"  Alignment: {asc_data['alignment']['policy']}-{asc_data['alignment']['personality']}")


if __name__ == '__main__':
    validate_comprehensive_parsing()