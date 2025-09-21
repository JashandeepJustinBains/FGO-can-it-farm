class Skills:
    def __init__(self, skills_data, append_5, mystic_code=None):
        self.skills = self.parse_skills(skills_data)
        self.cooldowns = {1: 0, 2: 0, 3: 0}
        self.max_cooldowns = self.initialize_max_cooldowns()
        self.cooldown_reduction_applied = {1: False, 2: False, 3: False}
        self.mystic_code = mystic_code  # Initialize Mystic Code
        self.melusine_skill = False
        self.append_5 = append_5

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
        if not self.cooldown_reduction_applied[skill_num] and self.append_5:
            self.cooldowns[skill_num] = self.max_cooldowns[skill_num] - 1
            self.cooldown_reduction_applied[skill_num] = True
        else:
            self.cooldowns[skill_num] = self.max_cooldowns[skill_num]

    def __repr__(self):
        return self._format_skills_repr()
    
    def _format_skills_repr(self):
        """Format skills into human-readable representation showing variants per slot."""
        if not self.skills:
            return "Skills(no skills available)"
        
        lines = ["Skills:"]
        
        for slot_num in sorted(self.skills.keys()):
            skill_variants = self.skills[slot_num]
            if not skill_variants:
                continue
                
            lines.append(f"  Skill {slot_num}:")
            
            for i, variant in enumerate(skill_variants):
                # Determine variant context
                if i == 0:
                    context = "base"
                elif len(skill_variants) == 2:
                    context = "requires upgrade"
                else:
                    context = f"variant {i + 1}"
                
                skill_name = variant.get('name', 'Unknown Skill')
                skill_id = variant.get('id', 'unknown')
                cooldown = variant.get('cooldown', 0)
                
                # Format effects summary
                effects_summary = self._summarize_skill_effects(variant)
                
                # Check if this is the chosen/default version
                chosen_variant = self.get_skill_by_num(slot_num)
                is_chosen = chosen_variant and chosen_variant.get('id') == variant.get('id')
                chosen_marker = " [CHOSEN]" if is_chosen else ""
                
                lines.append(f"    ver {i + 1} | {context}: {skill_name} | cooldown: {cooldown} | {effects_summary}{chosen_marker}")
        
        return "\n".join(lines)
    
    def _summarize_skill_effects(self, skill_variant):
        """Create a brief summary of skill effects while preserving raw data indicators."""
        functions = skill_variant.get('functions', [])
        if not functions:
            return "effects: raw preserved"
        
        effect_count = len(functions)
        return f"effects: raw preserved ({effect_count} functions)"
