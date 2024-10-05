class Skills:
    def __init__(self, skills_data):
        self.skills = self.parse_skills(skills_data)
        self.cooldowns = {0:0, 1:0, 2:0}
        self.max_cooldowns

    def parse_skills(self, skills_data):
        skills = []
        for skill in skills_data:
            parsed_skill = {
                'id': skill.get('id'),
                'name': skill.get('name'),
                'cooldown': skill.get('coolDown')[9],  # This is the maximum cooldown
                'functions': []
            }
            for function in skill.get('functions', []):
                parsed_function = {
                    'funcType': function.get('funcType'),
                    'funcTargetType': function.get('funcTargetType'),
                    'functvals': function.get('functvals'),
                    'fieldReq': function.get('funcquestTvals', []),
                    'condTarget': function.get('functvals', []),
                    'svals': function.get('svals')[9],
                    'buffs': []
                }
                for buff in function.get('buffs', []):
                    parsed_buff = {
                        'name': buff.get('name'),
                        'tvals': buff.get('tvals', []),  # Ensure tvals are included
                        'svals': buff.get('svals')[9] if len(buff.get('svals', [])) > 9 else None,
                        'value': buff.get('svals')[9]['Value'] if len(buff.get('svals', [])) > 9 else 0  # Extract value from svals
                    }
                    parsed_function['buffs'].append(parsed_buff)
                parsed_skill['functions'].append(parsed_function)
            skills.append(parsed_skill)
        self.max_cooldowns = {0: skills[0]['cooldown'], 1:skills[1]['cooldown'], 2:skills[2]['cooldown']}
        return skills

    def get_skill_by_num(self, num):
        if 0 <= num < len(self.skills):
            return self.skills[num]
        else:
            raise IndexError(f"Skill number {num} is out of range")

    def __iter__(self):
        return iter(self.skills)

    def get_skill_names(self):
        return [skill['name'] for skill in self.skills]

    def get_skill_cooldowns(self):
        return self.cooldowns

    def get_skill_details(self, skill_num):
        if 0 <= skill_num < len(self.skills):
            return self.skills[skill_num]
        else:
            raise IndexError(f"Skill number {skill_num} is out of range")

    def decrement_cooldowns(self, turns: int):
        for skill_num in self.cooldowns:
            if self.cooldowns[skill_num] > 0:
                self.cooldowns[skill_num] = max(0, self.cooldowns[skill_num] - turns)

    def skill_available(self, skill_num):
        return self.cooldowns[skill_num] == 0

    def set_skill_cooldown(self, skill_num):
        self.cooldowns[skill_num] = self.max_cooldowns[skill_num]

    def __repr__(self):
        return f"Skills(skills={self.skills}, cooldowns={self.cooldowns}, max_cooldowns={self.max_cooldowns})"
