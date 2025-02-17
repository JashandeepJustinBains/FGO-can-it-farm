import logging

# Configure logging TODO ADD LOGGING HERE
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class SkillManager:
    def __init__(self, turn_manager, sm_copy=None):
        self.tm = turn_manager
        self.gm = self.tm.gm

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
                'turns': effect['svals'].get('Turn', 0),
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

    def apply_effect(self, effect, servant, ally_target=None):
        if effect.get('funcType'):
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
                targets = self.gm.get_enemies()
            elif target_type == 'ptOther':
                targets = [ally for ally in self.gm.servants if ally != servant]
            elif target_type == 'ptAll':
                targets = self.gm.servants
            elif target_type == 'ptOne':
                targets = [ally_target]
            else:
                targets = []

            # Apply the effect to each target
            check_cond_target = lambda target: not condTarget or all(trait['id'] in [t for t in target.traits] for trait in condTarget)
            check_field_req = lambda: not field_req or any(field['id'] in [f[0] for f in self.gm.fields] for field in field_req)

            for target in targets:
                if check_cond_target(target) and check_field_req():
                    if effect_type in self.effect_functions:
                        self.effect_functions[effect_type](self, effect=effect, target=target)

    def apply_add_state(self, effect, target):
        state = self.extract_state(effect)
        self.apply_buff(target, state)

    def apply_add_state_short(self, effect, target):
        state = self.extract_state(effect)
        self.apply_buff(target, state)

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

    def apply_buff(self, target, state):
        buff = state['buff_name']
        value = state['value']
        functvals = state['functvals']
        tvals = [tval['id'] for tval in state.get('tvals', [])]
        turns = state['turns']
        logging.info(f"added buff {buff} to {target.name}")
        target.buffs.add_buff({'buff': buff, 'functvals': functvals, 'value': value, 'tvals': tvals, 'turns': turns})

    def skill_available(self, servant, skill_num):
        return servant.skills.skill_available(skill_num)


    def use_mystic_code_skill(self, skill_num, target=None):
        mystic_code = self.gm.mc  # Get the equipped mystic code
        if not hasattr(mystic_code, 'cooldowns'):
            mystic_code.cooldowns = {0: 0, 1: 0, 2: 0}

        if mystic_code.cooldowns[skill_num] == 0:
            skill = mystic_code.get_skill_by_num(skill_num)
            print(f"Using Mystic Code skill {skill['name']}")

            for effect in skill['functions']:
                if effect['funcType'] == 'swapServant':
                    # Swap ability handling
                    if target:
                        self.swap_servants(target[0], target[1])
                else:
                    self.apply_effect(effect, target)
            
            # Set the cooldown for the used skill
            mystic_code.cooldowns[skill_num] = skill['cooldown']
        else:
            print(f"Mystic Code skill {skill_num} is on cooldown: {mystic_code.cooldowns[skill_num]} turns remaining")


    def use_skill(self, servant, skill_num, target=None):
        logging.info(f"BEGINNING USE_SKILL OF {servant.name}' SKILL {servant.skills.get_skill_by_num(skill_num+1)}")
        skill_num += 1
        if self.skill_available(servant, skill_num):
            skill = servant.skills.get_skill_by_num(skill_num)
            servant.skills.set_skill_cooldown(skill_num)
            logging.info(f"Skill {skill_num} used. Cooldown remaining: {servant.skills.get_skill_cooldowns()[skill_num]} turns")
            logging.info(f"Applying {servant.name}'s {servant.skills.get_skill_by_num(skill_num)}")
            for effect in skill['functions']:
                # logging.info(f"Applying {servant.name}'s {next(iter(effect.get('buffs', '')), {}).get('name', '')} - Value:{effect['svals'].get('Value','')} for {effect['svals'].get('Turn', '')} turns to '{effect['funcTargetType']}' / target=: {target.name if target else None}")
                self.apply_effect(effect, servant, target)

        else:
            print(f"{servant.name} skill {skill_num} is on cooldown: {servant.skills.cooldowns[skill_num]} turns remaining")
            return False

    def swap_servants(self, frontline_idx, backline_idx):
        # Perform the swap operation
        if (backline_idx == 1 and len(self.gm.servants) > 4) or (backline_idx == 2 and len(self.gm.servants) > 4) or (backline_idx == 3 and len(self.gm.servants) > 5):
            self.gm.swap_servants(frontline_idx - 1, 2 + backline_idx)  # Adjust for 0-based indexing
            print(f"Swapped frontline servant {frontline_idx}:{self.gm.servants[frontline_idx - 1].name} with backline servant {backline_idx + 2}:{self.gm.servants[backline_idx + 2].name}")
        else:
            return False
        
    
    def swap_servants(self):
        # simplified swap operations: swaps backline 2 with frontline 3 if possible, otherwise backline 1 and frontline 3 
        if (len(self.gm.servants) > 5):
            self.gm.swap_servants(2, 4)  # Adjust for 0-based indexing
            print(f"Swapped frontline servant {3}:{self.gm.servants[2].name} with backline servant {2}:{self.gm.servants[4].name}")
            f"Swapped frontline servant {3}:{self.gm.servants[2].name} with backline servant {2}:{self.gm.servants[4].name}"
        if (len(self.gm.servants) > 4):
            self.gm.swap_servants(2, 3)  # Adjust for 0-based indexing
            print(f"Swapped frontline servant {3}:{self.gm.servants[2].name} with backline servant {1}:{self.gm.servants[3].name}")
            logging.info(f"Swapped frontline servant {3}:{self.gm.servants[2].name} with backline servant {1}:{self.gm.servants[3].name}")
        else:
            return False


    def apply_gain_np(self, effect, target):
        state = self.extract_state(effect)

        np_gain_value = state.get('value', 0)
        if state.get('value', 0) == 0:
            np_gain_value = state.get('Value', 0)
        if np_gain_value == 0:
            return False
        target.set_npgauge(np_gain_value / 100)

    def apply_cooldown_reduction(self, effect, target):
        target.skills.decrement_cooldowns(effect['svals']['Value'])

    def apply_transform(self, effect, target):
        return

    def add_field_change(self, effect, target):
        state = self.extract_state(effect)
        self.add_field(state)

    def apply_multiply_np(self, effect, target):
        target.set_npgauge(target.get_npgauge())

    def apply_self_kill(self, effect, target):
        target.kill = True

    def apply_instant_death(self, effect, target):
        print(f"hellllllllllllllooooooooooooooooooooooo DEATH CHANCE CALC??? {effect['funcType']}")
        if effect['funcType'] == "instantDeath":
            deathchance = effect.get('svals', '').get('Rate', '') / 1000
            for i, s in enumerate(self.gm.servants[:3]):
                if s.id == 297:
                    deathchance *= 1.2
                if s.id == 92:
                    deathchance *= 2
            deathrate = target.death_rate / 1000

            print(f"DEATH CHANCE ={deathchance} and DEATHRATE = {deathrate} \n INSTANT DEATH SUCCESS?{True if deathchance*deathrate > 0.5 else False}")

            if deathchance * deathrate > 0.5:
                target.set_hp(target.get_hp())

    effect_functions = {
        'addState': apply_add_state,
        'gainNp': apply_gain_np,
        'addStateShort': apply_add_state_short, 
        'shortenSkill': apply_cooldown_reduction, 
        'addFieldChangeToField': add_field_change,
        'transformServant': apply_transform, 
        'gainMultiplyNp': apply_multiply_np,
        'forceInstantDeath': apply_self_kill,
        'instantDeath': apply_instant_death,
    }
