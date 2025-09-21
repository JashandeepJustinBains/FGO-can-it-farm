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
            print(f"the cooldown of the {self.get_skill_by_num(skill_num)['name']} is currently {self.cooldowns[skill_num]} and the max cooldown is {self.max_cooldowns[skill_num]}")
            self.cooldowns[skill_num] = self.max_cooldowns[skill_num] - 1
            print(f"the cooldown of the {self.get_skill_by_num(skill_num)['name']} is currently {self.cooldowns[skill_num]} and the max cooldown is {self.max_cooldowns[skill_num]}")
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
                chosen_marker = " (chosen)" if variant == self.get_skill_by_num(slot_num) else ""
                
                lines.append(f"    ver {i + 1} | {context} | {skill_name} (ID: {skill_id}) | CD: {cooldown} | effects: {effects_summary}{chosen_marker}")
        
        # Add cooldown information
        lines.append(f"  Current cooldowns: {self.cooldowns}")
        lines.append(f"  Max cooldowns: {self.max_cooldowns}")
        
        return "\n".join(lines)
    
    def _summarize_skill_effects(self, skill_variant):
        """Create a brief summary of skill effects while preserving raw data indicators."""
        if not skill_variant.get('functions'):
            return "raw effects preserved"
        
        effect_types = []
        for func in skill_variant['functions'][:3]:  # Limit to first 3 for brevity
            func_type = func.get('funcType', 'unknown')
            target_type = func.get('funcTargetType', 'unknown')
            effect_types.append(f"{func_type}({target_type})")
        
        if len(skill_variant['functions']) > 3:
            effect_types.append("...")
            
        return f"raw effects preserved: {', '.join(effect_types)}" if effect_types else "raw effects preserved"
