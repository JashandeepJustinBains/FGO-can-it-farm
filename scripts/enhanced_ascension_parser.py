"""
Enhanced Comprehensive FGO Servant Ascension Parser with Advanced Heuristics
============================================================================

This enhanced version implements comprehensive heuristics to handle all edge cases:
1. Simple cases (no swaps, trait-only changes)
2. Skill/NP/Trait swaps at specific ascensions
3. Transformation mechanics (skill-triggered, form changes)
4. Unlockable content (second NPs, conditional skills)
5. Multiple forms/variants/costumes
6. Partial inheritance vs complete replacement

Based on the comprehensive brainstorm and analysis of FGO servant mechanics.
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from collections import defaultdict


# Known edge case servants and their specific mechanics
EDGE_CASE_SERVANTS = {
    413: {
        "type": "transformation",
        "base_form": 413,
        "transformed_form": 4132,
        "trigger": "skill_use",
        "trigger_skill": 3,  # Third skill triggers transformation
        "description": "Aoko → Super Aoko transformation"
    },
    421: {
        "type": "unlockable_np",
        "unlock_trigger": "skill_use", 
        "trigger_skill": 3,  # Third skill unlocks second NP
        "description": "Unlockable second NP via skill"
    },
    444: {
        "type": "complete_replacement",
        "swap_ascension": 3,
        "description": "U-Olga Marie complete skill set replacement"
    },
    312: {
        "type": "skill_inheritance", 
        "transformation_skills": [3],  # Third skill transforms
        "description": "Mélusine Ray Horizon transformation"
    },
    448: {
        "type": "multi_swap",
        "skill_swap_asc": 3,
        "np_swap_asc": 3,
        "trait_changes": True,
        "description": "Morgan multiple changes at ascension 3"
    },
    394: {
        "type": "np_swap",
        "swap_ascension": 3,
        "description": "NP changes at ascension 3"
    },
    385: {
        "type": "np_swap",
        "swap_ascension": 3,
        "description": "NP changes at ascension 3"  
    },
    391: {
        "type": "np_swap",
        "swap_ascension": 3,
        "description": "NP changes at ascension 3"
    },
    # Trait-only change servants
    418: {"type": "trait_only", "description": "Only traits change"},
    417: {"type": "trait_only", "description": "Only traits change"}, 
    416: {"type": "trait_only", "description": "Only traits change"}
}


class AdvancedAscensionHeuristics:
    """Advanced heuristics engine for handling complex FGO servant mechanics."""
    
    def __init__(self, servant_data: Dict[str, Any]):
        self.servant_data = servant_data
        self.collection_no = servant_data.get('collectionNo')
        self.edge_case_info = EDGE_CASE_SERVANTS.get(self.collection_no, {})
        self.servant_type = self.edge_case_info.get('type', 'simple')
        
    def detect_servant_type(self) -> str:
        """Automatically detect servant type based on data patterns."""
        if self.collection_no in EDGE_CASE_SERVANTS:
            return self.servant_type
            
        # Auto-detection logic
        skills = self.servant_data.get('skills', [])
        nps = self.servant_data.get('noblePhantasms', [])
        transforms = self.servant_data.get('transforms', [])
        ascension_add = self.servant_data.get('ascensionAdd', {})
        
        # Check for transformations
        if transforms:
            return 'transformation'
            
        # Check for multiple priorities (swap indicators)
        skill_priorities = set(skill.get('priority', 1) for skill in skills)
        np_priorities = set(np.get('priority', 1) for np in nps)
        
        if len(skill_priorities) > 1 and len(np_priorities) > 1:
            return 'multi_swap'
        elif len(skill_priorities) > 1:
            return 'skill_swap'  
        elif len(np_priorities) > 1:
            return 'np_swap'
        elif ascension_add:
            return 'trait_only'
        else:
            return 'simple'
    
    def get_swap_ascension(self, content_type: str = 'skills') -> int:
        """Determine the ascension where swaps occur."""
        # Use edge case info if available
        if content_type == 'skills' and 'skill_swap_asc' in self.edge_case_info:
            return self.edge_case_info['skill_swap_asc']
        elif content_type == 'nps' and 'np_swap_asc' in self.edge_case_info:
            return self.edge_case_info['np_swap_asc']
        elif 'swap_ascension' in self.edge_case_info:
            return self.edge_case_info['swap_ascension']
            
        # Default FGO convention: most swaps happen at ascension 3
        return 3
        
    def should_inherit_vs_replace(self, ascension: int, slot: int, content_type: str) -> str:
        """Determine if content should be inherited or completely replaced."""
        if self.servant_type == 'complete_replacement':
            return 'replace'
        elif self.servant_type == 'skill_inheritance':
            return 'inherit'  
        elif self.servant_type in ['skill_swap', 'np_swap', 'multi_swap']:
            swap_asc = self.get_swap_ascension(content_type)
            return 'replace' if ascension >= swap_asc else 'inherit'
        else:
            return 'inherit'
    
    def has_transformation_at_ascension(self, ascension: int) -> bool:
        """Check if servant has transformation mechanics at this ascension."""
        if self.servant_type == 'transformation':
            return ascension >= 1  # Transformation available from ascension 1
        return False
        
    def has_unlockable_content(self, ascension: int) -> Dict[str, Any]:
        """Check for unlockable skills/NPs at this ascension."""
        unlocks = {}
        
        if self.servant_type == 'unlockable_np':
            unlocks['np'] = {
                'trigger': self.edge_case_info.get('unlock_trigger', 'skill_use'),
                'trigger_skill': self.edge_case_info.get('trigger_skill', 3),
                'available_from_asc': ascension
            }
            
        return unlocks
    
    def get_priority_logic(self, ascension: int, content_type: str = 'skills') -> str:
        """Get priority selection logic for this ascension."""
        if self.servant_type == 'complete_replacement':
            swap_asc = self.get_swap_ascension(content_type)
            return 'priority_1' if ascension < swap_asc else 'highest'
        elif self.servant_type in ['skill_swap', 'np_swap', 'multi_swap']:
            swap_asc = self.get_swap_ascension(content_type)
            return 'priority_1' if ascension < swap_asc else 'highest'
        else:
            # Default logic: ascensions 1-2 prefer priority 1, 3+ prefer highest
            return 'priority_1' if ascension <= 2 else 'highest'


def get_skills_for_slot_enhanced(servant_data: Dict[str, Any], slot: int, heuristics: AdvancedAscensionHeuristics) -> List[Dict[str, Any]]:
    """Enhanced skill slot detection with heuristics."""
    skills = servant_data.get('skills', [])
    candidates = []
    
    for skill in skills:
        skill_slot = skill.get('num', 1)
        if skill_slot == slot:
            # Add heuristic metadata
            skill_copy = skill.copy()
            skill_copy['heuristic_type'] = heuristics.servant_type
            candidates.append(skill_copy)
    
    return candidates


def get_nps_for_slot_enhanced(servant_data: Dict[str, Any], slot: int, heuristics: AdvancedAscensionHeuristics) -> List[Dict[str, Any]]:
    """Enhanced NP slot detection with heuristics."""
    nps = servant_data.get('noblePhantasms', [])
    candidates = []
    
    for np in nps:
        np_slot = np.get('slot', 1)  # Default to slot 1
        if np_slot == slot:
            # Add heuristic metadata
            np_copy = np.copy()
            np_copy['heuristic_type'] = heuristics.servant_type
            candidates.append(np_copy)
    
    return candidates


def select_content_for_ascension_enhanced(candidates: List[Dict[str, Any]], ascension: int, 
                                        slot: int, content_type: str, 
                                        heuristics: AdvancedAscensionHeuristics) -> Optional[Dict[str, Any]]:
    """Enhanced content selection with advanced heuristics."""
    if not candidates:
        return None
    
    # Filter valid candidates for this ascension
    valid_candidates = []
    for candidate in candidates:
        if content_type == 'skills':
            if is_skill_valid_for_ascension_enhanced(candidate, ascension, heuristics):
                valid_candidates.append(candidate)
        else:  # NPs
            if is_np_valid_for_ascension_enhanced(candidate, ascension, heuristics):
                valid_candidates.append(candidate)
    
    if not valid_candidates:
        return candidates[0] if candidates else None
    
    # Get priority logic from heuristics
    priority_logic = heuristics.get_priority_logic(ascension, content_type)
    
    # Sort by priority
    valid_candidates.sort(key=lambda x: x.get('priority', 1), reverse=True)
    
    # Debug output
    if len(valid_candidates) > 1:
        priorities = [c.get('priority', 1) for c in valid_candidates]
        print(f"    {content_type} slot {slot} asc {ascension}: priorities {priorities}, logic: {priority_logic}")
    
    if priority_logic == 'priority_1':
        # Prefer priority 1
        priority_1_candidates = [c for c in valid_candidates if c.get('priority', 1) == 1]
        return priority_1_candidates[0] if priority_1_candidates else valid_candidates[0]
    else:
        # Use highest priority
        return valid_candidates[0]


def is_skill_valid_for_ascension_enhanced(skill: Dict[str, Any], ascension: int, 
                                        heuristics: AdvancedAscensionHeuristics) -> bool:
    """Enhanced skill validation with heuristics."""
    # Basic validation
    cond_type = skill.get('condType', '')
    cond_value = skill.get('condValue', 0)
    cond_num = skill.get('condNum', 0)
    
    if not cond_type and not cond_value and not cond_num:
        return True
    
    # Standard condition checks
    if cond_type == 'limitCountAbove':
        return ascension > cond_value
    elif cond_type == 'limitCountBelow':
        return ascension < cond_value
    elif cond_type == 'limitCount':
        return ascension == cond_value
    
    # Heuristic-based validation
    if heuristics.servant_type == 'transformation':
        # For transformation servants, all skills are potentially available
        return True
    elif heuristics.servant_type == 'complete_replacement':
        # For complete replacement, both skill sets are valid at their respective ascensions
        return True
    
    return True


def is_np_valid_for_ascension_enhanced(np: Dict[str, Any], ascension: int,
                                     heuristics: AdvancedAscensionHeuristics) -> bool:
    """Enhanced NP validation with heuristics."""
    # Use same basic logic as skills for now
    return is_skill_valid_for_ascension_enhanced(np, ascension, heuristics)


def apply_transformation_mechanics(skills: List[Dict[str, Any]], nps: List[Dict[str, Any]], 
                                 ascension: int, heuristics: AdvancedAscensionHeuristics) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Apply transformation mechanics based on servant type."""
    if heuristics.servant_type == 'transformation':
        # For transformation servants, add transformation metadata
        if heuristics.collection_no == 413:  # Aoko
            # Add transformation capability to third skill
            for skill in skills:
                if skill.get('num') == 3:
                    skill['transformation'] = {
                        'target_form': 4132,
                        'trigger': 'skill_use',
                        'description': 'Transform into Super Aoko'
                    }
                    
    elif heuristics.servant_type == 'skill_inheritance' and heuristics.collection_no == 312:
        # Mélusine Ray Horizon transformation
        for i, skill in enumerate(skills):
            if skill.get('num') == 3:
                skill_id = skill.get('id')
                if skill_id == 888550 and ascension >= 3:
                    # Transform Ray Horizon A at ascension 3+
                    skills[i] = skill.copy()
                    skills[i]['id'] = 888575
                    skills[i]['transformed'] = True
                    skills[i]['original_id'] = 888550
                    print(f"  Applied Mélusine transformation: {skill_id} → 888575")
    
    return skills, nps


