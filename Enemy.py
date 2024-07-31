
class Enemy:
    def __init__(self, enemydata):
        self.name = enemydata[0]
        self.hp = enemydata[1]
        self.class_name = enemydata[2]
        self.traits = enemydata[3]
        self.state = enemydata[4]
        self.defense = 0
        self.b_resdown = 0
        self.a_resdown = 0
        self.q_resdown = 0  
    
    def process_buffs(self):
        # Reset modifiers
        self.defense = 0
        self.b_resdown = 0
        self.a_resdown = 0
        self.q_resdown = 0

        # Process buffs and update modifiers
        for buff in self.buffs:
            if buff['buff'] == 'DEF Down':
                self.defense -= buff['value'] / 100
            elif buff['buff'] == 'Buster Card Resist Down':
                self.b_resdown += buff['value'] / 100
            elif buff['buff'] == 'Arts Card Resist Down':
                self.a_resdown += buff['value'] / 100
            elif buff['buff'] == 'Quick Card Resist Down':
                self.q_resdown += buff['value'] / 100
           
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
    def get_state(self):
        return self.state
    
        
