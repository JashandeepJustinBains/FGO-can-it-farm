from data import base_multipliers
from .stats import Stats
from .skills import Skills
from .buffs import Buffs
from .np import NP

# Mock DB connection for testing
try:
    from scripts.connectDB import db
except ImportError:
    # Create a mock DB for testing
    class MockDB:
        class MockCollection:
            def find_one(self, query):
                return None
        
        @property
        def servants(self):
            return self.MockCollection()
    
    db = MockDB()

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

    def __init__(self, collectionNo, np=1, ascension=1, lvl=0, initialCharge=0, attack=0, atkUp=0, artsUp=0, quickUp=0, busterUp=0, npUp=0, damageUp=0, busterDamageUp=0, quickDamageUp=0, artsDamageUp=0, append_5=False):
        self.id = collectionNo
        self.data = select_character(collectionNo)
        if self.data is None:
            raise ValueError(f"Servant data for collectionNo {collectionNo} not found.")
        self.name = self.data.get('name')
        self.class_name = self.data.get('className')
        self.class_id = self.data.get('classId')
        self.gender = self.data.get('gender')
        self.attribute = self.data.get('attribute')
        self.traits = [trait['id'] for trait in self.data.get('traits', [])]
        self.cards = self.data.get('cards', [])
        self.lvl = lvl # currently working on High Prio TODOs
        self.ascension = ascension; # currently working on High Prio TODOs
        self.atk_growth = self.data.get('atkGrowth', [])
        
        # Use ascension-aware data selection so Servant picks ascension-specific
        # skills and noblePhantasms when present in the JSON. Falls back to
        # legacy fields if ascension-specific data is not available.
        ascension_data = select_ascension_data(self.data, ascension)
        self.skills = Skills(ascension_data.get('skills', self.data.get('skills', [])), append_5=append_5)
        self.np_level = np
        self.oc_level = 1
        self.nps = NP(ascension_data.get('noblePhantasms', self.data.get('noblePhantasms', [])))
        self.rarity = self.data.get('rarity')
        self.np_gauge = initialCharge
        self.np_gain_mod = 1
        self.buffs = Buffs(self)
        self.stats = Stats(self)
        self.bonus_attack = attack
        self.atk_mod = atkUp
        self.b_up = busterUp
        self.a_up = artsUp
        self.q_up = quickUp
        self.power_mod = {damageUp}
        self.np_damage_mod = 0
        # Use the NP helper's default card type (NP.card) which selects the
        # appropriate NP version's card. Previously this used the first NP
        # entry which caused mismatches for upgraded NPs.
        self.card_type = getattr(self.nps, 'card', None)
        self.class_base_multiplier = 1 if self.id == 426 else base_multipliers[self.class_name]

        self.passives = self.buffs.parse_passive(self.data.get('classPassive', []))
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

    def __repr__(self):
        return (
            f"Servant(name={self.name}, class_id={self.class_name}, attribute={self.attribute})\n"
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
        tvals = [tval['id'] for tval in state.get('tvals', [])] if state.get('tvals') else []
        turns = state['turns']
        
        # Preserve metadata for trigger handling
        buff_entry = {
            'buff': buff, 
            'functvals': functvals, 
            'value': value, 
            'tvals': tvals, 
            'turns': turns,
            'svals': state.get('svals', {}),
            'count': state.get('count'),
            'trigger_type': state.get('trigger_type')
        }
        
        self.buffs.add_buff(buff_entry)

    def apply_ce_effects(self, ce_effects):
        for effect in ce_effects:
            state = {
                'buff_name': effect.get('name', 'Unknown'),
                'value': effect.get('value', 0),
                'turns': -1,  # Infinite duration
                'functvals': effect.get('functvals', [])
            }
            self.apply_buff(state)

    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove database connection if present
        if 'data' in state and hasattr(state['data'], 'collection'):  # crude check for pymongo object
            state['data'] = None
        return state

    def get_lvl(self):
        return self.lvl


def select_character(character_id):
    servant = db.servants.find_one({'collectionNo': character_id})
    return servant  # Ensure character_id is an integer
