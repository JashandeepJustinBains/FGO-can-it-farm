from Servant import Servant
from Quest import Quest
from Enemy import Enemy
from beaver import Beaver
import itertools


class GameState:
    def __init__(self):
        self.enemies = [] # list to hold enemy objects
        self.servants = []  # List to hold servant objects
        self.wave = 1  # Track the number of turns
        self.fields = []  # Track the field state

    def end_turn(self):
        # End the turn and decrement buffs
        self.decrement_buffs()
        self.decrement_cooldowns()
        for servant in self.servants[:3]:
            servant.process_end_turn_skills()
        for enemy in self.enemies:
            if enemy.get_hp() > 0:
                return "FAILURE"
        self.wave += 1

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
            state = {}
            state['type'] = 'buff'
            buffs = effect.get('buffs', [])
            if buffs and buffs[0].get('name', 'Unknown') != "Unknown":
                state['buff_name'] = buffs[0].get('name', 'Unknown')
                state['functvals'] = effect.get('functvals', [])
                state['tvals'] = buffs[0].get('tvals', [])  # Ensure tvals are included
            else:
                state['buff_name'] = buffs[0].get('type', 'Unknown') if buffs else 'Unknown'
                tvals = buffs[0].get('tvals', [])
                state['functvals'] = tvals[0].get('id', 'Unknown') if tvals else 'Unknown'
                state['tvals'] = tvals  # Ensure tvals are included

            state['value'] = effect.get('svals', {}).get('Value', 0)
            state['turns'] = effect.get('svals', {}).get('Turn', 0)
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
        tvals = []
        for tval in state.get('tvals', []):
            tvals.append(tval['id'])
        turns = state['turns']

        target.add_buff({'buff': buff, 'functvals': functvals, 'value': value, 'tvals':tvals, 'turns': turns})

    def decrement_buffs(self):
        # Decrement the timer for each buff and remove buffs with 0 time left
        for target in self.enemies + self.servants:
            target.decrement_buffs()
    def decrement_cooldowns(self):
        # Decrement the timer for each buff and remove buffs with 0 time left
        for target in self.servants:
            target.decrement_cooldowns(1)


    def use_skill(self, servant, skill_num, target=None):
        # Use a skill and apply its effects
        if servant.skill_available(skill_num):
            skill = servant.get_skill_by_num(skill_num)
            servant.set_skill_cooldown(skill_num)
            # print(f"Applying {servant.name}'s '{skill['name']}' to '{[funcs['funcTargetType'] for funcs in skill['functions']]}' / target=ally number: {target}")
            for effect in skill['functions']:
                #logger1.info(f"Applying {servant.name}'s '{effect['funcType']}':{effect['buffs']} to '{effect['funcTargetType']}' / target=ally number: {target}")
                print(f"Applying {servant.name}'s '{effect['funcType']}':{effect['buffs']} to '{effect['funcTargetType']}' / target=ally number: {target.name if target else None}")             
                self.apply_effect(effect, servant, target)
        else:
            #logger1.info(f"{servant.name} skill {skill_num} is on cooldown: {servant.cooldowns[skill_num]} turns remaining")
            print(f"{servant.name} skill {skill_num} is on cooldown: {servant.cooldowns[skill_num]} turns remaining")

    
    def use_np(self, servant):
        if servant.get_npgauge() >= 99:
            servant.set_npgauge(0)  # Reset NP gauge after use
            functions = servant.get_np_values(servant.np_level, servant.get_oc_level())
            maintarget = None
            max_hp = 0

            # Identify the enemy with the highest HP
            for enemy in self.enemies:
                if enemy.get_hp() > max_hp:
                    max_hp = enemy.get_hp()
                    maintarget = enemy

            # Apply effects and damage
            for i, func in enumerate(functions):

                if func['funcType'] == 'damageNp' or func['funcType'] == 'damageNpIndividual':
                    servant.process_buffs()
                    print(self.servants[0].get_current_buffs())
                    for enemy in self.enemies:
                        self.apply_np_damage(servant, enemy)
                elif func['funcType'] == 'damageNpIndividualSum':
                    # print("firing NP")
                    servant.process_buffs()
                    print(self.servants[0].get_current_buffs())

                    for enemy in self.enemies:
                        self.apply_np_odd_damage(servant, enemy)
                else:
                    if func['funcTargetType'] == 'enemyAll':
                        for enemy in self.enemies:
                            self.apply_effect(func, servant)
                    if func['funcTargetType'] == 'enemy':
                        self.apply_effect(func, maintarget)
                    else:
                        self.apply_effect(func, servant)
        else:
            print(f"{servant.name} does not have enough NP gauge: {servant.get_npgauge()}")

    def apply_np_damage(self, servant, target):
        card_damage_value = None
        card_type = servant.get_cardtype()
        card_np_value = 1
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
            card_np_value = 3
            card_mod = servant.get_a_up()
            enemy_res_mod = target.get_a_resdown()

        class_modifier = servant.get_class_multiplier(target.get_class())
        attribute_modifier = servant.get_attribute_modifier(target)
        atk_mod = servant.get_atk_mod()
        enemy_def_mod = target.get_def()
        power_mod = servant.get_power_mod(target)
        self_damage_mod = 0
        np_damage_mod = servant.get_np_damage_mod()
        np_damage_multiplier, np_correction_target, super_effective_modifier = servant.get_np_damage_values(np_level=servant.np_level, oc=servant.get_oc_level())
        is_super_effective = 1 if np_correction_target in target.traits else 0
        servant_atk = servant.get_atk_at_level()

        total_damage = (servant_atk * np_damage_multiplier * (card_damage_value * (1 + card_mod - enemy_res_mod)) *
                        class_modifier * attribute_modifier * 0.23 * (1 + atk_mod - enemy_def_mod) *
                        (1 + self_damage_mod + np_damage_mod + power_mod) * 
                        (1 + (((super_effective_modifier if super_effective_modifier else 0) - 1) * is_super_effective)))
        np_gain = servant.get_npgain() * servant.get_np_gain_mod()
        np_distribution = servant.get_npdist()
        
        damage_per_hit = [total_damage * value/100 for value in np_distribution]

        cumulative_damage = 0
        for i, hit in enumerate(np_distribution):
            hit_damage = damage_per_hit[i]
            cumulative_damage += hit_damage
            overkill_bonus = 1.5 if cumulative_damage > target.get_hp() else 1
            specific_enemy_modifier = target.np_per_hit_mult

            np_per_hit = (np_gain * card_np_value * (1 + card_mod) * specific_enemy_modifier * overkill_bonus)

            if card_type != 'buster':
                servant.set_npgauge(np_per_hit)

            target.set_hp(hit_damage)
            # print(f"{servant.name} deals {hit_damage} to {target.name} who has {target.get_hp()} hp left and gains {np_per_hit}% np")

            # if target.get_hp() <= 0:
                # print(f"{target.get_name()} has been defeated by hit {i+1}!")

        print(f"{servant.get_name()} attacks {target.get_name()} with Noble Phantasm for {'%.0f' % total_damage} total damage!")
  
  
    def apply_np_odd_damage(self, servant, target):
        card_damage_value = None
        card_type = servant.get_cardtype()
        card_np_value = 1
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
            card_np_value = 3
            card_mod = servant.get_a_up()
            enemy_res_mod = target.get_a_resdown()

        class_modifier = servant.get_class_multiplier(target.get_class())
        attribute_modifier = servant.get_attribute_modifier(target)
        atk_mod = servant.get_atk_mod()
        enemy_def_mod = target.get_def()
        power_mod = servant.get_power_mod()
        self_damage_mod = 0
        np_damage_mod = servant.get_np_damage_mod()

        # servant applies their own super effective requires a different approach
        # check if the target is in tagetList for musashi
        # if Target1 == 0 that means count number of times ids in the TargetList are in servant.buffs[]
        # if Target1 == 1 that means count number of times ids in the TargetList are in target.buffs[]
        # correction = "Value2" + N * "Correction" to max of N="ParamAddMaxCount"

        # TODO test with allies who count buffs placed on them ,if this doesnt work jsut hard code it cuz lawwdd knows ereshkigal is gonna be ap ain itn the ass

        np_damage_multiplier, \
        np_damage_correction_init,\
        np_correction,\
        np_correction_id ,\
        np_correction_target = servant.get_np_damage_values(np_level=servant.np_level, oc=servant.get_oc_level())
        
        servant_atk = servant.get_atk_at_level() * servant.get_class_base_multiplier()
        is_super_effective = 1
        super_effective_modifier = 1
        if np_correction_target == 1:
            for id in np_correction_id:
                super_effective_modifier += np_correction * target.traits.count(id)
        else:
            for id in np_correction_id:
                cum = 0
                if servant.name == "Super Aoko":
                    for buff in servant.buffs:
                        if buff['buff'] == "Magic Bullet":
                            cum += 1
                    super_effective_modifier += cum * np_correction

        total_damage = (servant_atk * np_damage_multiplier * (card_damage_value * (1 + card_mod - enemy_res_mod)) *
                        class_modifier * attribute_modifier * 0.23 * (1 + atk_mod - enemy_def_mod) *
                        (1 + power_mod + self_damage_mod + np_damage_mod) *
                        (1 + ((super_effective_modifier - 1) * is_super_effective)))
        np_gain = servant.get_npgain() * servant.get_np_gain_mod()
        np_distribution = servant.get_npdist()
        damage_per_hit = [total_damage * value for value in np_distribution]

        cumulative_damage = 0
        for i, hit in enumerate(np_distribution):
            hit_damage = damage_per_hit[i]
            cumulative_damage += hit_damage
            overkill_bonus = 1.5 if cumulative_damage > target.get_hp() else 1
            specific_enemy_modifier = target.np_per_hit_mult  # Adjust based on enemy class and traits

            np_per_hit = (np_gain * card_np_value * (1 + card_mod) * specific_enemy_modifier * overkill_bonus)
            
            if card_type != 'buster':
                servant.set_npgauge(np_per_hit)
            
            target.set_hp(hit_damage)

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
        np_gain_value = state.get('value', 0) / 100
        target.set_npgauge(np_gain_value)

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
        target.decrement_cooldowns(effect)

    def apply_effect(self, effect, servant, ally_target=None):
        effect_type = effect['funcType']
        target_type = effect['funcTargetType']
        condTarget = effect.get('condTarget', [])
        field_req = effect.get('fieldReq', {})

        if ally_target is None:
            ally_target = servant
        # Determine the targets based on target type
        if target_type == 'self':
            targets = [servant]
        elif target_type == 'enemyAll':
            targets = self.enemies
        elif target_type == 'ptOther':
            targets = [ally for ally in self.servants if ally != servant]
        elif target_type == 'ptAll':
            targets = self.servants
        elif target_type == 'ptOne':
            targets = [ally_target]
        else:
            targets = []

        # Apply the effect to each target
        # print(f"attempting to use effect: {effect_type}: {(effect['buffs'])} on {target_type} ")

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
        # 'absorbNpturn': apply_np_absorb, 
        # 'gainStar': apply_gain_star, 
        # 'lossNp': apply_loss_np, 
        # 'gainNpFromTargets': apply_np_absorb, 
        # 'gainMultiplyNp': apply_multiply_np, 
    }

    def simulate_permutation(self, permutation):
        for token in permutation:
            self.execute_token(token)
        # Check if the NP can be used or the wave is cleared
        # Return True if successful, otherwise False
        return True

    # TODO IMPLEMENT THIS
    # def swap_servant(servants, field_positions, old_index, new_servant):
    #     field_positions[old_index] = new_servant
    #     return generate_tokens_for_positions(field_positions)

    def execute_token(self, token):
        for servant in self.servants:
            print(servant)
        token_actions = {
            'a': lambda: self.use_skill(self.servants[0], 0),
            'a1': lambda: self.use_skill(self.servants[0], 0, self.servants[1]),
            'a2': lambda: self.use_skill(self.servants[0], 0, self.servants[2]),
            'b': lambda: self.use_skill(self.servants[0], 1),
            'b1': lambda: self.use_skill(self.servants[0], 1, self.servants[1]),
            'b2': lambda: self.use_skill(self.servants[0], 1, self.servants[2]),
            'c': lambda: self.use_skill(self.servants[0], 2),
            'c1': lambda: self.use_skill(self.servants[0], 2, self.servants[1]),
            'c2': lambda: self.use_skill(self.servants[0], 2, self.servants[2]),
            'd': lambda: self.use_skill(self.servants[1], 0),
            'd1': lambda: self.use_skill(self.servants[1], 0, self.servants[0]),
            'd2': lambda: self.use_skill(self.servants[1], 0, self.servants[2]),
            'e': lambda: self.use_skill(self.servants[1], 1),
            'e1': lambda: self.use_skill(self.servants[1], 1, self.servants[0]),
            'e2': lambda: self.use_skill(self.servants[1], 1, self.servants[2]),
            'f': lambda: self.use_skill(self.servants[1], 2),
            'f1': lambda: self.use_skill(self.servants[1], 2, self.servants[0]),
            'f2': lambda: self.use_skill(self.servants[1], 2, self.servants[2]),
            'g': lambda: self.use_skill(self.servants[2], 0),
            'g1': lambda: self.use_skill(self.servants[2], 0, self.servants[0]),
            'g2': lambda: self.use_skill(self.servants[2], 0, self.servants[1]),
            'h': lambda: self.use_skill(self.servants[2], 1),
            'h1': lambda: self.use_skill(self.servants[2], 1, self.servants[0]),
            'h2': lambda: self.use_skill(self.servants[2], 1, self.servants[1]),
            'i': lambda: self.use_skill(self.servants[2], 2),
            'i1': lambda: self.use_skill(self.servants[2], 2, self.servants[0]),
            'i2': lambda: self.use_skill(self.servants[2], 2, self.servants[1]),
            '4': lambda: self.use_np(self.servants[0]),
            '5': lambda: self.use_np(self.servants[1]),
            '6': lambda: self.use_np(self.servants[2]),
            '#': lambda: self.end_turn(),
        }

        action = token_actions.get(token, lambda: print(f"Unknown token: {token}"))
        action()

def generate_tokens_for_positions(servants):
    all_tokens = []
    skill_tokens = [['a', 'b', 'c'], ['d', 'e', 'f'], ['g', 'h', 'i']]
    
    for i in range(3):  # Only 3 positions on the field
        servant = servants[i]
        servant_tokens = []
        for skill, token in zip(servant.get_skills(), skill_tokens[i]):
            has_ptOne = any(func['funcTargetType'] == 'ptOne' for func in skill['functions'])
            if has_ptOne:
                for j in range(1, 4):
                    servant_tokens.append(f"{token}{j}")
            else:
                servant_tokens.append(token)
        all_tokens.append(servant_tokens)
    return all_tokens