def apply_unlockable_content(skills: List[Dict[str, Any]], nps: List[Dict[str, Any]], 
                           ascension: int, heuristics: AdvancedAscensionHeuristics) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Apply unlockable content mechanics."""
    unlocks = heuristics.has_unlockable_content(ascension)
    
    if 'np' in unlocks:
        unlock_info = unlocks['np']
        # Mark secondary NPs as unlockable
        for i, np in enumerate(nps):
            if i > 0:  # Secondary NP
                np['unlockable'] = True
                np['unlock_trigger'] = unlock_info['trigger']
                np['trigger_skill'] = unlock_info['trigger_skill']
                np['locked'] = True  # Initially locked
    
    return skills, nps


def merge_traits_enhanced(base_traits: List[Dict[str, Any]], servant_data: Dict[str, Any], 
                        ascension: int, heuristics: AdvancedAscensionHeuristics) -> List[Dict[str, Any]]:
    """Enhanced trait merging with heuristics."""
    merged_traits = base_traits.copy()
    
    # Standard ascension trait merging
    ascension_add = servant_data.get('ascensionAdd', {})
    individuality = ascension_add.get('individuality', {})
    ascension_traits = individuality.get('ascension', {})
    
    # Get traits for this ascension
    ascension_key = str(ascension - 1)  # Convert to 0-based
    if ascension_key in ascension_traits:
        additional_traits = ascension_traits[ascension_key]
        if isinstance(additional_traits, list):
            for trait in additional_traits:
                if isinstance(trait, dict):
                    merged_traits.append(trait)
    
    # Apply heuristic-specific trait changes
    if heuristics.servant_type == 'transformation':
        # Add transformation-related traits
        if ascension >= 1:
            merged_traits.append({
                'id': 9999901,
                'name': 'Transformation Capable'
            })
    
    # Remove duplicates
    seen_ids = set()
    unique_traits = []
    for trait in merged_traits:
        trait_id = trait.get('id')
        if trait_id not in seen_ids:
            seen_ids.add(trait_id)
            unique_traits.append(trait)
    
    return unique_traits


def parse_servant_ascensions_enhanced(servant_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """
    Enhanced main parser with comprehensive heuristics.
    
    Handles all edge cases:
    - Simple (no changes)
    - Trait-only changes
    - Skill/NP swaps
    - Transformations
    - Unlockable content
    - Multiple combinations
    """
    collection_no = servant_data.get('collectionNo')
    
    # Skip collectionNo 1
    if collection_no == 1:
        return None
    
    # Initialize heuristics engine
    heuristics = AdvancedAscensionHeuristics(servant_data)
    actual_type = heuristics.detect_servant_type()
    
    print(f"Processing servant {collection_no}: detected type '{actual_type}'")
    
    # Detect max ascensions
    max_ascensions = detect_max_ascensions_enhanced(servant_data)
    base_traits = get_base_traits_enhanced(servant_data)
    
    # Get skill and NP slots
    all_skills = servant_data.get('skills', [])
    all_nps = servant_data.get('noblePhantasms', [])
    
    skill_slots = sorted(set(skill.get('num', 1) for skill in all_skills))
    np_slots = [1]  # Most servants have 1 NP, expandable for multi-NP servants
    
    output = {}
    
    # Process each ascension
    for asc in range(1, max_ascensions + 1):
        skills = []
        nps = []
        traits = base_traits.copy()
        
        # Process skill slots
        for slot in skill_slots:
            candidates = get_skills_for_slot_enhanced(servant_data, slot, heuristics)
            best_skill = select_content_for_ascension_enhanced(
                candidates, asc, slot, 'skills', heuristics
            )
            if best_skill:
                # Clean up metadata
                if 'heuristic_type' in best_skill:
                    del best_skill['heuristic_type']
                skills.append(best_skill)
        
        # Process NP slots  
        for slot in np_slots:
            candidates = get_nps_for_slot_enhanced(servant_data, slot, heuristics)
            best_np = select_content_for_ascension_enhanced(
                candidates, asc, slot, 'nps', heuristics
            )
            if best_np:
                # Clean up metadata
                if 'heuristic_type' in best_np:
                    del best_np['heuristic_type']
                nps.append(best_np)
        
        # Handle unlockable secondary NPs
        if heuristics.servant_type == 'unlockable_np':
            # Add all NPs, mark secondary ones as unlockable
            all_nps_for_asc = servant_data.get('noblePhantasms', [])
            for i, np in enumerate(all_nps_for_asc):
                if i == 0:
                    continue  # Primary NP already handled
                np_copy = np.copy()
                np_copy['unlockable'] = True
                np_copy['locked'] = True
                nps.append(np_copy)
        
        # Apply transformation mechanics
        skills, nps = apply_transformation_mechanics(skills, nps, asc, heuristics)
        
        # Apply unlockable content
        skills, nps = apply_unlockable_content(skills, nps, asc, heuristics)
        
        # Handle traits
        traits = merge_traits_enhanced(traits, servant_data, asc, heuristics)
        
        # Get alignment
        alignment = get_alignment_for_ascension_enhanced(servant_data, asc)
        
        # Build output
        output[asc] = {
            "skills": skills,
            "noblePhantasms": nps,
            "passives": servant_data.get('passives', servant_data.get('classPassive', [])),
            "traits": traits,
            "alignment": alignment,
            "transforms": servant_data.get('transforms', []),
            "heuristics": {
                "type": actual_type,
                "unlocks": heuristics.has_unlockable_content(asc)
            }
        }
    
    return output


def detect_max_ascensions_enhanced(servant_data: Dict[str, Any]) -> int:
    """Enhanced max ascension detection."""
    # Check limits
    limits = servant_data.get('limits', [])
    if limits:
        max_from_limits = max(limit.get('limitCount', 0) for limit in limits)
        return max(max_from_limits, 4)
    
    # Check ascensionAdd
    ascension_add = servant_data.get('ascensionAdd', {})
    individuality = ascension_add.get('individuality', {})
    ascension_traits = individuality.get('ascension', {})
    
    if ascension_traits:
        max_asc_key = max(int(k) for k in ascension_traits.keys() if k.isdigit())
        return max(max_asc_key + 1, 4)  # Convert from 0-based to 1-based
    
    return 4


def get_base_traits_enhanced(servant_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Enhanced base trait extraction."""
    traits = servant_data.get('traits', [])
    base_traits = []
    
    for trait in traits:
        if isinstance(trait, dict):
            base_traits.append(trait)
        elif isinstance(trait, str):
            base_traits.append({"id": 0, "name": trait})
    
    return base_traits


