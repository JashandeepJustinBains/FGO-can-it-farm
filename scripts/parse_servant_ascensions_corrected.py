"""
Corrected parser for ascension-specific servant data.

Based on analysis of the actual JSON structure, this parser correctly maps:
- Skills/NPs by priority (Priority 1 = ascensions 1-2, Priority 2+ = ascensions 3-4)  
- Traits by combining base traits with ascensionAdd.individuality.ascension data
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict


def parse_traits_by_ascension(servant_data: Dict[str, Any]) -> Dict[int, List[str]]:
    """Parse traits for each ascension using ascensionAdd structure."""
    traits_by_ascension = {}
    
    # Get base traits that apply to all ascensions
    base_traits = servant_data.get('traits', [])
    
    # Get ascension-specific trait additions
    ascension_add = servant_data.get('ascensionAdd', {})
    individuality = ascension_add.get('individuality', {})
    ascension_traits = individuality.get('ascension', {})
    
    # Process each ascension (0-4)
    for asc in range(5):  # 0, 1, 2, 3, 4
        ascension_traits_list = base_traits.copy()
        
        # Add ascension-specific traits if they exist
        asc_key = str(asc)
        if asc_key in ascension_traits:
            ascension_specific = ascension_traits[asc_key]
            if isinstance(ascension_specific, list):
                ascension_traits_list.extend(ascension_specific)
        
        traits_by_ascension[asc] = ascension_traits_list
    
    return traits_by_ascension


def group_skills_by_priority_and_slot(skills: List[Dict[str, Any]]) -> Dict[int, Dict[int, Dict[str, Any]]]:
    """
    Group skills by priority and skill slot (num).
    
    Returns: {priority: {slot: skill_data}}
    """
    grouped = defaultdict(dict)
    
    for skill in skills:
        priority = skill.get('priority', 1)
        skill_num = skill.get('num', 0)  # Skill slot number
        
        # For skills with same slot and different priorities, store by priority
        grouped[priority][skill_num] = skill
    
    return dict(grouped)


def group_nps_by_priority(nps: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """Group Noble Phantasms by priority."""
    grouped = defaultdict(list)
    
    for np in nps:
        priority = np.get('priority', 1)
        grouped[priority].append(np)
    
    return dict(grouped)


def map_priority_to_ascensions(priorities: List[int], skill_slots_by_priority: Dict[int, Dict[int, Any]] = None) -> Dict[int, List[int]]:
    """
    Map skill/NP priorities to ascension ranges.
    
    Rules:
    1. If only one priority: all ascensions use it
    2. For skills with overlapping slots: higher priority replaces lower priority in later ascensions  
    3. For skills with non-overlapping slots: all continue throughout their active ascensions
    4. For NPs: always replacement pattern by priority
    """
    priority_to_ascensions = {}
    sorted_priorities = sorted(priorities)
    
    if len(sorted_priorities) == 1:
        # All ascensions use the same skills/NPs
        priority_to_ascensions[sorted_priorities[0]] = [1, 2, 3, 4]
    elif len(sorted_priorities) == 2:
        # Check if this is skills and analyze slot overlap
        if skill_slots_by_priority is not None:
            # Get slots for each priority
            slots_p1 = set(skill_slots_by_priority.get(sorted_priorities[0], {}).keys())
            slots_p2 = set(skill_slots_by_priority.get(sorted_priorities[1], {}).keys())
            
            # Determine ascensions for each priority
            # Lower priority (1) active in ascensions 1-2
            # For ascensions 3-4: keep non-overlapping slots from p1, add all slots from p2
            priority_to_ascensions[sorted_priorities[0]] = [1, 2]
            priority_to_ascensions[sorted_priorities[1]] = [3, 4]
            
            # If there are non-overlapping slots in p1, they continue to ascensions 3-4
            non_overlapping_p1_slots = slots_p1 - slots_p2
            if non_overlapping_p1_slots:
                # Extend p1 to ascensions 3-4 (will be filtered by slot later)
                priority_to_ascensions[sorted_priorities[0]] = [1, 2, 3, 4]
        else:
            # For NPs or when no slot info: replacement pattern
            priority_to_ascensions[sorted_priorities[0]] = [1, 2]
            priority_to_ascensions[sorted_priorities[1]] = [3, 4]
    else:
        # More complex mapping - use priority order with replacement pattern
        for i, priority in enumerate(sorted_priorities):
            if i == 0:
                priority_to_ascensions[priority] = [1, 2]
            else:
                priority_to_ascensions[priority] = [3, 4]
    
    return priority_to_ascensions


def create_structured_servant_data(servant_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create structured servant data with correct ascension mapping.
    
    Args:
        servant_data: Raw servant JSON data
        
    Returns:
        Structured servant data with ascension-aware skills, NPs, and traits
    """
    collection_no = servant_data.get('collectionNo')
    
    # Skip collectionNo 1 as specified
    if collection_no == 1:
        return None
    
    # Parse traits by ascension
    traits_by_ascension = parse_traits_by_ascension(servant_data)
    
    # Group skills by priority and slot
    skills = servant_data.get('skills', [])
    skills_by_priority = group_skills_by_priority_and_slot(skills)
    
    # Group NPs by priority  
    nps = servant_data.get('noblePhantasms', [])
    nps_by_priority = group_nps_by_priority(nps)
    
    # Map priorities to ascensions
    skill_priorities = list(skills_by_priority.keys())
    np_priorities = list(nps_by_priority.keys())
    
    skill_priority_mapping = map_priority_to_ascensions(skill_priorities, skills_by_priority)
    np_priority_mapping = map_priority_to_ascensions(np_priorities)
    
    # Create structured data
    structured = {
        'collectionNo': collection_no,
        'name': servant_data.get('name', ''),
        'rarity': servant_data.get('rarity', servant_data.get('star', 0)),
        'className': servant_data.get('className', ''),
        'attribute': servant_data.get('attribute', ''),
        'maxAscensions': 4,
        'atkGrowth': servant_data.get('atkGrowth', servant_data.get('atkgrowth', [])),
        'skillsByPriority': skills_by_priority,
        'npsByPriority': nps_by_priority,
        'skillPriorityMapping': skill_priority_mapping,
        'npPriorityMapping': np_priority_mapping,
        'traits': traits_by_ascension,
        'passives': servant_data.get('passives', servant_data.get('classPassive', [])),
        'transforms': servant_data.get('transforms', [])
    }
    
    return structured


