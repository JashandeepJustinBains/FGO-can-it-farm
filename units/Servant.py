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

class Servant:
    special_servants = [312, 394, 391, 413, 385, 350, 306, 305]

    def __init__(self, collectionNo, np=5, np_gauge=20, CE=None): # TODO np is at test value of 5 for now
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
        self.skills = Skills(self.data.get('skills', []))
        self.np_level = np
        self.oc_level = 1
        self.nps = NP(self.data.get('noblePhantasms', []))
        self.rarity = self.data.get('rarity')
        self.np_gauge = np_gauge
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
