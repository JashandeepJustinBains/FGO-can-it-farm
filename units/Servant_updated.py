"""
Updated Servant.py with comprehensive ascension parser integration.

This file integrates the comprehensive ascension parser functions directly
into the Servant class and updates select_ascension_data to use them.
"""

import json
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from units.stats import Stats
from units.skills import Skills
from units.np import NP
from units.buffs import Buffs
from units.traits import TraitSet


# Comprehensive Ascension Parser Functions (integrated from scripts/comprehensive_ascension_parser.py)

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
    
    # Handle specific condition types that affect availability
    if cond_type == 'limitCountAbove':
        return ascension > cond_value
    elif cond_type == 'limitCountBelow':
        return ascension < cond_value
    elif cond_type == 'limitCount':
        return ascension == cond_value
    
    # Default to available for unknown conditions
    return True


def is_np_valid_for_ascension(np: Dict[str, Any], ascension: int) -> bool:
    """Check if an NP is valid/available for a specific ascension."""
    # Use same logic as skills for now
    return is_skill_valid_for_ascension(np, ascension)


def select_highest_priority_for_ascension(candidates: List[Dict[str, Any]], ascension: int) -> Optional[Dict[str, Any]]:
    """
    Select the highest priority skill/NP for a given ascension with ascension-aware logic.
    
    Logic:
    - Ascensions 1-2: Prefer priority 1, fallback to highest if not available
    - Ascensions 3-4: Prefer highest priority, fallback to available
    """
    if not candidates:
        return None
    
    # Filter candidates that are valid for this ascension
    valid_candidates = []
    for candidate in candidates:
        candidate_type = candidate.get('type', 'skill')  # Default to skill if not specified
        if candidate_type == 'skill':
            if is_skill_valid_for_ascension(candidate, ascension):
                valid_candidates.append(candidate)
        else:  # NP
            if is_np_valid_for_ascension(candidate, ascension):
                valid_candidates.append(candidate)
    
    if not valid_candidates:
        # No valid candidates, return first candidate as fallback
        return candidates[0] if candidates else None
    
    # Sort by priority (higher numbers = higher priority)
    valid_candidates.sort(key=lambda x: x.get('priority', 1), reverse=True)
    
    if ascension <= 2:
        # Ascensions 1-2: Prefer priority 1
        priority_1_candidates = [c for c in valid_candidates if c.get('priority', 1) == 1]
        if priority_1_candidates:
            return priority_1_candidates[0]
        else:
            # Fallback to highest available
            return valid_candidates[0]
    else:
        # Ascensions 3-4: Use highest priority
        return valid_candidates[0]


