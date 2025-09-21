from data import base_multipliers
from .stats import Stats
from .skills import Skills
from .buffs import Buffs
from .np import NP
from connectDB import db

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
            asc_index = asc_data.get('ascension', asc_data.get('ascensionIndex', 0))
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
                highest_asc = max(ascensions_data, key=lambda x: x.get('ascension', x.get('ascensionIndex', 0)))
                highest_level = highest_asc.get('ascension', highest_asc.get('ascensionIndex', 0))
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
    special_servants = [312, 394, 391, 413, 385, 350, 306, 305]

    def __init__(self, collectionNo, np=5, np_gauge=20, CE=None, ascension=1): # TODO np is at test value of 5 for now
        self.id = collectionNo
        self.data = select_character(collectionNo)
        self.name = self.data.get('name')
        self.class_name = self.data.get('className')
        self.class_id = self.data.get('classId')
        self.gender = self.data.get('gender')
        self.attribute = self.data.get('attribute')
        self.traits = [trait['id'] for trait in self.data.get('traits', [])]
        self.cards = self.data.get('cards', [])
        self.atk_growth = self.data.get('atkGrowth', [])
        
        # Example integration for ascension data selection:
        # ascension_data = select_ascension_data(self.data, ascension)
        # self.skills = Skills(ascension_data.get('skills', self.data.get('skills', [])), append_5=append_5)
        # self.nps = NP(ascension_data.get('noblePhantasms', self.data.get('noblePhantasms', [])))
        # For now, using original logic:
        self.skills = Skills(self.data.get('skills', []))
        self.nps = NP(self.data.get('noblePhantasms', []))
        
        self.np_level = np
        self.oc_level = 1
        self.rarity = self.data.get('rarity')
        self.np_gauge = np_gauge
        self.ascension = ascension
        self.np_gain_mod = 1
        self.buffs = Buffs(self)
        self.stats = Stats(self)
        self.atk_mod = 0
        self.b_up = 0
        self.a_up = 0
        self.q_up = 0
        self.power_mod = {}
        self.np_damage_mod = 0
        self.card_type = self.nps.nps[0]['card'] #if self.nps.nps else None
        self.class_base_multiplier = 1 if self.id == 426 else base_multipliers[self.class_name]

        self.passives = self.buffs.parse_passive(self.data.get('classPassive', []))
        self.apply_passive_buffs()
        self.kill = False

    def __repr__(self):
        return f"Servant(name={self.name}, class_id={self.class_name}, attribute={self.attribute}, \n {self.buffs})"

    def set_npgauge(self, value):
        logging.info(f"INCREASING NP GAUGE OF {self.name} TO {self.np_gauge + value}")
        self.np_gauge += value
    def get_npgauge(self):
        return self.np_gauge

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

def select_character(character_id):
    servant = db.servants.find_one({'collectionNo': character_id})
    return servant  # Ensure character_id is an integer
