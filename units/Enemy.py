from .buffs import Buffs

class Enemy:
    def __init__(self, enemydata):
        self.name = enemydata[0]
        self.max_hp = enemydata[1]
        self.hp = enemydata[1]
        self.death_rate = enemydata[2]
        self.class_name = enemydata[3]
        self.traits = enemydata[4]
        self.attribute = enemydata[5]
        self.state = enemydata[6]
        self.defense = 0
        self.b_resdown = 0
        self.a_resdown = 0
        self.q_resdown = 0  
        self.buffs = Buffs(servant=None, enemy=self)
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
    def get_max_hp(self):
        return self.max_hp
    def get_hp(self):
        return self.hp
    def set_hp(self, decrement):
        print(f"{self.name} takes {decrement} damage. HP remaining: {self.hp-decrement}")
        self.hp -= decrement
    def get_class(self):
        return self.class_name
    def get_traits(self):
        return self.traits

    def add_buff(self, buff : dict):
        self.buffs.append(buff)
        self.buffs.process_enemy_buffs()
    
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

