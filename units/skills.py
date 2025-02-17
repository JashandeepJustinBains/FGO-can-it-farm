class Skills:
    def __init__(self, skills_data, mystic_code=None):
        self.skills = self.parse_skills(skills_data)
        self.cooldowns = {1: 0, 2: 0, 3: 0}
        self.max_cooldowns = self.initialize_max_cooldowns()
        self.cooldown_reduction_applied = {1: False, 2: False, 3: False}
        self.mystic_code = mystic_code  # Initialize Mystic Code
        self.melusine_skill = False

    def parse_skills(self, skills_data):
        skills = {1:[], 2:[], 3:[]}
        for skill in skills_data:
            parsed_skill = {
                'id': skill.get('id'),
                'name': skill.get('name'),
                'cooldown': skill.get('coolDown')[9] if len(skill.get('coolDown', [])) > 9 else 0,
                'functions': []
            }
            for function in skill.get('functions', []):
                parsed_function = {
                    'funcType': function.get('funcType'),
                    'funcTargetType': function.get('funcTargetType'),
                    'functvals': function.get('functvals'),
                    'fieldReq': function.get('funcquestTvals', []),
                    'condTarget': function.get('functvals', []),
                    'svals': function.get('svals')[9] if len(function.get('svals', [])) > 9 else {},
                    'buffs': []
                }
                for buff in function.get('buffs', []):
                    parsed_buff = {
                        'name': buff.get('name'),
                        'tvals': buff.get('tvals', []),
                        'svals': buff.get('svals')[9] if len(buff.get('svals', [])) > 9 else None,
                        'value': buff.get('svals')[9]['Value'] if len(buff.get('svals', [])) > 9 else 0
                    }
                    parsed_function['buffs'].append(parsed_buff)
                parsed_skill['functions'].append(parsed_function)
            skills[int(skill['num'])].append(parsed_skill)
        return skills

    def initialize_max_cooldowns(self):
        max_cooldowns = {}
        for i in range(1, len(self.skills) + 1):
            max_cooldowns[i] = self.skills[i][-1]['cooldown']
        return max_cooldowns

    def get_skill_by_num(self, num):
        if 1 <= num < len(self.skills) + 1:

            if self.melusine_skill == False and self.skills[num][0]['id'] == 888550:
                self.melusine_skill = True
                return self.skills[num][0]
            else:
                return self.skills[num][-1]
        else:
            raise IndexError(f"Skill number {num} is out of range")

    def __iter__(self):
        return iter(self.skills)

    def get_skill_names(self):
        return [skill['name'] for skill in self.skills]

    def get_skill_cooldowns(self):
        return self.cooldowns

    def decrement_cooldowns(self, turns: int):
        for skill_num in self.cooldowns:
            if self.cooldowns[skill_num] > 0:
                self.cooldowns[skill_num] = max(0, self.cooldowns[skill_num] - turns)

    def skill_available(self, skill_num):
        return self.cooldowns[skill_num] == 0

    def set_skill_cooldown(self, skill_num):
        if not self.cooldown_reduction_applied[skill_num]:
            # print(f"BEFORE SKILL USE: {self.get_skill_by_num(skill_num)['name']} is currently {self.cooldowns[skill_num]} and the max cooldown is {self.max_cooldowns[skill_num]}")
            self.cooldowns[skill_num] = self.max_cooldowns[skill_num] - 1
            # print(f"AFTER SKILL USE: {self.get_skill_by_num(skill_num)['name']} is currently {self.cooldowns[skill_num]} and the max cooldown is {self.max_cooldowns[skill_num]}")
            self.cooldown_reduction_applied[skill_num] = True
        else:
            self.cooldowns[skill_num] = self.max_cooldowns[skill_num]

    def use_mystic_code_skill(self, skill_num):
        if self.mystic_code and 0 <= skill_num < len(self.mystic_code.skills):
            skill = self.mystic_code.get_skill_by_num(skill_num)
            # Apply skill effects
            print(f"Using Mystic Code skill: {skill['name']}")
            # Handle cooldown for mystic code skills (if applicable)
            # Similar cooldown logic for mystic codes, if needed
        else:
            raise IndexError(f"Mystic Code skill number {skill_num} is out of range")

    def __repr__(self):
        return f"Skills(skills={self.skills}, cooldowns={self.cooldowns}, max_cooldowns={self.max_cooldowns}, cooldown_reduction_applied={self.cooldown_reduction_applied})"
