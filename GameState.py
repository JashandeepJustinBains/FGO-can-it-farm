from Servant import Servant
from Enemy import Enemy
from connectDB import db
import pandas as pd
import os
import sys
import random
import json

class GameState:
    def __init__(self):
        self.enemies = [] # list to hold enemy objects
        self.servants = []  # List to hold servant objects
        self.turn_count = 0  # Track the number of turns
        self.fields = []  # Track the field state


    def end_turn(self):
        # End the turn and decrement buffs
        self.decrement_buffs()
        self.turn_count += 1

    def add_servant(self, servant_id):
        servant = Servant(collectionNo=servant_id)
        self.apply_passive_buffs(servant)
        self.servants.append(servant)
    def apply_passive_buffs(self, servant):
        for passive in servant.passives:
            for func in passive['functions']:
                for buff in func['buffs']:
                    state = {
                        'buff_name': buff.get('name', 'Unknown'),
                        'value': func['svals'].get('Value', 0),
                        'turns': -1,  # Infinite duration
                        'functvals': func.get('functvals', [])
                    }
                    self.apply_buff(servant, state)

    def add_enemies(self, enemy_data):
        enemy = Enemy(enemy_data)
        self.enemies.append(enemy)

    def add_quest(self, quest_data):
        # adds quest fields and initializes all enemies
        return


    def extract_state(self, effect):
        if effect['funcType'] == 'gainNp':
            state = {
                'type': 'gainNp',
                'functvals': effect.get('condTarget', []),
                'value': effect['svals'].get('Value', 0)
            }
        elif effect['funcType'] == 'addFieldChangeToField':
            state = {
                'type': 'fieldChange',
                'field_name': effect['svals']['FieldIndividuality'][0],
                'turns': effect['svals'].get('Turn',0),
            }
        else:
            state = {
                'type': 'buff',
                'buff_name': effect['buffs'][0].get('name', 'Unknown') if effect.get('buffs') else 'Unknown',
                'value': effect['svals'].get('Value', 0),
                'functvals': effect.get('functvals', []),
                'turns': effect['svals'].get('Turn', 0)
            }
        return state



    def add_field(self, state):
        name = state.get('field_name', 'Unknown')
        turns = state.get('turns', 0)
        self.fields.append([name, turns])

    def apply_buff(self, target, state):
        # Apply a buff to a target for a certain number of turns
        buff = state['buff_name']
        value = state['value']
        functvals = state['functvals']
        turns = state['turns']

        target.add_buff({'buff': buff, 'value': value, 'turns': turns})

    def decrement_buffs(self):
        # Decrement the timer for each buff and remove buffs with 0 time left
        for target in self.enemies + self.servants:
            target.decrement_buffs()


    def use_skill(self, servant, skill):
        # Use a skill and apply its effects
        for effect in skill['functions']:
            print(f"Applying {servant.name}'s '{effect['funcType']}' to '{effect['funcTargetType']}'")
            self.apply_effect(effect, servant)


    def use_np(self, servant, np_level, overcharge_level):
        if servant.get_npgauge() >= 100:
            servant.set_npgauge(0)  # Reset NP gauge after use
            functions = servant.get_np_values(np_level, overcharge_level)
            damage_index = None
            maintarget = 0
            for enemy in self.enemies:
                # TODO single target NP's attack the highest hp target
                # TODO yamato takeru's arts down effect only affects this target as well
                maintarget = max(enemy.get_hp(), maintarget)

            # Find the index of the damageNp function
            for i, func in enumerate(functions):
                if func['funcType'] == 'damageNp' or func['funcType'] == 'damageNpIndividual':
                    damage_index = i
                    break

            # Apply effects before damage
            for i in range(damage_index):
                self.apply_effect(functions[i], servant)

            # Apply damage
            for enemy in self.enemies:
                self.apply_np_damage(servant, enemy)

            # Apply effects after damage
            for i in range(damage_index + 1, len(functions)):
                self.apply_effect(functions[i], servant)
        else:
            print(f"{servant.name} does not have enough NP gauge: {servant.get_npgauge()}")


    def apply_np_damage(self, servant, target):
        card_damage_value = None
        card_type = servant.get_cardtype()
        if card_type == 'buster':
            card_damage_value = 1.5
            card_mod = servant.get_b_up()
            enemy_res_mod = target.get_b_resdown()
        elif card_type == 'quick':
            card_damage_value = 0.8
            card_mod = servant.get_q_up()
            enemy_res_mod = target.get_q_resdown()
        elif card_type == 'arts':
            card_damage_value = 1
            card_mod = servant.get_a_up()
            enemy_res_mod = target.get_a_resdown()

        class_modifier = servant.get_class_multiplier(target.get_class())
        attribute_modifier = servant.get_attribute_modifier(target)
        atk_mod = servant.get_atk_mod()
        enemy_def_mod = target.get_def()
        power_mod = servant.get_power_mod()
        self_damage_mod = 0
        np_damage_mod = servant.get_np_damage_mod()
        is_super_effective = 1 if servant.hasSuperEffective() in target.traits else 0
        np_damage_multiplier, super_effective_modifier = servant.get_np_damage_values(2, 2)
        servant_atk = servant.get_atk_at_level()
        # print(f"servant_atk={servant_atk}| |np_damage_multiplier={np_damage_multiplier}|card_damage_value={card_damage_value}|card_mod={card_mod}|enemy_res_mod={enemy_res_mod}|class_modifier={class_modifier}|attribute_modifier={attribute_modifier}|atk_mod={atk_mod}|enemy_def_mod={enemy_def_mod}|power_mod={power_mod}|self_damage_mod={self_damage_mod}|np_damage_mod={np_damage_mod}|super_effective_modifier={super_effective_modifier}|is_super_effective={is_super_effective}")
        
        total_damage = (servant_atk * np_damage_multiplier * (card_damage_value * (1 + card_mod - enemy_res_mod)) *
                        class_modifier * attribute_modifier * 0.23 * (1 + atk_mod - enemy_def_mod) *
                        (1 + power_mod + self_damage_mod + np_damage_mod) *
                        (1 + ((super_effective_modifier - 1) * is_super_effective)))
        np_gain = servant.get_npgain()
        np_distribution = servant.get_npdist()
        damage_per_hit = [total_damage * value for value in np_distribution]

        for i, hit in enumerate(np_distribution):
            hit_damage = damage_per_hit[i]
            target.set_hp(hit_damage)
            np_gain_per_hit = np_gain
            if card_type != 'buster':
                servant.np_gauge += np_gain_per_hit

        print(f"{servant.get_name()} attacks {target.get_name()} with Noble Phantasm for {'%.0f' % total_damage} total damage!")

    # Define functions for each effect type
    def apply_add_state_short(self, effect, target):
        # adds a state for x turns
        state = self.extract_state(effect)
        self.apply_buff(target, state)

    def apply_gain_np(self, effect, target):
        # Extract the buff info
        state = self.extract_state(effect)
        
        # Increase the NP gauge of the target
        np_gain_value = state.get('value', 0)
        target.np_gauge += np_gain_value
        print(f"Increasing NP gauge of {target.get_name()} by {np_gain_value}")

    def apply_transform(self, effect, target):
        # 
        return

    def apply_add_state(self, effect, target):
        # adds a state for x turns y uses
        state = self.extract_state(effect)
        self.apply_buff(target, state)

    def add_field_change(self, effect, target):
        state = self.extract_state(effect)
        self.add_field(state)

    def apply_cooldown_reduction(self, effect, target):
        # Reduce the cooldown of all skills of the target ally by 2 turns
        for skill in target['skills']:
            skill['cooldown'] = max(0, skill['cooldown'] - 2)

    def apply_effect(self, effect, servant):
        effect_type = effect['funcType']
        target_type = effect['funcTargetType']
        condTarget = effect.get('condTarget', [])
        field_req = effect.get('fieldReq', {})


        # Determine the targets based on target type
        if target_type == 'self':
            targets = [servant]
        elif target_type == 'enemyAll':
            targets = self.enemies
        elif target_type == 'ptOther':
            targets = [ally for ally in self.servants if ally != servant]
        elif target_type == 'ptAll':
            targets = self.servants
        else:
            targets = []

        # Apply the effect to each target
        print(f"attempting to use effect: {effect_type} on {target_type} ")

        # Lambda functions for conditional checks
        check_cond_target = lambda target: not condTarget or all(trait['id'] in [t for t in target.traits] for trait in condTarget)
        check_field_req = lambda: not field_req or any(field['id'] in [f[0] for f in self.fields] for field in field_req)

        for target in targets:
        # Check if the target meets the conditional requirements
            if check_cond_target(target) and check_field_req():
                if effect_type in self.effect_functions:
                        self.effect_functions[effect_type](self, effect, target)


    # Create a dictionary to map effect types to functions
    effect_functions = {
        'addState': apply_add_state,
        'gainNp': apply_gain_np,
        'addStateShort': apply_add_state_short, 
        'shortenSkill': apply_cooldown_reduction, 
        'addFieldChangeToField': add_field_change,
        'transformServant': apply_transform, 
        # 'gainStar': apply_gain_star, 
        # 'lossNp': apply_loss_np, 
        # 'gainNpFromTargets': apply_np_absorb, 
        # 'absorbNpturn': apply_np_absorb, 
        # 'gainMultiplyNp': apply_multiply_np, 
    }

