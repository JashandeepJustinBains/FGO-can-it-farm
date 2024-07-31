from data import class_advantage_matrix, attribute, class_indices, base_multipliers, traits_dict, character_list
from connectDB import db
import pandas as pd
import random

#TODO implement 1 quest fight with 1 specific team, early era 90+ with simple castoria team, then add in 1 quick team and 1 buster team just to see if proper refund and damage
#   create an algorithm that detemrines possible ways to fill up the bar i.e. servant skills, mystic code skills, swap teammember, clear first wave with arash/sojuro/hebetrot, increase over charge
#   create 3 different standards of character investment (apart from just NP levels) such as [90 10/10/10] [100 10/10/10] [120 10/10/10] [120 10/10/10 Class Score]
#    

# holds data for loading the unit after being retrieved from mongodb
class Servant:
    def __init__(self, collectionNo, np=1):
        self.data = select_character(collectionNo)
        self.name = self.data.get('name')
        self.class_name = self.data.get('className')
        self.class_id = self.data.get('classId')
        self.image_url = self.data.get("extraAssets", {}).get("faces", {}).get("ascension", {}).get("4")
        self.gender = self.data.get('gender')
        self.attribute = self.data.get('attribute')
        self.traits = [trait['id'] for trait in self.data.get('traits', [])]
        self.cards = self.data.get('cards', [])
        self.atk_growth = self.data.get('atkGrowth', [])
        self.cooldowns = []
        self.skills = self.parse_skills(self.data.get('skills', []))
        self.np_level = np
        self.oc_level = 1
        self.nps = self.parse_noble_phantasms(self.data.get('noblePhantasms', []))
        self.passives = self.parse_passive(self.data.get('classPassive', []))
        self.rarity = self.data.get('rarity')
        self.np_gauge = 0
        self.buffs = []
        self.atk_mod = 0
        self.b_up = 0
        self.a_up = 0
        self.q_up = 0
        self.power_mod = 0
        self.np_damage_mod = 0
        self.card_type = self.nps[0]['card']

    def parse_skills(self, skills_data):
        skills = []
        for skill in skills_data:
            parsed_skill = {
                'id': skill.get('id'),
                'name': skill.get('name'),
                'cooldown': skill.get('coolDown'),
                'functions': skill.get('functions')
            }
            skills.append(parsed_skill)
        return skills

    def parse_noble_phantasms(self, nps_data):
        nps = []
        for np in nps_data:
            parsed_np = {
                'id': np.get('id'),
                'name': np.get('name'),
                'card': np.get('card'),
                'npgain': np.get('npGain'),
                'npdist': np.get('npDistribution'),
                'functions': self.parse_np_functions(np.get('functions'))
            }
            nps.append(parsed_np)
        return nps
    def parse_np_functions(self, functions_data):
        np_values_list = []
        for func in functions_data:
            func_dict = {
                'funcId': func['funcId'],
                'funcType': func['funcType'],
                'funcTargetType': func['funcTargetType'],
                'values': {
                    1: {i+1: func['svals'][i] for i in range(5)},
                    2: {i+1: func['svals2'][i] for i in range(5)},
                    3: {i+1: func['svals3'][i] for i in range(5)},
                    4: {i+1: func['svals4'][i] for i in range(5)},
                    5: {i+1: func['svals5'][i] for i in range(5)}
                },
                'buffs': []
            }
            for buff in func.get('buffs', []):
                buff_dict = {
                    'type': buff['type'],
                    'tvals': buff['tvals'],
                    'values': {
                        1: {i+1: func['svals'][i] for i in range(5)},
                        2: {i+1: func['svals2'][i] for i in range(5)},
                        3: {i+1: func['svals3'][i] for i in range(5)},
                        4: {i+1: func['svals4'][i] for i in range(5)},
                        5: {i+1: func['svals5'][i] for i in range(5)}
                    }
                }
                func_dict['buffs'].append(buff_dict)
            np_values_list.append(func_dict)
        return np_values_list
    def get_np_values(self, np_level, overcharge_level):
        result = []
        for np in self.nps:
            for func in np['functions']:
                func_values = func['values'].get(overcharge_level, {}).get(np_level, {})
                buffs = []
                for buff in func['buffs']:
                    buff_values = buff['values'].get(overcharge_level, {}).get(np_level, {})
                    buffs.append({
                        'type': buff['type'],
                        'tvals': buff['tvals'],
                        'values': buff_values
                    })
                result.append({
                    'funcId': func['funcId'],
                    'funcType': func['funcType'],
                    'funcTargetType': func['funcTargetType'],
                    'values': func_values,
                    'buffs': buffs
                })
        return result
    def hasSuperEffective(self) -> int:
        for np in self.nps:
            for func in np['functions']:
                if func['funcType'] == 'damageNpIndividual':
                    for overcharge_level in range(1, 6):
                        for np_level in range(1, 6):
                            sval = func['values'][overcharge_level][np_level]
                            if 'Target' in sval:
                                return int(sval['Target'])
        return None


    def parse_passive(self, passives_data):
        passives = []
        for passive in passives_data:
            parsed_passive = {
                'id': passive.get('id'),
                'name': passive.get('name'),
                'functions': passive.get('functions')
            }
            passives.append(parsed_passive)
        return passives

    def get_atk_at_level(self, level=0):
        if level == 0:
            if self.rarity == 1:
                level = 55
            if self.rarity == 2:
                level = 60
            if self.rarity == 3:
                level = 65
            if self.rarity == 4:
                level = 80
            if self.rarity == 5:
                level = 90
        return self.atk_growth[level-1] if level <= 120 else None

    def process_buffs(self):
        # Reset modifiers
        self.atk_mod = 0
        self.b_up = 0
        self.a_up = 0
        self.q_up = 0
        self.power_mod = 0
        self.np_damage_mod = 0

        # Process buffs and update modifiers
        for buff in self.buffs:
            if buff['buff'] == 'ATKUp':
                self.atk_mod += buff['value'] / 100
            elif buff['buff'] == 'BusterUp':
                self.b_up += buff['value'] / 100
            elif buff['buff'] == 'ArtsUp':
                self.a_up += buff['value'] / 100
            elif buff['buff'] == 'QuickUp':
                self.q_up += buff['value'] / 100
            elif buff['buff'] == 'PowerUp':
                self.power_mod += buff['value'] / 100
            elif buff['buff'] == 'SelfDamageUp':
                self.self_damage_mod += buff['value'] / 100
            elif buff['buff'] == 'NPStrengthUp':
                self.np_damage_mod += buff['value'] / 100
            # Add more buff processing as needed

    def get_name(self):
        return self.name
    def get_atk_mod(self):
        return self.atk_mod
    def get_b_up(self):
        return self.b_up
    def get_a_up(self):
        return self.a_up
    def get_q_up(self):
        return self.q_up
    def get_power_mod(self):
        return self.power_mod
    def get_np_damage_mod(self):
        return self.np_damage_mod
    def get_np_level(self):
        return self.np_level
    def get_oc_level(self):        
        return self.oc_level 
    def set_oc_level(self, oc):
        self.oc_level = oc
    def get_npgain(self):
        return self.nps[0]['npgain'][self.nps[0]['card']][0] / 100
    def get_npdist(self):
        return self.nps[0]['npdist']
    def get_cardtype(self):
        return self.nps[0]['card']

    def __repr__(self):
        return f"Servant(name={self.name}, class_id={self.class_id}, attribute={self.attribute})"

    def print_self(self):
        print('\n')
        print(f"Servant: (ID:{self.id}){self.name}, NP level: {self.np_level} ATK: {self.get_atk_at_level()}")
        self.print_skills()
        self.print_passives()
        self.print_nps()
    
    def print_skills(self):
        # Print skill information
        for skill in self.skills:
            print(f"Skill: {skill['name']}")
            for func in skill['functions']:
                print(func)
              
    def print_passives(self):
        # Print class passive information
        for passive in self.passives:
            print(f"Class Passive: {passive['name']}")
            for func in passive['functions']:
                print(func)

    def print_nps(self):
        # Print noble phantasm information
        for np in self.nps:
            print(f"Noble Phantasm: {np['name']}")
            # print(f"  Card: {np['card']}")
            for func in np['functions']:
                print(func)
    
    def get_class_multiplier(self, defender_class):       
        defender_index = class_indices[defender_class]
        return class_advantage_matrix[class_indices[self.class_name]][defender_index]

    def get_class_base_multiplier(self):
        return self.class_base_multiplier

def select_character(character_id):
    servant = db.servants.find_one({'collectionNo': character_id})
    return servant # Ensure character_id is an integer


def display_character_stats(characters):
    data = []
    for c in characters:
        atk = (
            c.get_atk_at_level(60) if c.rarity == 1 else
            c.get_atk_at_level(65) if c.rarity == 2 else
            c.get_atk_at_level(70) if c.rarity == 3 else
            c.get_atk_at_level(80) if c.rarity == 4 else
            c.get_atk_at_level(90) if c.rarity == 5 else
            None  # Default value if none of the conditions are met
        )

        skills_summary = ", ".join([f"{skill['name']} (Cooldown: {skill['cooldown']})" for skill in c.skills])
        class_passive_summary = ", ".join([passive['name'] for passive in c.class_passive])
        data.append({
            'Name': c.name,
            'Gender': c.gender,
            'Attribute': c.attribute,
            'Cards': ", ".join(c.cards),
            'ATK': atk,
            'Skills': skills_summary,
            'Class Passive': class_passive_summary
        })
    
    df = pd.DataFrame(data)
    
    # Set display options to show all columns and rows
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_colwidth', None)
    
    print(df)