def get_alignment_for_ascension_enhanced(servant_data: Dict[str, Any], ascension: int) -> Dict[str, str]:
    """Enhanced alignment detection."""
    limits = servant_data.get('limits', [])
    alignment = {'policy': 'unknown', 'personality': 'unknown'}
    
    if limits:
        # Try ascension-specific alignment
        for limit in limits:
            limit_count = limit.get('limitCount', 0)
            if limit_count == ascension:
                alignment['policy'] = limit.get('policy', 'unknown')
                alignment['personality'] = limit.get('personality', 'unknown')
                break
        
        # Fallback to base
        if alignment['policy'] == 'unknown' and limits:
            base_limit = limits[0]
            alignment['policy'] = base_limit.get('policy', 'unknown')  
            alignment['personality'] = base_limit.get('personality', 'unknown')
    
    return alignment


def test_enhanced_parser():
    """Test the enhanced parser with edge case servants."""
    test_servants = [444, 312, 413, 421, 448, 394, 418]
    
    for servant_id in test_servants:
        json_file = Path(f'example_servant_data/{servant_id}.json')
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                servant_data = json.load(f)
            
            print(f"\n=== Testing Enhanced Parser for Servant {servant_id} ===")
            result = parse_servant_ascensions_enhanced(servant_data)
            
            if result:
                for asc, data in result.items():
                    print(f"Ascension {asc}:")
                    skill_details = []
                    for s in data['skills']:
                        skill_details.append(f"{s.get('name', 'Unknown')} (ID: {s.get('id')})")
                    print(f"  Skills: {skill_details}")
                    
                    np_details = []
                    for np in data['noblePhantasms']:
                        np_details.append(f"{np.get('name', 'Unknown')} (ID: {np.get('id')})")
                    print(f"  NPs: {np_details}")
                    
                    if data.get('heuristics', {}).get('unlocks'):
                        print(f"  Unlocks: {data['heuristics']['unlocks']}")


if __name__ == "__main__":
    test_enhanced_parser()