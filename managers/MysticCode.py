import json

class MysticCode:
    def __init__(self, mc_id) -> None:
        self.data = self.load_mystic_code(mc_id)
        self.skills = self.parse_skills(self.data.get('skills', []))

    def load_mystic_code(self, mc_id):
        filename = f"MysticCodes/mc_{mc_id}.json"  # Assuming files are named like "mc_260.json"
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)

    def parse_skills(self, skills_data):
        skills = []
        for skill in skills_data:
            parsed_skill = {
                'id': skill.get('id'),
                'name': skill.get('name'),
                'cooldown': skill.get('coolDown')[-1],  # Assuming max level
                'functions': []
            }
            for function in skill.get('functions', []):
                parsed_function = {
                    'funcType': function.get('funcType'),
                    'funcTargetType': function.get('funcTargetType'),
                    'functvals': function.get('functvals'),
                    'fieldReq': function.get('funcquestTvals', []),
                    'condTarget': function.get('functvals', []),
                    'svals': function.get('svals')[-1] if 'svals' in function else {},
                    'buffs': []
                }
                for buff in function.get('buffs', []):
                    parsed_buff = {
                        'name': buff.get('name'),
                        'tvals': buff['tvals'],
                        'svals': buff.get('svals')[-1] if 'svals' in buff else None
                    }
                    parsed_function['buffs'].append(parsed_buff)
                parsed_skill['functions'].append(parsed_function)
            skills.append(parsed_skill)
        return skills

    def get_skill_by_num(self, num):
        return self.skills[num]