def select_ascension_data_enhanced(structured_servant: Dict[str, Any], ascension: int) -> Dict[str, Any]:
    """
    Select ascension-specific data from structured servant data.
    
    Args:
        structured_servant: Structured servant data
        ascension: Requested ascension level (1-based)
    
    Returns:
        Dictionary with ascension-specific skills, NPs, traits, etc.
    """
    result = {
        'skills': [],
        'noblePhantasms': [],
        'passives': structured_servant.get('passives', []),
        'transforms': structured_servant.get('transforms', []),
        'traits': []
    }
    
    # Select skills for this ascension with slot-based conflict resolution
    skills_by_priority = structured_servant.get('skillsByPriority', {})
    skill_priority_mapping = structured_servant.get('skillPriorityMapping', {})
    
    # Collect all applicable skills, then resolve conflicts by slot
    applicable_skills_by_slot = {}
    
    for priority, ascensions in skill_priority_mapping.items():
        if ascension in ascensions:
            priority_skills = skills_by_priority.get(priority, {})
            for slot, skill in priority_skills.items():
                # For slot conflicts, higher priority wins
                if slot not in applicable_skills_by_slot or priority > applicable_skills_by_slot[slot]['priority']:
                    applicable_skills_by_slot[slot] = {
                        'skill': skill,
                        'priority': priority
                    }
    
    # Add skills in slot order
    for slot in sorted(applicable_skills_by_slot.keys()):
        result['skills'].append(applicable_skills_by_slot[slot]['skill'])
    
    # Select Noble Phantasms for this ascension
    nps_by_priority = structured_servant.get('npsByPriority', {})
    np_priority_mapping = structured_servant.get('npPriorityMapping', {})
    
    for priority, ascensions in np_priority_mapping.items():
        if ascension in ascensions:
            result['noblePhantasms'].extend(nps_by_priority.get(priority, []))
    
    # Select traits for this ascension
    traits_by_asc = structured_servant.get('traits', {})
    result['traits'] = traits_by_asc.get(ascension, traits_by_asc.get(str(ascension), []))
    
    return result