# Instantiate the GameState class
game_state = GameState()
# Instantiate the Servant class with Archetype Earth and Ibuki Douji
game_state.add_servant(351)
game_state.add_servant(355)
game_state.add_servant(4132)

enemy1 = ['Enemy 1', 100000, 'saber',[301],'human', []]
enemy2 = ['Enemy 2', 10000, 'ruler',[],'sky', []]
enemy3 = ['Enemy 3', 10000, 'avenger',[],'beast', []]
game_state.add_enemies(enemy1)
game_state.add_enemies(enemy2)
game_state.add_enemies(enemy3)

# game_state.servants.append(servant2)
game_state.use_skill(game_state.servants[0], game_state.servants[0].skills[1])
# game_state.use_skill(game_state.servants[0], game_state.servants[0].skills[0])

game_state.use_np(game_state.servants[0], np_level=1, overcharge_level=1)
game_state.use_skill(game_state.servants[0], game_state.servants[0].skills[2])

game_state.end_turn()
print(f"{game_state.servants[0]}'s NP gauge is {game_state.servants[0].get_npgauge()}% ")
print(f"{game_state.servants[1]}'s NP gauge is {game_state.servants[1].get_npgauge()}% ")
print(f"{game_state.servants[2]}'s NP gauge is {game_state.servants[2].get_npgauge()}% ")

