from data import class_advantage_matrix, attribute_dict, class_indices, base_multipliers, class_advantage_matrix
from connectDB import db

class Servant:
    special_servants = [312, 394, 391,413, 385, 350, 306, 305]
    # TODO following units have transformations: 312=Melusine, 394=Ptolemy, 391=UDK-Barghest, 413=Aoko
    # TODO following units start with cooldowns unready: 385=Aesc skill 3 starts at 5 cooldown
    # TODO following units have special 'Triggers Each Turn' effects: 305:caren, 306: galatea, 350:tametomo, 413/4132 npgain effect + magic bullets per turn
    # TODO we assume every one has the 2nd and 5th appends unlocked for simplicity
    def __init__(self, collectionNo, np=1, np_gauge=20, CE=None):
        self.data = select_character(collectionNo)
        self.name = self.data.get('name')
        self.class_name = self.data.get('className')
        self.class_id = self.data.get('classId')
        self.gender = self.data.get('gender')
        self.attribute = self.data.get('attribute')
        self.traits = [trait['id'] for trait in self.data.get('traits', [])]
        self.cards = self.data.get('cards', [])
        self.atk_growth = self.data.get('atkGrowth', [])
        self.cooldowns = {0: 0, 1: 0, 2: 0} if collectionNo != 385 else {0:0, 1:0, 2:5}
        self.skills = self.parse_skills(self.data.get('skills', []))
        self.np_level = np
        self.oc_level = 1
        self.nps = self.parse_noble_phantasms(self.data.get('noblePhantasms', []))
        self.passives = self.parse_passive(self.data.get('classPassive', []))
        self.rarity = self.data.get('rarity')
        self.np_gauge = np_gauge
        self.np_gain_mod = 1
        self.buffs = []
        self.atk_mod = 0
        self.b_up = 0
        self.a_up = 0
        self.q_up = 0
        self.power_mod = {}
        self.np_damage_mod = 0
        self.card_type = self.nps[0]['card']
        self.class_base_multiplier = base_multipliers[self.class_name]

    def parse_skills(self, skills_data):
        skills = []
        for skill in skills_data:
            parsed_skill = {
                'id': skill.get('id'),
                'name': skill.get('name'),
                'cooldown': skill.get('coolDown')[9]-1, #TODO HERE IS WHERE APPEND 5 IS ASSUMED
                'functions': []
            }
            for function in skill.get('functions', []):
                parsed_function = {
                    'funcType': function.get('funcType'),
                    'funcTargetType': function.get('funcTargetType'),
                    'functvals': function.get('functvals'),
                    'fieldReq': function.get('funcquestTvals', []),
                    'condTarget': function.get('functvals',[]),
                    'svals': function.get('svals')[9],
                    'buffs': []
                }
                for buff in function.get('buffs', []):
                    parsed_buff = {
                        'name': buff.get('name'),
                        'tvals': buff.get('tvals', []),  # Ensure tvals are included
                        'svals': buff.get('svals')[9] if len(buff.get('svals', [])) > 9 else None,
                        'value': buff.get('svals')[9]['Value'] if len(buff.get('svals', [])) > 9 else 0  # Extract value from svals
                    }
                    parsed_function['buffs'].append(parsed_buff)
                parsed_skill['functions'].append(parsed_function)
            skills.append(parsed_skill)
        return skills


    def get_skills(self):
        return self.skills
    def get_skill_by_num(self, num):
        return self.skills[num]

    def decrement_cooldowns(self, effect):
        for skill in self.cooldowns:
            if self.cooldowns[skill] > 0:
                self.cooldowns[skill] = max(self.cooldowns[skill] - effect['svals']['Value'], 0)

            # logger1.debug(f"Decremented cooldown for skill {skill} by {num}. New cooldown: {self.cooldowns[skill]}")
    
    def skill_available(self, num):
        available = self.cooldowns[num] == 0
        # Log skill availability check
        # logger1.debug(f"Skill {num} availability checked: {'available' if available else 'not available'}")
        return available

    def set_skill_cooldown(self, num):
        self.cooldowns[num] = self.get_skill_by_num(num)['cooldown']
        # Log setting skill cooldown
        # logger1.info(f"Set cooldown for skill {num} to {self.cooldowns[num]}")
    
    def process_end_turn_skills(self):
        for buff in self.buffs:
            if buff['buff'] == 'NP Gain Each Turn':
                self.set_npgauge(buff['value']) 

    def process_buffs(self):
        # Reset modifiers
        self.atk_mod = 0
        self.b_up = 0
        self.a_up = 0
        self.q_up = 0
        self.power_mod = {}
        self.np_damage_mod = 0
        self.oc_level = 1
        self.np_gain_mod = 1

        # Process each buff
        for buff in self.buffs:
            # Check if the buff has a conditional field state
            required_field = buff.get('script', {}).get('INDIVIDUALITIE', {}).get('id')
            if required_field is None:
                required_field = buff.get('originalScript', {}).get('INDIVIDUALITIE')

            # Apply the buff only if the required field state is present
            if required_field is None or (required_field in self.fields):
                # Update modifiers based on the buff type
                if buff['buff'] == 'ATK Up':
                    self.atk_mod += buff['value'] / 1000
                elif buff['buff'] == 'Buster Up':
                    self.b_up += buff['value'] / 1000
                elif buff['buff'] == 'Arts Up':
                    self.a_up += buff['value'] / 1000
                elif buff['buff'] == 'Quick Up':
                    self.q_up += buff['value'] / 1000
                elif buff['buff'] == 'Power Up':
                    self.power_mod += buff['value'] / 1000
                elif buff['buff'] == 'NP Strength Up' or buff['buff'] == 'upNpdamage':
                    self.np_damage_mod += buff['value'] / 1000
                elif buff['buff'] == 'NP Overcharge Level Up':
                    self.oc_level += buff['value']
                elif "STR Up" in buff["buff"] or "Strength Up" in buff["buff"]:
                    for tval in buff['tvals']:
                        if tval not in self.power_mod:
                            self.power_mod[tval] = 0
                        self.power_mod[tval] += buff.get("value", 0)
                elif 'Triggers Each Turn' in buff['buff']:
                    self.np_gauge += buff['value'] 
                elif buff['buff'] == 'NP Gain Up':
                    self.np_gain_mod += buff['value'] / 1000

                # Log the application of the buff
                # logger1.info(f"Applied buff: {buff['buff']} with value: {buff['value']}")

    def parse_noble_phantasms(self, nps_data):
        nps = []
        for np in nps_data:
            parsed_np = {
                'id': np.get('id'),
                'name': np.get('name'),
                'card': np.get('card'),
                'npgain': np.get('npGain'),
                'npdist': np.get('npDistribution'),
                'aoe': np.get('effectFlags')[0],
                'functions': self.parse_np_functions(np.get('functions'))
            }
            nps.append(parsed_np)
            # Log the parsing of noble phantasms
            # logger1.debug(f"Parsed Noble Phantasm: {parsed_np['name']}")
        return nps

    def parse_np_functions(self, functions_data):
        np_values_list = []
        for func in functions_data:
            func_dict = {
                'funcId': func['funcId'],
                'funcType': func['funcType'],
                'funcTargetType': func['funcTargetType'],
                'fieldReq': func.get('funcquestTvals', {}),
                'condTarget': func.get('functvals', {}),
                'values': {
                    1: {i+1: func['svals'][i] for i in range(5)},
                    2: {i+1: func['svals2'][i] for i in range(5)},
                    3: {i+1: func['svals3'][i] for i in range(5)},
                    4: {i+1: func['svals4'][i] for i in range(5)},
                    5: {i+1: func['svals5'][i] for i in range(5)}
                },
                'buffs': self.parse_np_buffs(func.get('buffs', []), func.get('svals', {}))
            }
            np_values_list.append(func_dict)
            # Log the parsing of NP functions
            # logger1.debug(f"Parsed NP function: {func_dict['funcId']}")
        return np_values_list

    def parse_np_buffs(self, buffs_data, svals_data):
        buffs_list = []
        for buff in buffs_data:
            buff_dict = {
                'type': buff['type'],
                'tvals': buff['tvals'],
                'functvals': buff.get('functvals', None),
                'values': buff['vals'],
                'svals': svals_data  # Include svals data
            }
            buffs_list.append(buff_dict)
            # Log the parsing of buffs
            # logger1.debug(f"Parsed buff: {buff_dict['type']}")
        return buffs_list    



    def get_np_values(self, np_level=1, overcharge_level=1):
        result = []
        for np in self.nps:
            for func in np['functions']:
                func_values = func['values'].get(overcharge_level, {}).get(np_level, {})
                buffs = [
                    {
                        'type': buff['type'],
                        'tvals': buff['tvals'],
                        'svals': buff['values']
                    }
                    for buff in func['buffs']
                ]
                result.append({
                    'funcId': func['funcId'],
                    'funcType': func['funcType'],
                    'funcTargetType': func['funcTargetType'],
                    'fieldReq': func.get('fieldReq', {}),
                    'condTarget': func.get('condTarget', {}),
                    'svals': func_values,
                    'buffs': buffs
                })
                # Log the retrieval of NP values
                # logger1.debug(f"Retrieved NP values for function: {func['funcId']}")
        return result

    def get_np_damage_values(self, oc=1, np_level=1):
        funcs = self.get_np_values(np_level, oc)
        for func in funcs:
            if func['funcType'] == 'damageNp':
                np_damage = func['svals'].get('Value', 0)
                # Log the NP damage calculation
                # logger1.info(f"Calculated NP damage: {np_damage / 1000} ")
                return np_damage / 1000, None, None
            if func['funcType'] == 'damageNpIndividual':
                np_damage = func['svals'].get('Value', 0)
                np_correction_target = func['svals'].get('Target', 0)
                np_correction = func['svals'].get('Correction', 0)
                # Log the NP individual damage calculation
                # logger1.info(f"Calculated NP SE damage: {np_damage / 1000}, np_correction_init={np_correction/1000} on units with trait={np_correction_target} ")
                return np_damage / 1000, np_correction_target, np_correction / 1000
            if func['funcType'] == 'damageNpIndividualSum':
                np_damage = func['svals'].get('Value', 0)
                np_damage_correction_init = func['svals'].get('Value2', 0)
                np_correction = func['svals'].get('Correction', 0)
                np_correction_target = func['svals'].get('Target', 0)
                np_correction_id = func['svals'].get('TargetList', 0)
                # Log the NP individual sum damage calculation
                # logger1.info(f"Calculated NP individual sum damage: {np_damage / 1000}, np_correction_init={np_damage_correction_init/1000}, np_correction increase={np_correction/1000} on units={'enemy' if np_correction_target==0 else 'self'} with trait/buff ID of={np_correction_id} ")
                return np_damage / 1000, np_damage_correction_init/1000, np_correction/1000, np_correction_id, np_correction_target
        return None

    def parse_passive(self, passives_data):
        passives = []
        for passive in passives_data:
            parsed_passive = {
                'id': passive.get('id'),
                'name': passive.get('name'),
                'functions': self.parse_passive_functions(passive.get('functions', []))
            }
            passives.append(parsed_passive)
            # Log the parsing of passives
            # logger1.debug(f"Parsed passive: {parsed_passive['name']}")
        return passives
    def parse_passive_functions(self, functions_data):
        functions = []
        for func in functions_data:
            parsed_function = {
                'funcType': func.get('funcType'),
                'funcTargetType': func.get('funcTargetType'),
                'functvals': func.get('functvals', []),
                'svals': func.get('svals', [{}])[0],
                'buffs': func.get('buffs', [])
            }
            functions.append(parsed_function)
        return functions

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
        atk = self.atk_growth[level-1] if level <= 120 else None
        # Log the attack value at the given level
        # logger1.debug(f"Retrieved ATK value at level {level}: {atk}")
        return atk

    def get_name(self):
        name = self.name
        # Log the retrieval of the servant's name
        # logger1.debug(f"Retrieved servant name: {name}")
        return name

    def get_atk_mod(self):
        atk_mod = self.atk_mod
        # Log the retrieval of the attack modifier
        # logger1.debug(f"Retrieved ATK modifier: {atk_mod}")
        return atk_mod

    def get_b_up(self):
        b_up = self.b_up
        # Log the retrieval of the Buster modifier
        # logger1.debug(f"Retrieved Buster modifier: {b_up}")
        return b_up

    def get_a_up(self):
        a_up = self.a_up
        # Log the retrieval of the Arts modifier
        # logger1.debug(f"Retrieved Arts modifier: {a_up}")
        # logger1.debug(f"Arts modifier retrieved: {a_up}")
        return a_up

    def get_q_up(self):
        q_up = self.q_up
        # Log the retrieval of the Quick modifier
        # logger1.debug(f"Retrieved Quick modifier: {q_up}")
        return q_up

    def get_power_mod(self, target=None):
        if target:
            powermod = 0
            for key in self.power_mod:
                if key in target.traits:
                    powermod += self.power_mod[key]
            powermod /= 1000
            # Log the retrieval of the power modifier
            # logger1.debug(f"Retrieved power modifier for target {target.get_name()}: {powermod}")
            return powermod
        else: return self.power_mod

    def get_np_damage_mod(self):
        np_damage_mod = self.np_damage_mod
        # Log the retrieval of the NP damage modifier
        # logger1.debug(f"Retrieved NP damage modifier: {np_damage_mod}")
        return np_damage_mod

    def get_np_level(self):
        np_level = self.np_level
        # Log the retrieval of the NP level
        # logger1.debug(f"Retrieved NP level: {np_level}")
        return np_level

    def get_oc_level(self):
        oc_level = self.oc_level
        # Log the retrieval of the Overcharge level
        # logger1.debug(f"Retrieved Overcharge level: {oc_level}")
        return oc_level

    def set_oc_level(self, oc):
        self.oc_level = oc
        # Log the setting of the Overcharge level
        # logger1.info(f"Set Overcharge level to: {oc}")

    def get_npgain(self):
        np_gain = self.nps[0]['npgain'][self.card_type][0] / 100
        # Log the retrieval of the NP gain
        # logger1.debug(f"Retrieved NP gain: {np_gain}")
        return np_gain

    def get_np_gain_mod(self):
        return self.np_gain_mod

    def get_npdist(self):
        np_dist = self.nps[0]['npdist']
        # Log the retrieval of the NP distribution
        # logger1.debug(f"Retrieved NP distribution: {np_dist}")
        return np_dist

    def get_cardtype(self):
        card_type = self.nps[0]['card']
        # Log the retrieval of the card type
        # logger1.debug(f"Retrieved card type: {card_type}")
        return card_type

    def get_npgauge(self):
        np_gauge = self.np_gauge
        # Log the retrieval of the NP gauge
        # logger1.debug(f"Retrieved NP gauge: {np_gauge}")
        return np_gauge

    def set_npgauge(self, val=0):
        if val == 0:
            print(f"Setting NP gauge of {self.get_name()} to {val}%")
            self.np_gauge = 0
        else:
            print(f"Increasing NP gauge of {self.get_name()} to {self.np_gauge + val}%")
            self.np_gauge += val
        # Log the setting of the NP gauge
        # logger1.info(f"Set NP gauge to: {self.np_gauge}")

    def get_current_buffs(self):
        return [{'atk':self.get_atk_mod()},
                {'buster+': self.get_b_up()},
                {'arts+':self.get_a_up()},
                {'quick+':self.get_q_up()},
                {'power mods':self.get_power_mod()},
                {'np gain':self.np_gain_mod},
                {'np damage': self.get_np_damage_mod()}
                ]

    def add_buff(self, buff: dict):
        self.buffs.append(buff)
        # self.process_buffs()
        # Log the addition of a buff
        # logger1.info(f"Added buff: {buff}")

    def decrement_buffs(self):
        # Create a copy of the list to iterate over
        for buff in self.buffs[:]:
            if buff['turns'] > 0:
                buff['turns'] -= 1
            if buff['turns'] == 0:
                self.buffs.remove(buff)
                # Log the removal of a buff
                # logger1.info(f"Removed buff: {buff}")

    def __repr__(self):
        return f"Servant(name={self.name}, class_id={self.class_name}, attribute={self.attribute}, \n {self.buffs})"


    def get_class_multiplier(self, defender_class):   
        return class_advantage_matrix[class_indices[self.class_name]][class_indices[defender_class]]
    def get_class_base_multiplier(self):
        return self.class_base_multiplier
    def get_attribute_modifier(self, defender):
        return attribute_dict.get(self.attribute).get(defender.attribute)
    
    def contains_trait(self, trait_id):
        return trait_id[0]['id'] in self.traits

    def clear_buff(self, str):
        res = [i['buff'] for i in self.buffs if i != str] 
        self.buffs = res

def select_character(character_id):
    servant = db.servants.find_one({'collectionNo': character_id})
    return servant # Ensure character_id is an integer