def process_all_servants():
    """Process all servant JSON files and create structured data."""
    input_dir = Path('example_servant_data')
    output_dir = Path('servants')
    output_dir.mkdir(exist_ok=True)
    
    processed_count = 0
    skipped_count = 0
    
    for json_file in input_dir.glob('*.json'):
        # Skip variant files for now
        if 'with_variants' in json_file.name:
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                servant_data = json.load(f)
            
            structured_data = create_structured_servant_data(servant_data)
            
            if structured_data is None:
                print(f"Skipped {json_file.name} (collectionNo 1 or invalid)")
                skipped_count += 1
                continue
            
            # Save structured data
            collection_no = structured_data['collectionNo']
            output_file = output_dir / f"{collection_no}_structured.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, ensure_ascii=False, indent=2)
            
            print(f"Processed {json_file.name} -> {output_file.name}")
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")
            skipped_count += 1
    
    print(f"\nProcessing complete: {processed_count} processed, {skipped_count} skipped")


def validate_servant_parsing():
    """Validate parsing of test servants."""
    # Test servant 444
    print("=== Validating Servant 444 ===")
    
    with open('example_servant_data/444.json', 'r', encoding='utf-8') as f:
        servant_444 = json.load(f)
    
    structured_444 = create_structured_servant_data(servant_444)
    
    print(f"Max Ascensions: {structured_444['maxAscensions']}")
    print(f"Structure Type: priority-based")
    print(f"Skills by priority: {list(structured_444['skillsByPriority'].keys())}")
    print(f"NPs by priority: {list(structured_444['npsByPriority'].keys())}")
    
    # Test ascension selection
    for asc in [1, 2, 3, 4]:
        asc_data = select_ascension_data_enhanced(structured_444, asc)
        print(f"\nAscension {asc}:")
        print(f"  Skills: {len(asc_data['skills'])}")
        print(f"  NPs: {len(asc_data['noblePhantasms'])}")
        print(f"  Traits: {len(asc_data['traits'])}")
        
        for skill in asc_data['skills']:
            skill_name = skill.get('name', f"[Unicode - ID {skill.get('id')}]")
            try:
                print(f"    - {skill_name}")
            except UnicodeEncodeError:
                print(f"    - [Unicode Skill - ID {skill.get('id')}]")
    
    # Test servant 312
    print("\n=== Validating Servant 312 ===")
    
    with open('example_servant_data/312.json', 'r', encoding='utf-8') as f:
        servant_312 = json.load(f)
    
    structured_312 = create_structured_servant_data(servant_312)
    
    print(f"Max Ascensions: {structured_312['maxAscensions']}")
    print(f"Structure Type: priority-based")
    
    # Test transformation mechanics
    for asc in [1, 2, 3, 4]:
        asc_data = select_ascension_data_enhanced(structured_312, asc)
        print(f"\nAscension {asc}:")
        skill_names = []
        for skill in asc_data['skills']:
            skill_names.append(skill.get('name', f"[ID {skill.get('id')}]"))
        print(f"  Skills: {skill_names}")
        
        np_names = []
        for np in asc_data['noblePhantasms']:
            np_names.append(np.get('name', f"[ID {np.get('id')}]"))
        print(f"  NPs: {np_names}")


if __name__ == '__main__':
    validate_servant_parsing()