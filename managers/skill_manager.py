class SkillManager:
    def __init__(self, turn_manager):
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
            targets = self.gm.enemies
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

        target.buffs.add_buff({'buff': buff, 'functvals': functvals, 'value': value, 'tvals': tvals, 'turns': turns})

    def skill_available(self, servant, skill_num):
        return servant.skills.skill_available(skill_num)

    def use_skill(self, servant, skill_num, target=None):
        if self.skill_available(servant, skill_num):
            skill = servant.skills.get_skill_by_num(skill_num)
            # print(f'Use {servant.name} skill {skill_num} on {target.name if target else None}')
            servant.skills.set_skill_cooldown(skill_num)
            for effect in skill['functions']:
                # print(f"Applying {servant.name}'s {next(iter(effect.get('buffs','')), {}).get('name', '')} - Value:{effect['svals']['Value']} for {effect['svals'].get('Turn', '')} turns to '{effect['funcTargetType']}' / target=: {target.name if target else None}")             
                self.apply_effect(effect, servant, target)
        else:
            print(f"{servant.name} skill {skill_num} is on cooldown: {servant.skills.cooldowns[skill_num]} turns remaining")

    def apply_gain_np(self, effect, target):
        state = self.extract_state(effect)
        np_gain_value = state.get('value', 0) / 100
        target.set_npgauge(np_gain_value)

    def apply_cooldown_reduction(self, effect, target):
        target.skills.decrement_cooldowns(effect['svals']['Value'])

    def apply_transform(self, effect, target):
        return

    def add_field_change(self, effect, target):
        state = self.extract_state(effect)
        self.add_field(state)

    effect_functions = {
        'addState': apply_add_state,
        'gainNp': apply_gain_np,
        'addStateShort': apply_add_state_short, 
        'shortenSkill': apply_cooldown_reduction, 
        'addFieldChangeToField': add_field_change,
        'transformServant': apply_transform, 
    }
