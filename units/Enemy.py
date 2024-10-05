
class Enemy:
    def __init__(self, enemydata):
        self.name = enemydata[0]
        self.hp = enemydata[1]
        self.class_name = enemydata[2]
        self.traits = enemydata[3]
        self.attribute = enemydata[4]
        self.state = enemydata[5]
        self.defense = 0
        self.b_resdown = 0
        self.a_resdown = 0
        self.q_resdown = 0  
        self.buffs = []
        self.np_per_hit_mult = self.np_gain_per_hit()

    def get_def(self):
        return self.defense
    def get_b_resdown(self):
        return self.b_resdown
    def get_a_resdown(self):
        return self.a_resdown
    def get_q_resdown(self):
        return self.q_resdown
    

    def get_name(self):
        return self.name
    def get_hp(self):
        return self.hp
    def set_hp(self, decrement):
        self.hp -= decrement
    def get_class(self):
        return self.class_name
    def get_traits(self):
        return self.traits

    def add_buff(self, buff : dict):
        self.buffs.append(buff)
        self.process_buffs()
    
    def process_buffs(self):
        # Reset modifiers
        self.defense = 0
        self.b_resdown = 0
        self.a_resdown = 0
        self.q_resdown = 0
        self.roman = self.traits.count(2004)
        # Process buffs and update modifiers
        # print(f"{self.name} has the following effects applied: {self.buffs}")
        for buff in self.buffs:
            if buff['buff'] == 'DEF Down':
                self.defense -= buff['value'] / 1000
            elif buff['buff'] == 'Buster Card Resist Down':
                self.b_resdown -= buff['value'] / 1000
            elif buff['buff'] == 'Arts Card Resist Down':
                self.a_resdown -= buff['value'] / 1000
            elif buff['buff'] == 'Quick Card Resist Down':
                self.q_resdown -= buff['value'] / 1000
            elif buff['buff'] == 'Apply Trait (Rome)':
                self.traits.append(2004)
            # Add more buff processing as needed
        # print(buff)

    def np_gain_per_hit(self):
        initial = 1
        if self.class_name == 'rider': 
            initial *= 1.1
        if self.class_name == 'caster': 
            initial *= 1.2
        if self.class_name == 'assassin': 
            initial *= 0.9
        if self.class_name == 'berserker': 
            initial *= 0.8
        if 1002 in self.traits or 1100 in self.traits: # undead/soldier/pirate mult
            initial *= 1.2
        # print(f"INITIAL NP MULT={initial}")
        return initial

    def decrement_buffs(self):
        # Create a copy of the list to iterate over
        for buff in self.buffs[:]:
            turns = buff.get('turns', None)
            if turns is not None:
                if turns > 0:
                    buff['turns'] -= 1
                if buff['turns'] == 0:
                    self.buffs.remove(buff)
        # print(buff)

    def __repr__(self) -> str:
        return f"Servant(name={self.name}, hp={self.hp}, class_id={self.class_name}, attribute={self.attribute}, traits={self.traits} \n {self.buffs})"
