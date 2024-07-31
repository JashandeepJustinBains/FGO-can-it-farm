from data import class_advantage_matrix, attribute, class_indices, base_multipliers, traits_dict, character_list
from Servant import Servant
from Enemy import Enemy
from connectDB import db
import pandas as pd
import os
import sys
import random
import json

def get_np_damage_values(np_level, effect):
    # Map NP level to the corresponding svals key
    np_level_to_svals_key = {
        1: effect.get('svals'),
        2: effect.get('svals2'),
        3: effect.get('svals3'),
        4: effect.get('svals4'),
        5: effect.get('svals5')
    }
    return np_level_to_svals_key.get(np_level)

def apply_trait_boost(attacker, target, trait_id, multiplier):
    trait_name = traits_dict.get(trait_id)
    if trait_name and trait_name in target['traits']:
        attacker['trait_multiplier'] = multiplier

class GameState:
    def __init__(self):
        self.enemies = [] # list to hold enemy objects
        self.servants = []  # List to hold servant objects
        self.turn_count = 0  # Track the number of turns
        self.field_state = None  # Track the field state

    def apply_buff(self, target, buff, value, turns):
        # Apply a buff to a target for a certain number of turns
        target['buffs'].append({'buff': buff, 'value': value, 'turns': turns})

    def process_buffs(self, target):
    # Process active buffs and apply their effects
        for buff in target['buffs']:
            if buff['buff'] == 'ATKUp':
                target['attack_multiplier'] = 1 + buff['value'] / 100
            elif buff['buff'] == 'QuickUp':
                target['quick_multiplier'] = 1 + buff['value'] / 100
            elif buff['buff'] == 'ArtsUp':
                target['arts_multiplier'] = 1 + buff['value'] / 100
            elif buff['buff'] == 'BusterUp':
                target['buster_multiplier'] = 1 + buff['value'] / 100
            elif buff['buff'] == 'NPStrengthUp':
                target['np_multiplier'] = 1 + buff['value'] / 100
            elif buff['buff'] == 'DEFDown':
                target['defense_multiplier'] = 1 - buff['value'] / 100
            elif buff['buff'] == 'QuickResistDown':
                target['quick_resist_multiplier'] = 1 - buff['value'] / 100
            elif buff['buff'] == 'ArtsResistDown':
                target['arts_resist_multiplier'] = 1 - buff['value'] / 100
            elif buff['buff'] == 'BusterResistDown':
                target['buster_resist_multiplier'] = 1 - buff['value'] / 100
            elif buff['buff'] == 'TraitDamageUp':
                target['trait_damage_multiplier'] = 1 + buff['value'] / 100
            # Add more buff processing as needed

    def decrement_buffs(self):
        # Decrement the timer for each buff and remove buffs with 0 time left
        for target in self.enemies + self.servants:
            target['buffs'] = [buff for buff in target['buffs'] if buff['turns'] > 1]
            for buff in target['buffs']:
                buff['turns'] -= 1

    def apply_trait_boost(self, attacker, target, trait_id, multiplier):
        trait_name = traits_dict.get(trait_id)
        if trait_name and trait_name in target['traits']:
            self.apply_buff(attacker, 'TraitDamageUp', multiplier * 100 - 100, 1)  # Apply as a buff with 1 turn duration

    def attack(self, attacker, target):
        # Calculate damage based on attacker's attack and target's defense
        self.process_buffs(attacker)
        self.process_buffs(target)
        damage = attacker['attack'] * attacker.get('attack_multiplier', 1)
        damage *= target.get('defense_multiplier', 1)
        damage *= attacker.get('quick_multiplier', 1)
        damage *= attacker.get('arts_multiplier', 1)
        damage *= attacker.get('buster_multiplier', 1)
        damage *= attacker.get('np_multiplier', 1)
        damage *= target.get('quick_resist_multiplier', 1)
        damage *= target.get('arts_resist_multiplier', 1)
        damage *= target.get('buster_resist_multiplier', 1)
        damage *= attacker.get('trait_damage_multiplier', 1)
        target['hp'] -= damage
        print(f"{attacker['name']} attacks {target['name']} for {damage} damage!")

    def apply_effect(self, effect, target):
        # Apply an effect to a target based on the effect type
        effect_type = effect['funcType']
        if effect_type in effect_functions:
            effect_functions[effect_type]

    def use_skill(self, servant, skill):
        # Use a skill and apply its effects
        for effect in skill['functions']:
            target_type = effect['funcTargetType']
            if target_type == 'enemyAll':
                for enemy in self.enemies:
                    self.apply_effect(effect, enemy)
            elif target_type == 'self':
                self.apply_effect(effect, servant)
            elif target_type == 'ptAll':
                for ally in self.servants:
                    self.apply_effect(effect, ally)
            # Add more target types as needed

    def use_np(self, servant, np_level, overcharge_level):
        for effect in servant.nps[0]['functions']:
            target_type = effect['funcTargetType']
            if target_type == 'enemyAll':
                for enemy in self.enemies:
                    self.apply_effect(effect, enemy)
                    if effect['funcType'] == 'damageNpIndividual':
                        np_damage_values = get_np_damage_values(np_level, effect)
                        self.apply_trait_boost(servant, enemy, 301, 1.5)  # Apply 1.5x damage to chaotic alignment enemies
                        self.apply_np_damage(servant, enemy, np_damage_values)
            elif target_type == 'self':
                self.apply_effect(effect, servant)
            elif target_type == 'ptAll':
                for ally in self.servants:
                    self.apply_effect(effect, ally)
            # Add more target types as needed

    def apply_np_damage(self, servant, target, np_damage_values):
        card_damage_value = 1
        if servant.get_cardtype() == 'buster':
            card_damage_value = 1.5
            card_mod = servant.get_b_up()
            enemy_res_mod = target.get_b_resdown()
        elif servant.get_cardtype() == 'quick':
            card_damage_value = 0.8
            card_mod = servant.get_q_up()
            enemy_res_mod = target.get_q_resdown()
        elif servant.get_cardtype() == 'arts':
            card_damage_value = 1
            card_mod = servant.get_a_up()
            enemy_res_mod = target.get_a_resdown()

        np_values = servant.get_np_values(servant.get_np_level, servant.get_oc_level)
        class_modifier = servant.get_class_multiplier(target.get_class())
        attribute_modifier = 1 #self.get_attribute_modifier(servant, target
        atk_mod = servant.get_atk_mod()  
        enemy_def_mod = target.get_def() 
        power_mod = 0 #servant.get_power_mod() 
        self_damage_mod = 0  
        np_damage_mod = servant.get_np_damage_mod()
        is_super_effective = 1 if servant.hasSuperEffective() in target.traits else 0 #  find how to check if "Target" and "Correction" exist in NP then we have NP damage SuperEffective
        super_effective_modifier = 1.5 # TODO this should be changing with nplevel/overcharge on some servants NPs
        # retrieved at run time with OC/NP level super_effective_correction
        # Assuming the first function is the damage function
        np_damage_values = np_values[0]['values'] if np_values else None

        # Check if np_damage_values is None
        if np_damage_values is None:
            print("Error: np_damage_values is None")
            return
        np_damage_multiplier = np_damage_values.get('Value', 0) / 100

        servant_atk = servant.get_atk_at_level()  # Assuming you have a method to get the servant's attack at the current level

        total_damage = (servant_atk * np_damage_multiplier * (card_damage_value * (1 + card_mod - enemy_res_mod)) * 
                        class_modifier * attribute_modifier * 0.23 * (1 + atk_mod - enemy_def_mod) *
                        (1 + power_mod + self_damage_mod + np_damage_mod) *
                        (1 + ((super_effective_modifier - 1) * is_super_effective)))

        np_gain = servant.get_npgain()  # Get the NP gain for the specific card type
        np_distribution = servant.get_npdist()
        print(total_damage)
        print([value for value in np_distribution])
        damage_per_hit = [total_damage * value for value in np_distribution]

        for i, hit in enumerate(np_distribution):
            hit_damage = damage_per_hit[i]
            target.set_hp(hit_damage)
            np_gain_per_hit = np_gain
            servant.np_gauge += np_gain_per_hit
            print(f"{servant.get_name()} hits {target.get_name()} for {hit_damage} damage and gains {np_gain_per_hit} NP!")

        print(f"{servant.get_name()} attacks {target.get_name()} with Noble Phantasm for {total_damage} total damage!")

    def end_turn(self):
        # End the turn and decrement buffs
        self.decrement_buffs()
        self.turn_count += 1



