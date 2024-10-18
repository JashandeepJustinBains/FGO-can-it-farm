class Buffs:
    def __init__(self, servant=None, enemy=None):
        if servant:
            self.servant = servant
            self.buffs = []
        if enemy:
            self.enemy = enemy
            self.buffs = []

    def process_end_turn_skills(self):
        for buff in self.buffs:
            if buff['buff'] == 'NP Gain Each Turn':
                self.servant.set_npgauge(buff['value'])

    def process_enemy_buffs(self):
        # Reset modifiers
        self.enemy.defense = 0
        self.enemy.b_resdown = 0
        self.enemy.a_resdown = 0
        self.enemy.q_resdown = 0
        self.enemy.roman = self.traits.count(2004)
        # Process buffs and update modifiers
        # print(f"{self.name} has the following effects applied: {self.buffs}")
        for buff in self.buffs:
            if buff['buff'] == 'DEF Down':
                self.enemy.defense -= buff['value'] / 1000
            elif buff['buff'] == 'Buster Card Resist Down':
                self.enemy.b_resdown -= buff['value'] / 1000
            elif buff['buff'] == 'Arts Card Resist Down':
                self.enemy.a_resdown -= buff['value'] / 1000
            elif buff['buff'] == 'Quick Card Resist Down':
                self.enemy.q_resdown -= buff['value'] / 1000
            elif buff['buff'] == 'Apply Trait (Rome)':
                self.enemy.traits.append(2004)
            # Add more buff processing as needed
        # print(buff)


    def process_servant_buffs(self):
        # Reset modifiers
        self.servant.atk_mod = 0
        self.servant.b_up = 0
        self.servant.a_up = 0
        self.servant.q_up = 0
        self.servant.power_mod = {}
        self.servant.np_damage_mod = 0
        self.servant.oc_level = 1
        self.servant.np_gain_mod = 1

        # Store a flag for Boost NP Strength Up
        boost_np_strength_up_active = False

        # Initial pass to calculate np_damage_mod
        for buff in self.buffs:
            required_field = buff.get('script', {}).get('INDIVIDUALITIE', {}).get('id')
            if required_field is None:
                required_field = buff.get('originalScript', {}).get('INDIVIDUALITIE')
            if required_field is None or (required_field in self.servant.fields):
                if buff['buff'] == 'NP Strength Up' or buff['buff'] == 'upNpdamage':
                    self.servant.np_damage_mod += buff['value'] / 1000
                elif buff['buff'] == 'Boost NP Strength Up':
                    boost_np_strength_up_active = True

        # Apply the Boost NP Strength Up multiplier
        if boost_np_strength_up_active:
            self.servant.np_damage_mod *= 2

        # Second pass for other buffs
        for buff in self.buffs:
            required_field = buff.get('script', {}).get('INDIVIDUALITIE', {}).get('id')
            if required_field is None:
                required_field = buff.get('originalScript', {}).get('INDIVIDUALITIE')
            if required_field is None or (required_field in self.servant.fields):
                if buff['buff'] == 'ATK Up':
                    self.servant.atk_mod += buff['value'] / 1000
                elif buff['buff'] == 'Buster Up':
                    self.servant.b_up += buff['value'] / 1000
                elif buff['buff'] == 'Arts Up':
                    self.servant.a_up += buff['value'] / 1000
                elif buff['buff'] == 'Quick Up':
                    self.servant.q_up += buff['value'] / 1000
                elif buff['buff'] == 'Power Up':
                    self.servant.power_mod += buff['value'] / 1000
                elif buff['buff'] == 'NP Overcharge Level Up':
                    self.servant.oc_level += buff['value']
                elif "STR Up" in buff["buff"] or "Strength Up" in buff["buff"]:
                    for tval in buff['tvals']:
                        if tval not in self.servant.power_mod:
                            self.servant.power_mod[tval] = 0
                        self.servant.power_mod[tval] += buff.get("value", 0)
                elif 'Triggers Each Turn' in buff['buff']:
                    self.servant.np_gauge += buff['value']
                elif buff['buff'] == 'NP Gain Up':
                    self.servant.np_gain_mod += buff['value'] / 1000

    def parse_passive(self, passives_data):
        passives = []
        for passive in passives_data:
            parsed_passive = {
                'id': passive.get('id'),
                'name': passive.get('name'),
                'functions': self.parse_passive_functions(passive.get('functions', []))
            }
            passives.append(parsed_passive)
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

    def add_buff(self, buff: dict):
        self.buffs.append(buff)

    def decrement_buffs(self):
        for buff in self.buffs[:]:
            if buff['turns'] > 0:
                buff['turns'] -= 1
            if buff['turns'] == 0:
                self.buffs.remove(buff)

    def clear_buff(self, str):
        self.buffs = [i for i in self.buffs if i['buff'] != str]

    def __repr__(self):
        buff_name_value = []
        for buff in self.buffs:
            buff_name_value.append(f"{buff['buff']}: {buff['value']/1000 if (buff['value']/1000) != 0 else ''} {buff['functvals'] if buff['functvals'] else ''}")
        return f"{buff_name_value}"

