from data import base_multipliers
from .stats import Stats
from .skills import Skills
from .buffs import Buffs
from .np import NP
from scripts.connectDB import db

import logging

# Configure logging
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def select_ascension_data(servant_json: dict, ascension: int) -> dict:
    """
    Select the appropriate ascension-specific data from a servant JSON.
    
    Handles multiple JSON formats:
    - Legacy single-list: skills/noblePhantasms is a single list (ascension-independent)
    - List-of-lists: outer list with per-ascension variants (pick index ascension-1)
    - ascensions/forms arrays: find matching ascension object and extract keys
    - Mixed shapes: prefer explicit ascension-matching entry, fallback to legacy
    
    If requested ascension > available entries, chooses highest available with warning.
    Preserves raw effect IDs and OC/NP matrices exactly.
    
    Args:
        servant_json: Raw servant data dictionary
        ascension: Requested ascension level (1-based)
    
    Returns:
        Dictionary with ascension-appropriate 'skills' and 'noblePhantasms' keys
    """
    result = {}
    
    # Handle skills
    skills_data = servant_json.get('skills', [])
    if isinstance(skills_data, list) and len(skills_data) > 0:
        if isinstance(skills_data[0], list):
            # List-of-lists format
            max_available = len(skills_data)
            if ascension > max_available:
                logging.warning(f"Requested ascension {ascension} > available skills entries {max_available}, using highest")
                chosen_idx = max_available - 1
            else:
                chosen_idx = ascension - 1
            result['skills'] = skills_data[chosen_idx]
        else:
            # Legacy single-list format - ascension independent
            result['skills'] = skills_data
    else:
        result['skills'] = []
    
    # Handle noblePhantasms
    nps_data = servant_json.get('noblePhantasms', [])
    if isinstance(nps_data, list) and len(nps_data) > 0:
        if isinstance(nps_data[0], list):
            # List-of-lists format
            max_available = len(nps_data)
            if ascension > max_available:
                logging.warning(f"Requested ascension {ascension} > available NP entries {max_available}, using highest")
                chosen_idx = max_available - 1
            else:
                chosen_idx = ascension - 1
            result['noblePhantasms'] = nps_data[chosen_idx]
        else:
            # Legacy single-list format - ascension independent
            result['noblePhantasms'] = nps_data
    else:
        result['noblePhantasms'] = []
    
    # Handle ascensions/forms arrays (if present, override above)
    ascensions_data = servant_json.get('ascensions', [])
    forms_data = servant_json.get('forms', [])
    
    if ascensions_data:
        # Find matching ascension entry
        matching_asc = None
        for asc_entry in ascensions_data:
            if asc_entry.get('ascension') == ascension:
                matching_asc = asc_entry
                break
        
        if matching_asc:
            # Override with ascension-specific data if available
            if 'skills' in matching_asc:
                result['skills'] = matching_asc['skills']
            if 'noblePhantasms' in matching_asc:
                result['noblePhantasms'] = matching_asc['noblePhantasms']
        else:
            # No exact match, use highest available
            if ascensions_data:
                highest_asc = max(ascensions_data, key=lambda x: x.get('ascension', 0))
                if highest_asc.get('ascension', 0) < ascension:
                    logging.warning(f"Requested ascension {ascension} not found in ascensions array, using ascension {highest_asc.get('ascension')}")
                if 'skills' in highest_asc:
                    result['skills'] = highest_asc['skills']
                if 'noblePhantasms' in highest_asc:
                    result['noblePhantasms'] = highest_asc['noblePhantasms']
    
    if forms_data:
        # Similar logic for forms
        matching_form = None
        for form_entry in forms_data:
            if form_entry.get('ascension') == ascension:
                matching_form = form_entry
                break
        
        if matching_form:
            if 'skills' in matching_form:
                result['skills'] = matching_form['skills']
            if 'noblePhantasms' in matching_form:
                result['noblePhantasms'] = matching_form['noblePhantasms']
        else:
            # No exact match, use highest available
            if forms_data:
                highest_form = max(forms_data, key=lambda x: x.get('ascension', 0))
                if highest_form.get('ascension', 0) < ascension:
                    logging.warning(f"Requested ascension {ascension} not found in forms array, using ascension {highest_form.get('ascension')}")
                if 'skills' in highest_form:
                    result['skills'] = highest_form['skills']
                if 'noblePhantasms' in highest_form:
                    result['noblePhantasms'] = highest_form['noblePhantasms']
    
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
        
        # Example integration of ascension data selection:
        # For servants with ascension-specific skills/NPs, you can use:
        # ascension_data = select_ascension_data(self.data, ascension)
        # self.skills = Skills(ascension_data.get('skills', []), append_5=append_5)
        # self.nps = NP(ascension_data.get('noblePhantasms', []))
        # Current implementation uses raw data for compatibility:
        self.skills = Skills(self.data.get('skills', []), append_5=append_5)
        self.np_level = np
        self.oc_level = 1
        self.nps = NP(self.data.get('noblePhantasms', []))
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
        self.card_type = self.nps.nps[0]['card'] #if self.nps.nps else None
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
        tvals = [tval['id'] for tval in state.get('tvals', [])]
        turns = state['turns']

        self.buffs.add_buff({'buff': buff, 'functvals': functvals, 'value': value, 'tvals': tvals, 'turns': turns})

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

def select_character(character_id):
    servant = db.servants.find_one({'collectionNo': character_id})
    return servant  # Ensure character_id is an integer
