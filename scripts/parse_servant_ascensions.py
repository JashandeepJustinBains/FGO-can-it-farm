def parse_np_effects(np_data: Dict[str, Any]) -> List[Dict]:
    """
    Parse NP functions to extract effects with OC/NP level scaling as self-describing key-value pairs.
    """
    effects = []
    for func in np_data.get('functions', []):
        oc_matrix = []
        effect_label = func.get('funcLabel') or func.get('funcType') or 'effect'
        for oc in range(1, 6):
            svals_key = f'svals{oc}' if oc > 1 else 'svals'
            svals_array = func.get(svals_key, func.get('svals', []))
            oc_row = []
            for np_level in range(1, 6):
                if isinstance(svals_array, list) and len(svals_array) >= np_level:
                    oc_row.append(svals_array[np_level - 1])
                elif isinstance(svals_array, list) and svals_array:
                    oc_row.append(svals_array[-1])
                else:
                    oc_row.append({})
            oc_matrix.append(oc_row)
        # Output as a key-value pair for the effect
        effect = {
            'funcType': func.get('funcType'),
            'funcLabel': effect_label,
            'funcTargetType': func.get('funcTargetType'),
            'functvals': func.get('functvals', []),
            'effectsByOC': {effect_label: oc_matrix},
            'buffs': []
        }
        for buff in func.get('buffs', []):
            buff_svals = buff.get('svals', [])
            if isinstance(buff_svals, list) and buff_svals:
                max_buff_svals = buff_svals[-1]
            else:
                max_buff_svals = buff_svals if isinstance(buff_svals, dict) else {}
            parsed_buff = {
                'name': buff.get('name', ''),
                'type': buff.get('type', ''),
                'svals': max_buff_svals
            }
            effect['buffs'].append(parsed_buff)
        effects.append(effect)
    return effects

# NOTE: To support alternate/replacement skills for forms/states (e.g., Mashu Paladin 2),
# the main structuring logic should check for form/state and include the correct skill version.
# For Mashu, ensure Paladin 2 includes the correct skill 2 (Timeworn Bullet Kindling of Amethyst B).
import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

def detect_ascension_structure(servant_data: Dict[str, Any]) -> str:
    """
    Detect the structure type of servant data.
    
    Returns:
        'explicit_ascensions': Has 'ascensions' or 'forms' array with ascension field
        'list_of_lists': Skills/NPs are nested lists per ascension
        'legacy_single': Single list format (ascension-independent)
        'mixed': Combination of formats
    """
    # Always use comprehensive structure
    return 'explicit_ascensions'

def extract_ascension_ranges(servant_data: Dict[str, Any]) -> Dict[str, List[int]]:
    """
    Extract which ascensions use which skills/NPs/traits.
    
    Returns:
        Dict mapping skill/np/trait IDs to list of ascensions that use them
    """
    ranges = {
        'skills': {},
        'noblePhantasms': {},
        'traits': {}
    }
    
    structure = detect_ascension_structure(servant_data)
    
    if structure == 'explicit_ascensions':
        ascensions_data = servant_data.get('ascensions', servant_data.get('forms', []))
        
        for asc_data in ascensions_data:
            ascension = asc_data.get('ascension', asc_data.get('ascensionIndex', asc_data.get('index', 0)))
            
            # Map skills to this ascension
            for skill in asc_data.get('skills', []):
                skill_id = skill.get('id', skill.get('num'))
                if skill_id not in ranges['skills']:
                    ranges['skills'][skill_id] = []
                ranges['skills'][skill_id].append(ascension)
            
            # Map NPs to this ascension
            for np in asc_data.get('noblePhantasms', []):
                np_id = np.get('id', np.get('new_id'))
                if np_id not in ranges['noblePhantasms']:
                    ranges['noblePhantasms'][np_id] = []
                ranges['noblePhantasms'][np_id].append(ascension)
    
    elif structure == 'list_of_lists':
        skills = servant_data.get('skills', [])
        nps = servant_data.get('noblePhantasms', [])
        
        # For list-of-lists, each index represents an ascension
        for asc_idx, skill_set in enumerate(skills):
            ascension = asc_idx + 1  # Convert 0-based to 1-based
            if isinstance(skill_set, list):
                for skill in skill_set:
                    skill_id = skill.get('id', skill.get('num'))
                    if skill_id not in ranges['skills']:
                        ranges['skills'][skill_id] = []
                    ranges['skills'][skill_id].append(ascension)
        
        for asc_idx, np_set in enumerate(nps):
            ascension = asc_idx + 1
            if isinstance(np_set, list):
                for np in np_set:
                    np_id = np.get('id', np.get('new_id'))
                    if np_id not in ranges['noblePhantasms']:
                        ranges['noblePhantasms'][np_id] = []
                    ranges['noblePhantasms'][np_id].append(ascension)
    
    else:  # legacy_single
        # For legacy format, all skills/NPs apply to all ascensions
        max_ascensions = detect_max_ascensions(servant_data)
        all_ascensions = list(range(1, max_ascensions + 1))
        
        for skill in servant_data.get('skills', []):
            skill_id = skill.get('id', skill.get('num'))
            ranges['skills'][skill_id] = all_ascensions.copy()
        
        for np in servant_data.get('noblePhantasms', []):
            np_id = np.get('id', np.get('new_id'))
            ranges['noblePhantasms'][np_id] = all_ascensions.copy()
    
    return ranges

