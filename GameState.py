from Servant import Servant
from Quest import Quest
from Enemy import Enemy
import random
import numpy as np

class GameState:
    def __init__(self):
        self.attack_up = 0
        self.x_up = 0
        self.np_damage_up = 0
        self.damage_bonus = 0 # 100 or 200 depending on event

    def calculate_damage(self, base_attack, attribute_multiplier):
        # Calculate total damage based on buffs and attribute multiplier
        damage = {"quick":  0.8*6.00* base_attack * (1 + self.attack_up / 100) * (1 + self.x_up / 100) * (1 + self.np_damage_up + self.damage_bonus)/100,
                  "buster": 1.5*3.00* base_attack * (1 + self.attack_up / 100) * (1 + self.x_up / 100) * (1 + self.np_damage_up + self.damage_bonus)/100,
                  "arts":   1.0*4.50* base_attack * (1 + self.attack_up / 100) * (1 + self.x_up / 100) * (1 + self.np_damage_up + self.damage_bonus)/100}
        return damage * attribute_multiplier