# Enhanced effect parser for FGO servants skill/NP/passive effects
# Provides a normalized effect schema that can handle the full diversity of effects
# from the FGOCombatSim MongoDB servants collection.
#
# Normalized Effect Schema:
# {
#   "source": "skill|np|passive|transform", 
#   "slot": 1|2|3|null,  # skill slot or null
#   "variant_id": number,  # original id/version if present
#   "funcType": "<string>",
#   "targetType": "<string or list>", 
#   "parameters": { ... },  # normalized numeric parameters
#   "svals": {
#     "base": [...],  # base svals indexed by level
#     "oc": {2: [...], 3: [...], ...}  # overcharge variations by OC level
#   },
#   "buffs": [ { "name":..., "params": {...} }, ... ],
#   "raw": {...}  # original raw object for full fidelity
# }

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
                # Parse into normalized effect schema
                normalized_effect = self._parse_function_to_effect(
                    function, 
                    source="skill", 
                    slot=int(skill['num']), 
                    variant_id=skill.get('id')
                )
                parsed_skill['functions'].append(normalized_effect)
                
                # Keep legacy format for backward compatibility
                legacy_function = {
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
                    legacy_function['buffs'].append(parsed_buff)
                
                # Add both normalized and legacy for transition
                parsed_skill['functions'][-1]['_legacy'] = legacy_function
                
            skills[int(skill['num'])].append(parsed_skill)
        return skills

    def initialize_max_cooldowns(self):
        max_cooldowns = {}
        for i in range(1, 4):  # Skills are numbered 1, 2, 3
            if i in self.skills and len(self.skills[i]) > 0:
                max_cooldowns[i] = self.skills[i][-1]['cooldown']
            else:
                max_cooldowns[i] = 0
        return max_cooldowns

    def get_skill_by_num(self, num):
        if 1 <= num <= 3 and num in self.skills and len(self.skills[num]) > 0:

            if self.melusine_skill == False and self.skills[num][0]['id'] == 888550:
                self.melusine_skill = True
                return self.skills[num][0]
            else:
                return self.skills[num][-1]
        else:
            raise IndexError(f"Skill number {num} is out of range or has no skills")

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

    def _parse_function_to_effect(self, function, source="skill", slot=None, variant_id=None):
        """Parse a function into normalized effect schema."""
        try:
            # Extract base parameters
            func_type = function.get('funcType', 'unknown')
            target_type = function.get('funcTargetType', 'unknown')
            
            # Normalize svals structure - handle all svals variations
            svals_normalized = self._normalize_svals(function)
            
            # Extract numeric parameters from svals
            parameters = self._extract_parameters(function, svals_normalized)
            
            # Parse buffs
            buffs_normalized = []
            for buff in function.get('buffs', []):
                buff_normalized = self._normalize_buff(buff)
                buffs_normalized.append(buff_normalized)
            
            # Create normalized effect
            effect = {
                "source": source,
                "slot": slot,
                "variant_id": variant_id,
                "funcType": func_type,
                "targetType": target_type,
                "parameters": parameters,
                "svals": svals_normalized,
                "buffs": buffs_normalized,
                "raw": function  # Preserve original for diagnostics
            }
            
            return effect
            
        except Exception as e:
            # Fallback to raw preservation if parsing fails
            return {
                "source": source,
                "slot": slot, 
                "variant_id": variant_id,
                "funcType": function.get('funcType', 'unknown'),
                "targetType": function.get('funcTargetType', 'unknown'),
                "parameters": {},
                "svals": {"base": [], "oc": {}},
                "buffs": [],
                "raw": function,
                "_parse_error": str(e)
            }
    
    def _normalize_svals(self, function):
        """Normalize svals structure into base + OC matrix."""
        normalized = {"base": [], "oc": {}}
        
        # Handle base svals
        base_svals = function.get('svals', [])
        if base_svals:
            normalized["base"] = base_svals
        
        # Handle overcharge variations (svals2, svals3, etc.)
        for key, value in function.items():
            if key.startswith('svals') and key != 'svals' and key.replace('svals', '').isdigit():
                oc_level = int(key.replace('svals', ''))
                normalized["oc"][oc_level] = value
        
        return normalized
    
    def _extract_parameters(self, function, svals_normalized):
        """Extract numeric parameters from function and svals."""
        parameters = {}
        
        # Extract common parameters from functvals
        functvals = function.get('functvals', [])
        if functvals:
            parameters['functvals'] = functvals
        
        # Extract from base svals if available
        if svals_normalized["base"]:
            # Try to get the highest level (usually index 9 for max level)
            max_level_idx = min(9, len(svals_normalized["base"]) - 1)
            if max_level_idx >= 0:
                max_level_svals = svals_normalized["base"][max_level_idx]
                if isinstance(max_level_svals, dict):
                    for key, value in max_level_svals.items():
                        if key in ['Value', 'Turn', 'Correction', 'Target', 'Count', 'Rate']:
                            parameters[key.lower()] = value
        
        # Extract field requirements
        field_req = function.get('funcquestTvals', [])
        if field_req:
            parameters['field_requirements'] = field_req
            
        return parameters
    
    def _normalize_buff(self, buff):
        """Normalize buff structure."""
        normalized = {
            "name": buff.get('name', 'unknown'),
            "params": {}
        }
        
        # Extract buff parameters
        tvals = buff.get('tvals', [])
        if tvals:
            normalized["params"]["tvals"] = tvals
        
        # Extract from buff svals
        buff_svals = buff.get('svals', [])
        if buff_svals and len(buff_svals) > 9:
            max_svals = buff_svals[9]
            if isinstance(max_svals, dict):
                for key, value in max_svals.items():
                    if key in ['Value', 'Turn', 'Count', 'Rate']:
                        normalized["params"][key.lower()] = value
        
        return normalized
    
    # Generic effect interpretation helpers
    def get_damage_effects(self, skill_num):
        """Get damage-related effects from a skill."""
        skill = self.get_skill_by_num(skill_num)
        damage_effects = []
        
        for func in skill.get('functions', []):
            func_type = func.get('funcType', '')
            if 'damage' in func_type.lower():
                damage_effects.append(func)
        
        return damage_effects
    
    def get_stat_buffs(self, skill_num):
        """Get stat buff effects from a skill."""
        skill = self.get_skill_by_num(skill_num)
        stat_buffs = []
        
        for func in skill.get('functions', []):
            func_type = func.get('funcType', '')
            if any(stat in func_type.lower() for stat in ['atkup', 'defup', 'busterup', 'artsup', 'quickup', 'npup']):
                stat_buffs.append(func)
        
        return stat_buffs
    
    def get_trait_effects(self, skill_num):
        """Get trait manipulation effects from a skill."""
        skill = self.get_skill_by_num(skill_num)
        trait_effects = []
        
        for func in skill.get('functions', []):
            func_type = func.get('funcType', '')
            if any(trait_op in func_type.lower() for trait_op in ['traitadd', 'applytrait']):
                trait_effects.append(func)
        
        return trait_effects
    
    def get_counter_effects(self, skill_num):
        """Get counter-related effects from a skill."""
        skill = self.get_skill_by_num(skill_num)
        counter_effects = []
        
        for func in skill.get('functions', []):
            # Look for counter patterns in parameters or funcType
            parameters = func.get('parameters', {})
            if 'counter' in func.get('funcType', '').lower() or any('counter' in str(v).lower() for v in parameters.values()):
                counter_effects.append(func)
        
        return counter_effects