def detect_max_ascensions(servant_data: Dict[str, Any]) -> int:
    """Detect maximum number of ascensions for this servant."""
    # Check explicit ascensions
    ascensions_data = servant_data.get('ascensions', servant_data.get('forms', []))
    if ascensions_data:
        max_asc = max(
            asc.get('ascension', asc.get('ascensionIndex', asc.get('index', 0)))
            for asc in ascensions_data
        )
        return max(max_asc, 4)  # Default to at least 4
    
    # Check list-of-lists structure
    skills = servant_data.get('skills', [])
    nps = servant_data.get('noblePhantasms', [])
    
    max_from_skills = len(skills) if skills and isinstance(skills[0], list) else 4
    max_from_nps = len(nps) if nps and isinstance(nps[0], list) else 4
    
    return max(max_from_skills, max_from_nps, 4)

def parse_traits_by_ascension(servant_data: Dict[str, Any]) -> Dict[int, List[str]]:
    """Parse traits for each ascension."""
    traits_by_ascension = {}
    max_ascensions = detect_max_ascensions(servant_data)
    
    # Get base traits that apply to all ascensions
    base_traits = servant_data.get('traits', [])
    
    # Parse ascension-specific traits
    for asc in range(max_ascensions + 1):  # Include ascension 0
        ascension_traits = base_traits.copy()
        
        # Add ascension-specific traits
        asc_key = f'Ascension {asc} Additional Traits'
        if asc_key in servant_data:
            ascension_traits.extend(servant_data[asc_key])
        
        traits_by_ascension[asc] = ascension_traits
    
    return traits_by_ascension

def normalize_skill_data(skill: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize skill data to consistent format."""
    # Ensure 'id' and 'num' are both present
    if 'id' not in skill and 'num' in skill:
        skill['id'] = skill['num']
    elif 'num' not in skill and 'id' in skill:
        skill['num'] = skill['id']
    
    # Default values
    skill.setdefault('type', 'active')
    skill.setdefault('id', '')
    skill.setdefault('name', '')
    skill.setdefault('desc', '')
    skill.setdefault('maxLevel', 10)
    skill.setdefault('cooldown', 0)
    skill.setdefault('cost', 0)
    skill.setdefault('target', 'self')
    skill.setdefault('effects', [])
    
    # Normalize effects
    normalized_effects = []
    for effect in skill['effects']:
        if isinstance(effect, dict):
            # Ensure all effects have a 'type' and 'value'
            effect.setdefault('type', 'unknown')
            effect.setdefault('value', 0)
            normalized_effects.append(effect)
        else:
            # For backward compatibility, convert old format to new
            normalized_effects.append({
                'type': 'unknown',
                'value': effect
            })
    
    skill['effects'] = normalized_effects
    
    return skill

def parse_np_effects(np_data: Dict[str, Any]) -> List[Dict]:
    """
    Parse NP functions to extract effects with OC/NP level scaling as self-describing key-value pairs.
    """
    effects = []
    for func in np_data.get('functions', []):
        oc_matrix = []
        effect_label = func.get('funcLabel') or func.get('funcType') or 'effect'
        for oc in range(1, 6):
            svals_key = f'svals{oc}' if oc > 1 else 'svals'
            svals_array = func.get(svals_key, func.get('svals', []))
            oc_row = []
            for np_level in range(1, 6):
                if isinstance(svals_array, list) and len(svals_array) >= np_level:
                    oc_row.append(svals_array[np_level - 1])
                elif isinstance(svals_array, list) and svals_array:
                    oc_row.append(svals_array[-1])
                else:
                    oc_row.append({})
            oc_matrix.append(oc_row)
        # Output as a key-value pair for the effect
        effect = {
            'funcType': func.get('funcType'),
            'funcLabel': effect_label,
            'funcTargetType': func.get('funcTargetType'),
            'functvals': func.get('functvals', []),
            'effectsByOC': {effect_label: oc_matrix},
            'buffs': []
        }
        for buff in func.get('buffs', []):
            buff_svals = buff.get('svals', [])
            if isinstance(buff_svals, list) and buff_svals:
                max_buff_svals = buff_svals[-1]
            else:
                max_buff_svals = buff_svals if isinstance(buff_svals, dict) else {}
            parsed_buff = {
                'name': buff.get('name', ''),
                'type': buff.get('type', ''),
                'svals': max_buff_svals
            }
            effect['buffs'].append(parsed_buff)
        effects.append(effect)
    return effects

# NOTE: To support alternate/replacement skills for forms/states (e.g., Mashu Paladin 2),
# the main structuring logic should check for form/state and include the correct skill version.
# For Mashu, ensure Paladin 2 includes the correct skill 2 (Timeworn Bullet Kindling of Amethyst B).
