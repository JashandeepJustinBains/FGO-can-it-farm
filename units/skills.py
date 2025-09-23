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
    def __init__(self, skills_data, servant=None, append_5=False, mystic_code=None):
        """
        Initialize Skills with variant-aware selection.
        
        Args:
            skills_data: Skills data from servant JSON (could be legacy or skillSvts)
            servant: Servant instance (provides variant_svt_id for selection)
            append_5: Whether to include append skill 5
            mystic_code: Mystic code instance
        """
        self.servant = servant
        self.skills = self.parse_skills(skills_data)
        self.cooldowns = {1: 0, 2: 0, 3: 0}
        self.max_cooldowns = self.initialize_max_cooldowns()
        self.cooldown_reduction_applied = {1: False, 2: False, 3: False}
        self.mystic_code = mystic_code
        self.melusine_skill = False
        self.append_5 = append_5

    def parse_skills(self, skills_data):
        """
        Parse skills with variant-aware selection.
        
        For skillSvts format:
        1. Filter skills by variant_svt_id
        2. For each skill number, pick the entry with highest id
        3. Use last svals and cooldown values (level 10/upgraded)
        
        For legacy format: use as-is for backwards compatibility
        """
        skills = {1: [], 2: [], 3: []}
        
        # Check if this is skillSvts format or legacy
        if skills_data and isinstance(skills_data, list) and len(skills_data) > 0:
            first_skill = skills_data[0]
            is_skill_svts = 'svtId' in first_skill
            
            if is_skill_svts and self.servant:
                # Use variant-aware selection for skillSvts
                skills = self._parse_skill_svts(skills_data)
            else:
                # Use legacy parsing
                skills = self._parse_legacy_skills(skills_data)
        
        return skills
    
    def _extract_number(self, value):
        """Extract number handling MongoDB format."""
        if isinstance(value, dict) and '$numberInt' in value:
            return int(value['$numberInt'])
        return int(value) if value is not None else 0
    
    def _parse_skill_svts(self, skill_svts):
        """Parse skillSvts format with variant-aware selection."""
        skills = {1: [], 2: [], 3: []}
        variant_svt_id = self.servant.variant_svt_id
        
        # Group skills by number
        skills_by_num = {}
        for skill in skill_svts:
            num = self._extract_number(skill.get('num', 0))
            if num not in skills_by_num:
                skills_by_num[num] = []
            skills_by_num[num].append(skill)
        
        for skill_num in [1, 2, 3]:
            if skill_num not in skills_by_num:
                continue
                
            candidate_skills = skills_by_num[skill_num]
            
            # Step 1: Filter by variant_svt_id if possible
            variant_matches = [s for s in candidate_skills if self._extract_number(s.get('svtId')) == variant_svt_id]
            
            # Step 2: If no variant matches, use all candidates
            if variant_matches:
                candidates = variant_matches
            else:
                candidates = candidate_skills
            
            # Step 3: Pick entry with highest id
            if candidates:
                selected_skill = max(candidates, key=lambda s: self._extract_number(s.get('id', 0)))
                parsed_skill = self._parse_single_skill(selected_skill, use_max_level=True)
                skills[skill_num].append(parsed_skill)
        
        return skills
    
    def _parse_legacy_skills(self, skills_data):
        """Parse legacy skills format for backwards compatibility."""
        skills = {1: [], 2: [], 3: []}
        for skill in skills_data:
            parsed_skill = self._parse_single_skill(skill, use_max_level=True)
            skill_num = self._extract_number(skill.get('num', 1))
            skills[skill_num].append(parsed_skill)
        return skills
    
    def _parse_single_skill(self, skill, use_max_level=True):
        """
        Parse a single skill entry.
        
        Args:
            skill: Skill data dict
            use_max_level: If True, use last elements in svals/cooldown arrays (level 10)
        """
        cooldown_array = skill.get('coolDown', [])
        if use_max_level and cooldown_array:
            # Use last cooldown (level 10/most upgraded)
            cooldown = self._extract_number(cooldown_array[-1]) if cooldown_array else 0
        else:
            # Use level 1 cooldown
            cooldown = self._extract_number(cooldown_array[0]) if cooldown_array else 0
        
        parsed_skill = {
            'id': self._extract_number(skill.get('id')),
            'name': skill.get('name'),
            'cooldown': cooldown,
            'functions': []
        }
        
        for function in skill.get('functions', []):
            # Parse into normalized effect schema
            normalized_effect = self._parse_function_to_effect(
                function, 
                source="skill",
                slot=self._extract_number(skill.get('num')),
                variant_id=self._extract_number(skill.get('id')),
                use_max_level=use_max_level
            )
            parsed_skill['functions'].append(normalized_effect)
            
            # Keep legacy format for backward compatibility
            svals = function.get('svals', [])
            if use_max_level and svals:
                # Use last svals element (level 10)
                svals_value = svals[-1] if svals else {}
            else:
                # Use first svals element (level 1)  
                svals_value = svals[0] if svals else {}
            
            parsed_function = {
                'funcType': function.get('funcType'),
                'funcTargetType': function.get('funcTargetType'),
                'functvals': function.get('functvals'),
                'fieldReq': function.get('funcquestTvals', []),
                'condTarget': function.get('functvals', []),
                'svals': svals_value,
                'buffs': []
            }
            
            for buff in function.get('buffs', []):
                buff_svals = buff.get('svals', [])
                if use_max_level and buff_svals:
                    buff_svals_value = buff_svals[-1]
                else:
                    buff_svals_value = buff_svals[0] if buff_svals else None
                
                parsed_buff = {
                    'name': buff.get('name'),
                    'tvals': buff.get('tvals', []),
                    'svals': buff_svals_value,
                    'value': buff_svals_value.get('Value', 0) if buff_svals_value else 0
                }
                parsed_function['buffs'].append(parsed_buff)
            parsed_skill['functions'].append(parsed_function)
        
        return parsed_skill
    
    def _parse_function_to_effect(self, function, source, slot=None, variant_id=None, use_max_level=True):
        """Parse function into normalized effect schema."""
        svals = function.get('svals', [])
        if use_max_level and svals:
            base_svals = svals[-1:]  # Last element as array
        else:
            base_svals = svals[:1]  # First element as array
        
        normalized_effect = {
            "source": source,
            "slot": slot,
            "variant_id": variant_id,
            "funcType": function.get('funcType', 'unknown'),
            "targetType": function.get('funcTargetType', 'unknown'),
            "parameters": {},
            "svals": {
                "base": base_svals,
                "oc": {}  # TODO: handle overcharge variations if present
            },
            "buffs": [],
            "raw": function
        }
        
        return normalized_effect

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
        return f"Skills(skills={self.skills}, cooldowns={self.cooldowns}, max_cooldowns={self.max_cooldowns}, cooldown_reduction_applied={self.cooldown_reduction_applied})"