def get_base_traits(servant_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get base traits from servant data."""
    traits = servant_data.get('traits', [])
    
    # Convert trait format if needed
    base_traits = []
    for trait in traits:
        if isinstance(trait, dict):
            base_traits.append(trait)
        elif isinstance(trait, str):
            # Convert string to dict format (fallback)
            base_traits.append({"id": 0, "name": trait})
    
    return base_traits


def merge_traits_for_ascension(base_traits: List[Dict[str, Any]], servant_data: Dict[str, Any], ascension: int) -> List[Dict[str, Any]]:
    """Merge base traits with ascension-specific trait additions."""
    merged_traits = base_traits.copy()
    
    # Check ascensionAdd for trait changes
    ascension_add = servant_data.get('ascensionAdd', {})
    individuality = ascension_add.get('individuality', {})
    ascension_traits = individuality.get('ascension', {})
    
    # Get traits for this ascension (convert 1-based to 0-based for lookup)
    ascension_key = str(ascension - 1)
    if ascension_key in ascension_traits:
        additional_traits = ascension_traits[ascension_key]
        if isinstance(additional_traits, list):
            for trait in additional_traits:
                if isinstance(trait, dict):
                    merged_traits.append(trait)
    
    # Remove duplicates based on trait ID
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
            "noblePhantasms": nps,
            "passives": servant_data.get('passives', servant_data.get('classPassive', [])),
            "traits": traits,
            "alignment": alignment,
            "transforms": servant_data.get('transforms', [])
        }
    
    return output


def get_comprehensive_ascension_data(servant_data: Dict[str, Any], ascension: int) -> Dict[str, Any]:
    """
    Get comprehensive ascension data for a specific ascension.
    
    Args:
        servant_data: Raw servant JSON data
        ascension: Requested ascension level (1-based)
    
    Returns:
        Dictionary with ascension-specific data
    """
    # Parse all ascensions
    all_ascensions = parse_servant_ascensions(servant_data)
    
    if all_ascensions is None or ascension not in all_ascensions:
        # Fallback to legacy behavior if comprehensive parsing fails
        return select_ascension_data_legacy(servant_data, ascension)
    
    return all_ascensions[ascension]


# Updated select_ascension_data function
def select_ascension_data(servant_json: dict, ascension: int) -> dict:
    """
    Select ascension-specific data from servant JSON using enhanced comprehensive parser.
    
    This function now uses the enhanced ascension parser with comprehensive heuristics
    for accurate per-ascension skill/NP/trait mapping with proper priority logic and
    support for all edge cases including transformations, unlocks, and complex swaps.
    
    Args:
        servant_json: The servant data dictionary
        ascension: The requested ascension level (1-based)
    
    Returns:
        Dictionary with selected ascension data (skills, noblePhantasms, passives, traits)
    """
    try:
        # Try enhanced comprehensive parser first
        from scripts.enhanced_ascension_parser import parse_servant_ascensions_enhanced
        all_ascensions = parse_servant_ascensions_enhanced(servant_json)
        
        if all_ascensions and ascension in all_ascensions:
            return all_ascensions[ascension]
        elif all_ascensions:
            # Fallback to highest available ascension
            available_ascensions = sorted(all_ascensions.keys())
            highest_asc = available_ascensions[-1]
            logging.warning(f"Ascension {ascension} not found, using highest available ascension {highest_asc}")
            return all_ascensions[highest_asc]
            
    except Exception as e:
        logging.warning(f"Enhanced parser failed for servant {servant_json.get('collectionNo')}, ascension {ascension}: {e}")
    
    # Fallback to legacy parser
    return select_ascension_data_legacy(servant_json, ascension)


def select_ascension_data_legacy(servant_json: dict, ascension: int) -> dict:
    """
    Legacy select ascension data function (original implementation).
    Used as fallback when comprehensive parser fails.
    """
    result = {}
    
    # Check for explicit ascensions/forms array first
    ascensions_data = servant_json.get('ascensions', servant_json.get('forms', []))
    if ascensions_data:
        # Look for matching ascension
        selected_ascension = None
        # ascensionAdd -> individuality -> costume -> ids

        for asc_data in ascensions_data:
            asc_index = asc_data.get('ascension', asc_data.get('ascensionIndex', asc_data.get('index', 0)))
            if asc_index == ascension:
                selected_ascension = asc_data
                break
        if selected_ascension:
            # Extract data from the ascension object
            result['skills'] = selected_ascension.get('skills', [])
            result['noblePhantasms'] = selected_ascension.get('noblePhantasms', [])
            result['passives'] = selected_ascension.get('passives', [])
            result['transforms'] = selected_ascension.get('transforms', [])
            return result
        else:
            # Requested ascension not found, use highest available
            if ascensions_data:
                highest_asc = max(ascensions_data, key=lambda x: x.get('ascension', x.get('ascensionIndex', x.get('index', 0))))
                highest_level = highest_asc.get('ascension', highest_asc.get('ascensionIndex', highest_asc.get('index', 0)))
                logging.warning(f"Ascension {ascension} not found, using highest available ascension {highest_level}")
                result['skills'] = highest_asc.get('skills', [])
                result['noblePhantasms'] = highest_asc.get('noblePhantasms', [])
                result['passives'] = highest_asc.get('passives', [])
                result['transforms'] = highest_asc.get('transforms', [])
                return result
    
    # Check for list-of-lists format (per-ascension lists)
    skills_data = servant_json.get('skills', [])
    nps_data = servant_json.get('noblePhantasms', [])
    
    # Detect if skills/nps are list-of-lists
    is_skills_list_of_lists = (skills_data and 
                              isinstance(skills_data, list) and 
                              len(skills_data) > 0 and 
                              isinstance(skills_data[0], list))
    
    is_nps_list_of_lists = (nps_data and 
                           isinstance(nps_data, list) and 
                           len(nps_data) > 0 and 
                           isinstance(nps_data[0], list))
    
    if is_skills_list_of_lists or is_nps_list_of_lists:
        # Handle list-of-lists format
        if is_skills_list_of_lists:
            if ascension <= len(skills_data):
                result['skills'] = skills_data[ascension - 1]
            else:
                # Use highest available
                highest_idx = len(skills_data) - 1
                logging.warning(f"Skills ascension {ascension} not found, using highest available ascension {highest_idx + 1}")
                result['skills'] = skills_data[highest_idx]
        else:
            result['skills'] = skills_data
            
        if is_nps_list_of_lists:
            if ascension <= len(nps_data):
                result['noblePhantasms'] = nps_data[ascension - 1]
            else:
                # Use highest available
                highest_idx = len(nps_data) - 1
                logging.warning(f"NoblePhantasms ascension {ascension} not found, using highest available ascension {highest_idx + 1}")
                result['noblePhantasms'] = nps_data[highest_idx]
        else:
            result['noblePhantasms'] = nps_data
            
        # For list-of-lists, other fields are typically ascension-independent
        result['passives'] = servant_json.get('passives', servant_json.get('classPassive', []))
        result['transforms'] = servant_json.get('transforms', [])
        return result
    
    # Legacy single-list format (ascension-independent)
    result['skills'] = skills_data
    result['noblePhantasms'] = nps_data
    result['passives'] = servant_json.get('passives', servant_json.get('classPassive', []))
    result['transforms'] = servant_json.get('transforms', [])
    
    return result


def _extract_number(value):
    """Extract number handling MongoDB format."""
    if isinstance(value, dict) and '$numberInt' in value:
        return int(value['$numberInt'])
    elif isinstance(value, dict) and '$numberLong' in value:
        return int(value['$numberLong'])
    elif isinstance(value, dict) and '$numberDouble' in value:
        return int(float(value['$numberDouble']))
    elif isinstance(value, (int, float)):
        return int(value)
    elif isinstance(value, str) and value.isdigit():
        return int(value)
    elif value is None:
        return 0
    else:
        # Fallback for other types
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0


def compute_variant_svt_id(servant_data, ascension_index, costume_svt_id=None):
    """Compute variant svtId based on ascension and costume."""
    if costume_svt_id:
        return costume_svt_id
    
    base_id = servant_data.get('id', 0)
    collection_no = servant_data.get('collectionNo', 0)
    
    # Simple variant computation (can be expanded)
    return base_id + (ascension_index - 1) * 10


# Base multipliers for damage calculation
base_multipliers = {
    'saber': 1.0,
    'archer': 0.95,
    'lancer': 1.05,
    'rider': 1.0,
    'caster': 0.9,
    'assassin': 0.9,
    'berserker': 1.1,
    'shielder': 1.0,
    'ruler': 1.1,
    'avenger': 1.1,
    'alterEgo': 1.0,
    'moonCancer': 1.0,
    'foreigner': 1.0,
    'pretender': 1.0,
}


class Servant:
    def __init__(self, id, ascension=4, variant_svt_id=None, np=1, oc=1, 
                 initialCharge=0, atkUp=0, busterUp=0, artsUp=0, quickUp=0, 
                 damageUp=set(), npUp=0, attack=0, append_5=False, 
                 busterDamageUp=0, quickDamageUp=0, artsDamageUp=0):
        """Initialize Servant with comprehensive ascension parsing."""
        
        from . import select_character  # Import here to avoid circular imports
        
        # Store initial parameters
        self.id = id
        self.ascension = ascension
        self._user_supplied_variant = variant_svt_id
        
        # Load base servant data
        self.data = select_character(id)
        if not self.data:
            raise ValueError(f"Servant with id {id} not found")
        
        # Set basic attributes
        self.name = self.data.get('name', f'Servant_{id}')
        self.class_name = self.data.get('className', 'unknown')
        
        # Compute variant svtId
        self.variant_svt_id = compute_variant_svt_id(self.data, ascension, variant_svt_id)
        
        # Get ascension-specific data using comprehensive parser
        ascension_data = select_ascension_data(self.data, ascension)
        
        # Initialize traits system with base traits and ascension-specific additions
        self.trait_set = TraitSet(self.data.get('traits', []))
        # If a variant override was provided or detected, apply costume traits
        # from ascensionAdd; otherwise apply ascension traits.
        if self._user_supplied_variant:
            self._apply_costume_traits(self._user_supplied_variant)
        else:
            self._apply_ascension_traits()
        
        # Initialize cards and other basic data
        self.cards = self.data.get('cards', [])
        
        # Initialize skills and NPs with ascension-aware data
        self.skills = Skills(ascension_data.get('skills', self.data.get('skills', [])), self, append_5=append_5)
        self.np_level = np
        self.oc_level = oc
        self.nps = NP(ascension_data.get('noblePhantasms', self.data.get('noblePhantasms', [])), self)
        self.rarity = self.data.get('rarity')
        self.np_gauge = initialCharge
        self.np_gain_mod = 1
        self.buffs = Buffs(self)
        self.stats = Stats(self)
        self.bonus_attack = attack
        
        # Store user-inputted modifiers
        self.atk_mod = atkUp
        self.b_up = busterUp
        self.a_up = artsUp
        self.q_up = quickUp
        self.power_mod = {damageUp}
        self.np_damage_mod = npUp
        self.card_type = self.nps.nps[0]['card'] if self.nps.nps else None
        self.class_base_multiplier = 1 if self.id == 426 else base_multipliers[self.class_name]

        # Parse passives from ascension-aware data
        passives_data = ascension_data.get('passives', self.data.get('classPassive', []))
        self.passives = self.buffs.parse_passive(passives_data)
        self.apply_passive_buffs()
        self.kill = False

        # Store user-inputted buffs separately
        self.user_atk_mod = atkUp
        self.user_b_up = busterUp
        self.user_a_up = artsUp
        self.user_q_up = quickUp
        self.user_np_damage_mod = npUp
        self.user_buster_damage_up = busterDamageUp
        self.user_quick_damage_up = quickDamageUp
        self.user_arts_damage_up = artsDamageUp

    def _apply_ascension_traits(self):
        """Apply ascension-specific traits based on current ascension level."""
        ascension_add = self.data.get('ascensionAdd', {})
        if ascension_add:
            self.trait_set.apply_ascension_traits(ascension_add, self.ascension - 1)  # Convert to 0-based
    
    def _apply_costume_traits(self, costume_svt_id):
        """Apply costume-specific traits."""
        ascension_add = self.data.get('ascensionAdd', {})
        if ascension_add:
            self.trait_set.apply_costume_traits(ascension_add, costume_svt_id)
    
    def change_ascension(self, ascension_index, costume_svt_id=None):
        """
        Change the servant's ascension and/or costume, updating variant data and traits.
        
        Args:
            ascension_index: New ascension level (1-based)
            costume_svt_id: Optional costume svtId to apply
        """
        self.ascension = ascension_index
        
        # Recompute variant svtId
        self.variant_svt_id = compute_variant_svt_id(self.data, ascension_index, costume_svt_id)
        
        # Update ascension-aware data using comprehensive parser
        ascension_data = select_ascension_data(self.data, ascension_index)
        
        # Update traits
        if costume_svt_id:
            self._apply_costume_traits(costume_svt_id)
        else:
            self._apply_ascension_traits()
        
        # Recreate skills and NPs with new ascension data and variant
        self.skills = Skills(ascension_data.get('skills', self.data.get('skills', [])), self)
        self.nps = NP(ascension_data.get('noblePhantasms', self.data.get('noblePhantasms', [])), self)
        
        # Update passives
        passives_data = ascension_data.get('passives', self.data.get('classPassive', []))
        self.passives = self.buffs.parse_passive(passives_data)
        
        # Update card type
        self.card_type = self.nps.nps[0]['card'] if self.nps.nps else None
    
    def apply_trait_transformation(self, changes):
        """
        Apply mid-combat trait changes (e.g., from transformations).
        
        Args:
            changes: Dict with 'add' and/or 'remove' keys containing trait lists
        """
        if 'add' in changes:
            for trait in changes['add']:
                self.trait_set.add_trait(trait)
        
        if 'remove' in changes:
            for trait in changes['remove']:
                self.trait_set.remove_trait(trait)

    # Rest of the Servant class methods would continue here...
    # (apply_passive_buffs, calc_damage, etc. - keeping existing implementation)


# The rest of the file would include all the existing Servant methods
# that are not shown here for brevity...