
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
            # Add more buff processing as needed
        print(buff)


    def decrement_buffs(self):
        # Create a copy of the list to iterate over
        for buff in self.buffs[:]:
            turns = buff.get('turns', None)
            print(buff)
            if turns is not None:
                if turns > 0:
                    buff['turns'] -= 1
                if buff['turns'] == 0:
                    self.buffs.remove(buff)




