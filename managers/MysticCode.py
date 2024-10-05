from data import class_advantage_matrix, attribute_dict, class_indices, base_multipliers, traits_dict, character_list
from connectDB import db
import pandas as pd

class MysticCode:
    def __init__(self, name) -> None:
        self.data = select_mc(name)
        skills = self.parse_skills(self.data.get('skills', []))
    
    def parse_skills(self, skills_data):
        skills = []
        for skill in skills_data:
            parsed_skill = {
                'id': skill.get('id'),
                'name': skill.get('name'),
                'cooldown': skill.get('coolDown')[9]-1, #TODO HERE IS WHERE APPEND 5 IS ASSUMED
                'functions': []
            }
            for function in skill.get('functions', []):
                parsed_function = {
                    'funcType': function.get('funcType'),
                    'funcTargetType': function.get('funcTargetType'),
                    'functvals': function.get('functvals'),
                    'fieldReq': function.get('funcquestTvals', []),
                    'condTarget': function.get('functvals',[]),
                    'svals': function.get('svals')[9],
                    'buffs': []
                }
                for buff in function.get('buffs', []):
                    parsed_buff = {
                        'name': buff.get('name'),
                        'tvals': buff['tvals'],
                        'svals': buff.get('svals')[9] if len(buff.get('svals', [])) > 9 else None
                    }
                    parsed_function['buffs'].append(parsed_buff)
                parsed_skill['functions'].append(parsed_function)
            skills.append(parsed_skill)
        return skills
    
    def getskill1(self):
        return self.skills[0]
    def getskill2(self):
        return self.skills[1]
    def getskill3(self):
        return self.skills[2]
    
def select_mc(name):
    mc = db.mysticcodes.find_one({'name': name})
    return mc # Ensure mystic code is an integer