# Define functions for each effect type
def apply_add_state_short(game_state, effect, target):
    # adds a state for x turns
    buff = effect['buffs'][0]['name']
    value = effect['svals']['Value']
    turns = effect['svals']['Turn']
    game_state.apply_buff(target, buff, value, turns)

def apply_gain_np(game_state, effect, target):
    target['np_gauge'] += effect['svals']['Value']

def apply_add_state(game_state, effect, target):
    # adds a state for x turns y uses
    buff = effect['buffs'][0]['name']
    value = effect['svals']['Value']
    turns = effect['svals']['Turn']
    uses = effect['svals']['Count']
    game_state.apply_buff(target, buff, value, turns, uses)

def apply_cooldown_reduction(game_state, effect, target):
    # Reduce the cooldown of all skills of the target ally by 2 turns
    for skill in target['skills']:
        skill['cooldown'] = max(0, skill['cooldown'] - 2)

# Example usage in the use_skill function
def use_skill(self, servant, skill):
    for effect in skill['functions']:
        target_type = effect['funcTargetType']
        if target_type == 'enemyAll':
            for enemy in self.enemies:
                self.apply_effect(effect, enemy)
        elif target_type == 'self':
            self.apply_effect(effect, servant)
        elif target_type == 'ptAll':
            for ally in self.servants:
                self.apply_effect(effect, ally)
        elif target_type == 'ptOne':
            # Assuming you have a way to select a single ally
            target_ally = self.select_ally()
            self.apply_effect(effect, target_ally)
        # Add more target types as needed


# Create a dictionary to map effect types to functions
effect_functions = {
    'addState': apply_add_state,
    'gainNp': apply_gain_np,
    'addStateShort': apply_add_state_short, 
    'shortenSkill': apply_cooldown_reduction, 
    # 'gainStar': apply_gain_star, 
    # 'lossNp': apply_loss_np, 
    # 'gainNpFromTargets': apply_np_absorb, 
    # 'absorbNpturn': apply_np_absorb, 
    # 'transformServant': apply_transform, 
    # 'gainMultiplyNp': apply_multiply_np, 
}
# Instantiate the Servant class with Archetype Earth and Ibuki Douji
servant1 = Servant(collectionNo=351)
servant2 = Servant(collectionNo=355)

# Instantiate the GameState class
game_state = GameState()
game_state.servants.append(servant1)
game_state.servants.append(servant2)

enemy1 = Enemy(['Enemy 1', 100000, 'saber',[301], []])
enemy2 = Enemy(['Enemy 2', 10000, 'alterEgo',[], []])
enemy3 = Enemy(['Enemy 3', 10000, 'avenger',[], []])
game_state.enemies.append(enemy1)
game_state.enemies.append(enemy2)
game_state.enemies.append(enemy3)

# game_state.servants.append(servant2)
# servant1.print_self()
# servant2.print_self()
game_state.use_np(servant1, np_level=1, overcharge_level=1)

