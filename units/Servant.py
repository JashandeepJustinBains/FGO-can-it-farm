from data import base_multipliers
from .stats import Stats
from .skills import Skills
from .buffs import Buffs
from .np import NP
from .traits import TraitSet, parse_trait_add_data, get_applicable_trait_adds

import logging

# Configure logging
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def select_ascension_data(servant_json: dict, ascension: int) -> dict:
    """
    Select ascension-specific data from servant JSON.
    
    Handles multiple input shapes:
    - Legacy single-list: skills/noblePhantasms as single list (ascension-independent)
    - List-of-lists: outer list with items per-ascension
    - ascensions/forms arrays: objects with ascension field containing skills/noblePhantasms
    - Mixed shapes: prefer explicit ascension entries, fallback to legacy
    
    Args:
        servant_json: The servant data dictionary
        ascension: The requested ascension level (1-based)
    
    Returns:
        Dictionary with selected ascension data (skills, noblePhantasms, passives, transforms)
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
    return int(value) if value is not None else 0


def compute_variant_svt_id(servant_json: dict, ascension: int, costume_svt_id=None) -> int:
    """
    Compute the selected variant svtId for the current ascension/costume.
    
    Algorithm:
    1. If user-supplied costume_svt_id is given, use it
    2. Try to map ascension index → variant using npSvts.imageIndex and skillSvts/releaseConditions
    3. Build mapping of imageIndex → most common svtId (use highest priority if priority field present)
    4. If ascension index maps to an imageIndex found in the data, set variant_svt_id to that svtId
    5. Scan skillSvts entries for releaseConditions with condType == "equipWithTargetCostume"
    6. Fallback: top-level svtId field
    
    Args:
        servant_json: The servant data dictionary
        ascension: The requested ascension level (1-based)
        costume_svt_id: Optional costume svtId override
        
    Returns:
        Selected variant svtId
    """

    # If an explicit costume override was provided, use it immediately.
    if costume_svt_id is not None:
        return _extract_number(costume_svt_id)

    # Heuristic: sometimes the API returns a variant svt id in the 'ascension'
    # field. If ascension looks like a variant id (large integer) or matches a
    # costume key in ascensionAdd, prefer it directly for variant selection.
    try:
        asc_int = int(ascension)
    except Exception:
        asc_int = None

    asc_add = servant_json.get('ascensionAdd', {}) or {}
    costume_keys = set()
    if isinstance(asc_add, dict):
        ind = asc_add.get('individuality', {}) or {}
        attr = asc_add.get('attribute', {}) or {}
        costume_keys.update((ind.get('costume') or {}).keys())
        costume_keys.update((attr.get('costume') or {}).keys())

    if (asc_int is not None and asc_int >= 100000) or (str(ascension) in costume_keys):
        return _extract_number(ascension)
    
    top_level_svt_id = _extract_number(servant_json.get('id', servant_json.get('svtId', 0)))
    
    # Step 2-3: Try npSvts.imageIndex mapping
    np_svts = servant_json.get('npSvts', [])
    if np_svts:
        # Build imageIndex → svtId mapping
        image_index_mapping = {}
        for np_entry in np_svts:
            image_index = _extract_number(np_entry.get('imageIndex', 0))
            svt_id = _extract_number(np_entry.get('svtId', top_level_svt_id))
            priority = _extract_number(np_entry.get('priority', 0))
            
            if image_index not in image_index_mapping:
                image_index_mapping[image_index] = {'svtId': svt_id, 'priority': priority}
            else:
                # Use highest priority, or highest svtId as tie-breaker
                current = image_index_mapping[image_index]
                if priority > current['priority'] or (priority == current['priority'] and svt_id > current['svtId']):
                    image_index_mapping[image_index] = {'svtId': svt_id, 'priority': priority}
        
        # Map ascension to imageIndex (typically 0-based ascension maps to 0-based imageIndex)
        ascension_image_index = ascension - 1  # Convert 1-based to 0-based
        if ascension_image_index in image_index_mapping:
            return image_index_mapping[ascension_image_index]['svtId']
    
    # Step 4: Try spriteModel mapping (some exports include per-ascension sprite model -> variant mapping)
    extra_assets = servant_json.get('extraAssets', {}) or {}
    sprite_models = extra_assets.get('spriteModel', {}) or {}
    asc_sprite_map = sprite_models.get('ascension', {}) or {}
    try:
        # asc_sprite_map may map ascension index -> svtId
        if ascension in asc_sprite_map:
            return _extract_number(asc_sprite_map[ascension])
        # or keys might be strings
        if str(ascension) in asc_sprite_map:
            return _extract_number(asc_sprite_map[str(ascension)])
    except Exception:
        pass

    # Step 5: Try skillSvts releaseConditions
    skill_svts = servant_json.get('skillSvts', [])
    if skill_svts:
        for skill_entry in skill_svts:
            release_conditions = skill_entry.get('releaseConditions', [])
            for condition in release_conditions:
                if condition.get('condType') == 'equipWithTargetCostume':
                    cond_target_id = _extract_number(condition.get('condTargetId', condition.get('condNum', 0)))
                    # condTargetId may be encoded as a costume svt id or a small ascension threshold
                    if cond_target_id:
                        # If cond_target_id looks like a small ascension number (<=10) compare to ascension
                        if cond_target_id <= 10 and (cond_target_id == ascension or cond_target_id == ascension + 10):
                            return _extract_number(skill_entry.get('svtId', top_level_svt_id))
                        # Otherwise treat as a svt id mapping
                        if cond_target_id == top_level_svt_id or cond_target_id == ascension:
                            return _extract_number(skill_entry.get('svtId', top_level_svt_id))
    
    # Step 5: Fallback to top-level svtId
    return top_level_svt_id


def select_character(character_id):
    """
    Load character data from database or mock data.
    
    Args:
        character_id: Collection number of the character
        
    Returns:
        Character data dict or None if not found
    """
    # Try to use a global `db` object if available (test harness may provide one).
    db = globals().get('db', None)
    if db:
        try:
            servant = db.servants.find_one({'collectionNo': character_id})
            if servant:
                return servant
        except Exception:
            # If any DB access error occurs, fall back to file-based loading
            pass

    # File fallback for local tests / environments without a DB.
    # Look for example_servant_data/<collectionNo>.json relative to repo root.
    import json
    import os

    # Compute the path to the example_servant_data directory (repo root is one
    # level up from the units package).
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    example_dir = os.path.join(repo_root, 'example_servant_data')

    try:
        filename = f"{int(character_id)}.json"
    except Exception:
        filename = f"{str(character_id)}.json"

    filepath = os.path.join(example_dir, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except Exception:
            # If reading fails, return None so caller can raise a clear error
            return None

    return None  # Ensure character_id is an integer

class Servant:
    special_servants = [
        #transforms completly new character on np to 4132
        312,
        # transforms np to different type on skill
        394, 391, 413, 448,
        # changes traits on different ascension
        385,
        # changes traits, skills and NP on different ascension
        1, 444,
        # applies special effect per turn that needs a translation to its real effect
        350, 306, 305]

    def __init__(self, collectionNo, np=1, oc=1, ascension=1, lvl=0, initialCharge=0, attack=0, atkUp=0, artsUp=0, quickUp=0, busterUp=0, npUp=0, damageUp=0, busterDamageUp=0, quickDamageUp=0, artsDamageUp=0, append_5=False, variant_svt_id=None):
        self.id = collectionNo
        self.data = select_character(collectionNo)
        if self.data is None:
            raise ValueError(f"Servant data for collectionNo {collectionNo} not found.")
        self.name = self.data.get('name')
        self.class_name = self.data.get('className')
        self.class_id = self.data.get('classId')
        self.gender = self.data.get('gender')
        self.attribute = self.data.get('attribute')
        
        # Store level and ascension
        self.lvl = lvl

        # The API sometimes returns the selected variant svt id in the 'ascension'
        # field. If ascension looks like a variant id (large number), treat it as
        # such and allow an optional explicit variant_svt_id parameter as well.
        incoming_ascension = ascension
        self._user_supplied_variant = None

        if variant_svt_id is not None:
            # explicit override takes precedence
            self._user_supplied_variant = variant_svt_id
            self.ascension = 1
        else:
            # heuristic: treat large ints (>=100000) as svt ids
            try:
                if isinstance(incoming_ascension, int) and incoming_ascension >= 100000:
                    self._user_supplied_variant = incoming_ascension
                    self.ascension = 1
                else:
                    self.ascension = incoming_ascension
            except Exception:
                self.ascension = incoming_ascension
        self.atk_growth = self.data.get('atkGrowth', [])

        # Compute variant svtId for ascension/costume-specific data. Pass along
        # any user-supplied variant id (from variant_svt_id param or detected
        # from the incoming ascension).
        variant_override = self._user_supplied_variant
        self.variant_svt_id = compute_variant_svt_id(self.data, self.ascension, variant_override)

        # Use ascension-aware data selection so Servant picks ascension-specific
        # skills and noblePhantasms when present in the JSON. Falls back to
        # legacy fields if ascension-specific data is not available.
        ascension_data = select_ascension_data(self.data, self.ascension)

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
        
        # Update ascension-aware data
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
        self.trait_set.apply_trait_changes(changes)
    
    def get_traits(self):
        """Get all currently active trait IDs."""
        return self.trait_set.get_traits()
    
    def has_trait(self, trait_id):
        """Check if servant currently has a specific trait."""
        return self.trait_set.contains(trait_id)
    
    # Backwards compatibility property
    @property
    def traits(self):
        """Backwards compatibility: return traits as list of IDs."""
        return list(self.trait_set.get_traits())

    def __repr__(self):
        return (
            f"Servant(name={self.name}, class_id={self.class_name}, attribute={self.attribute})\n"
            f"Ascension: {self.ascension}, Variant ID: {self.variant_svt_id}\n"
            f"Traits: {len(self.get_traits())} active\n"
            f"Buffs:\n{self.buffs.grouped_str()}"
        )
    

    def set_npgauge(self, value):
        
        if value == 0:
            logging.info(f"Setting NP GAUGE to 0 for {self.name}")
            self.np_gauge = 0
        else:
            logging.info(f"INCREASING NP GAUGE OF {self.name} TO {self.np_gauge + value}")
            self.np_gauge += value

    def get_npgauge(self):
        return self.np_gauge

    def apply_bonus_buffs(self):
        # Only apply if the value is nonzero
        if self.user_atk_mod:
            self.apply_buff({'buff_name': 'ATK Up', 'value': self.user_atk_mod, 'turns': -1, 'functvals': [], 'tvals': []})
        if self.user_b_up:
            self.apply_buff({'buff_name': 'Buster Up', 'value': self.user_b_up, 'turns': -1, 'functvals': [], 'tvals': []})
        if self.user_a_up:
            self.apply_buff({'buff_name': 'Arts Up', 'value': self.user_a_up, 'turns': -1, 'functvals': [], 'tvals': []})
        if self.user_q_up:
            self.apply_buff({'buff_name': 'Quick Up', 'value': self.user_q_up, 'turns': -1, 'functvals': [], 'tvals': []})
        if self.user_np_damage_mod:
            self.apply_buff({'buff_name': 'NP Strength Up', 'value': self.user_np_damage_mod, 'turns': -1, 'functvals': [], 'tvals': []})
        if self.user_buster_damage_up:
            self.apply_buff({'buff_name': 'Buster Card Damage Up', 'value': self.user_buster_damage_up, 'turns': -1, 'functvals': [], 'tvals': []})
        if self.user_quick_damage_up:
            self.apply_buff({'buff_name': 'Quick Card Damage Up', 'value': self.user_quick_damage_up, 'turns': -1, 'functvals': [], 'tvals': []})
        if self.user_arts_damage_up:
            self.apply_buff({'buff_name': 'Arts Card Damage Up', 'value': self.user_arts_damage_up, 'turns': -1, 'functvals': [], 'tvals': []})
          

    def apply_passive_buffs(self):
        for passive in self.passives:
            for func in passive['functions']:
                for buff in func['buffs']:
                    state = {
                        'buff_name': buff.get('name', 'Unknown'),
                        'value': func['svals'].get('Value', 0),
                        'turns': -1,  # Infinite duration
                        'functvals': func.get('functvals', [])
                    }
                    self.apply_buff(state)

    def apply_buff(self, state):
        buff = state['buff_name']
        value = state['value']
        functvals = state['functvals']
        tvals = [tval['id'] for tval in state.get('tvals', [])]
        turns = state['turns']

        self.buffs.add_buff({'buff': buff, 'functvals': functvals, 'value': value, 'tvals': tvals, 'turns': turns})



    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove database connection if present
        if 'data' in state and hasattr(state['data'], 'collection'):  # crude check for pymongo object
            state['data'] = None
        return state

