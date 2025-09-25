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
        # For skillSvts format we store raw entries and select the proper
        # skill at use-time (dynamic selection) so runtime ascension/costume
        # changes (e.g., via Servant.change_ascension or skill effects)
        # are respected. Legacy format remains parsed eagerly.
        parsed = self.parse_skills(skills_data)
        # parsed may be a dict mapping skill numbers -> parsed entries for legacy
        self._is_skill_svts = isinstance(parsed, dict) and any(isinstance(v, list) and v and 'raw_candidates' in v[0] for v in parsed.values())
        if self._is_skill_svts:
            # keep parsed structure but will select on demand
            self.skills = parsed
        else:
            self.skills = parsed
        self.cooldowns = {1: 0, 2: 0, 3: 0}
        self.max_cooldowns = self.initialize_max_cooldowns()
        self.cooldown_reduction_applied = {1: False, 2: False, 3: False}
        self.mystic_code = mystic_code
        self.melusine_skill = False
        self.append_5 = append_5

    def parse_skills(self, skills_data):
        """
        Parse skills with variant-aware selection.
        
        For skillSvts format (nested within skills):
        1. Each skill object has its own skillSvts array
        2. Store raw candidates for deferred selection 
        3. Use current servant variant_svt_id at runtime in get_skill_by_num
        
        For legacy format: use as-is for backwards compatibility
        """
        skills = {1: [], 2: [], 3: []}
        
        # Check if this is nested skillSvts format or legacy
        if skills_data and isinstance(skills_data, list) and len(skills_data) > 0:
            first_skill = skills_data[0]
            has_nested_skill_svts = 'skillSvts' in first_skill
            
            if has_nested_skill_svts:
                # For nested skillSvts format, store raw candidate lists per slot and
                # defer final selection to get_skill_by_num so selection can
                # consider the servant's current ascension/variant at call time.
                skills = self._parse_nested_skill_svts(skills_data)
            else:
                # If the caller provided a servant with a computed variant, and
                # there exists a top-level `skillSvts` in the servant data, we
                # prefer using those variant candidates rather than the legacy
                # skill entries. This makes variant-aware selection the
                # default when the API supplies a variant id.
                if self.servant and isinstance(self.servant, object):
                    svc_data = getattr(self.servant, 'data', {}) or {}
                    top_skill_svts = svc_data.get('skillSvts', [])
                    if top_skill_svts:
                        skills = self._parse_top_level_skill_svts(top_skill_svts)
                    else:
                        # Try to discover any scattered 'skillSvts' blocks
                        # elsewhere in the servant JSON and use them if present.
                        discovered = self._collect_skill_svts_from_data(svc_data)
                        if discovered:
                            skills = self._parse_top_level_skill_svts(discovered)
                        else:
                            skills = self._parse_legacy_skills(skills_data)
                else:
                    # Use legacy parsing
                    skills = self._parse_legacy_skills(skills_data)
        
        return skills
    
    def _extract_number(self, value):
        """Extract number handling MongoDB format."""
        if isinstance(value, dict) and '$numberInt' in value:
            return int(value['$numberInt'])
        return int(value) if value is not None else 0
    
    def _parse_nested_skill_svts(self, skills_data):
        """Parse nested skillSvts format where each skill has its own skillSvts array.
        
        Each skill object has a 'skillSvts' array with different variant entries.
        We store these as raw candidates for dynamic selection at runtime.
        """
        skills = {1: [], 2: [], 3: []}
        
        for skill in skills_data:
            skill_num = self._extract_number(skill.get('num', 0))
            if skill_num not in [1, 2, 3]:
                continue
                
            skill_svts = skill.get('skillSvts', [])
            if skill_svts:
                # Create candidate entries by combining base skill data with each skillSvt
                raw_candidates = []
                for skill_svt in skill_svts:
                    # Create a combined entry with skill data and skillSvt-specific info
                    candidate = dict(skill)  # Copy base skill data
                    candidate.update(skill_svt)  # Override with skillSvt-specific data
                    # Ensure the skill number is preserved
                    candidate['num'] = skill.get('num')
                    raw_candidates.append(candidate)
                
                # Store raw candidates for deferred selection
                skills[skill_num].append({'raw_candidates': raw_candidates})
            else:
                # No skillSvts, treat as legacy single entry
                parsed_skill = self._parse_single_skill(skill, use_max_level=True)
                skills[skill_num].append(parsed_skill)
        
        return skills

    def _select_skill_from_candidates(self, candidate_skills, variant_svt_id):
        """Select a single skill entry from candidates using the same
        strategy as NP selection: filter by releaseConditions, prefer exact
        svtId match, then pick the entry with highest id as tie-breaker.
        """
        if not candidate_skills:
            return None

        # Step 1: Filter by release conditions
        available = []
        for s in candidate_skills:
            release_conditions = s.get('releaseConditions', [])
            if not release_conditions:
                available.append(s)
                continue
            # Group by condGroup
            groups = {}
            for cond in release_conditions:
                grp = self._extract_number(cond.get('condGroup', 0))
                groups.setdefault(grp, []).append(cond)

            cond_met = False
            for group_conds in groups.values():
                group_ok = True
                for cond in group_conds:
                    if not self._check_skill_release_condition(cond):
                        group_ok = False
                        break
                if group_ok:
                    cond_met = True
                    break
            if cond_met:
                available.append(s)

        if not available:
            available = candidate_skills

        # Prefer candidates that explicitly had releaseConditions which were met
        matched_by_release = []
        for s in candidate_skills:
            rc = s.get('releaseConditions', [])
            if not rc:
                continue
            # check if any condGroup in this candidate is satisfied
            groups = {}
            for cond in rc:
                grp = self._extract_number(cond.get('condGroup', 0))
                groups.setdefault(grp, []).append(cond)
            group_ok = False
            for group_conds in groups.values():
                ok = True
                for cond in group_conds:
                    if not self._check_skill_release_condition(cond):
                        ok = False
                        break
                if ok:
                    group_ok = True
                    break
            if group_ok:
                matched_by_release.append(s)

        if matched_by_release:
            available = matched_by_release

        # Step 2: prefer exact svtId match among the available set (use priority/id as tie-breaker)
        if variant_svt_id is not None:
            variant_matches = [s for s in available if self._extract_number(s.get('svtId')) == variant_svt_id]
            if variant_matches:
                return max(variant_matches, key=lambda x: (self._extract_number(x.get('priority', 0)), self._extract_number(x.get('id', 0))))

        # Step 3: pick highest priority then id among available
        return max(available, key=lambda x: (self._extract_number(x.get('priority', 0)), self._extract_number(x.get('id', 0))))

    def _check_skill_release_condition(self, condition):
        """Check a single release condition for skills.

        Mirrors NP._check_release_condition behavior: treat
        'equipWithTargetCostume' as an ascension threshold encoded in condNum.
        Unknown condition types are assumed met to avoid blocking.
        """
        cond_type = condition.get('condType', '')
        cond_num = self._extract_number(condition.get('condNum', 0))
        if cond_type == 'equipWithTargetCostume':
            # Interpret condTargetId and condNum robustly:
            # - condTargetId may be a costume/variant svt id (e.g. 800100)
            # - condNum sometimes encodes ascension as 10 + ascension (e.g. 12 -> ascension 2)
            cond_target = self._extract_number(condition.get('condTargetId', 0))

            # If we don't have a servant context, be conservative and return False
            if not self.servant:
                return False

            # Top-level servant id from data
            try:
                top_id = self._extract_number(getattr(self.servant, 'id', 0))
            except Exception:
                top_id = 0

            variant_id = getattr(self.servant, 'variant_svt_id', None)

            # If condTargetId refers to this servant (top-level or variant), use condNum semantics
            if cond_target:
                if cond_target == top_id or (variant_id is not None and cond_target == variant_id):
                    # If condNum uses 10+ascension encoding, decode it
                    if cond_num > 10:
                        expected_asc = cond_num - 10
                        return self.servant and self.servant.ascension == expected_asc
                    # Otherwise treat condNum as a minimum ascension requirement
                    return self.servant and self.servant.ascension >= cond_num
                # If condTargetId is a costume/variant id different from top-level, require exact variant match
                return self.servant and variant_id is not None and cond_target == variant_id

            # No condTargetId present: fall back to condNum semantics
            if cond_num > 10:
                expected_asc = cond_num - 10
                return self.servant and self.servant.ascension == expected_asc
            return self.servant and self.servant.ascension >= cond_num
        elif cond_type in ('questClear', 'friendshipRank'):
            return True
        else:
            return True
    
    def _parse_legacy_skills(self, skills_data):
        """Parse legacy skills format for backwards compatibility."""
        skills = {1: [], 2: [], 3: []}
        for skill in skills_data:
            parsed_skill = self._parse_single_skill(skill, use_max_level=True)
            skill_num = self._extract_number(skill.get('num', 1))
            skills[skill_num].append(parsed_skill)
        return skills

    def _parse_top_level_skill_svts(self, skill_svts):
        """Parse the top-level skillSvts array (svt-wide list of variant skill entries).

        Groups entries by their `num` field (skill slot) and stores raw
        candidates for deferred selection.
        """
        skills = {1: [], 2: [], 3: []}

        # Group by skill number
        skills_by_num = {}
        for entry in skill_svts:
            num = self._extract_number(entry.get('num', 0))
            if num not in [1, 2, 3]:
                continue
            skills_by_num.setdefault(num, []).append(entry)

        for skill_num in [1, 2, 3]:
            candidates = skills_by_num.get(skill_num, [])
            if not candidates:
                continue
            # Store raw candidates for deferred selection
            # Note: top-level entries are already variant-specific; we keep
            # them as-is so selection logic can filter by svtId/releaseConditions.
            skills[skill_num].append({'raw_candidates': candidates})

        return skills

    def _collect_skill_svts_from_data(self, data):
        """Recursively search servant JSON for any lists named 'skillSvts' and
        aggregate their entries. Returns a flat list of skillSvt entries or []
        if none found.
        """
        found = []

        def visit(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == 'skillSvts' and isinstance(v, list):
                        for e in v:
                            if isinstance(e, dict) and ('svtId' in e or 'num' in e):
                                found.append(e)
                    else:
                        visit(v)
            elif isinstance(obj, list):
                for item in obj:
                    visit(item)

        try:
            visit(data or {})
        except Exception:
            return []

        return found
    
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
            slot_list = self.skills.get(i, [])
            if not slot_list:
                max_cooldowns[i] = 0
                continue

            first = slot_list[0]
            # If deferred raw_candidates stored, select candidate now using
            # the servant's current variant and parse to get cooldown.
            if isinstance(first, dict) and 'raw_candidates' in first:
                raw_candidates = first['raw_candidates']
                selected = self._select_skill_from_candidates(raw_candidates, self.servant.variant_svt_id if self.servant else None)
                if selected:
                    parsed = self._parse_single_skill(selected, use_max_level=True)
                    max_cooldowns[i] = parsed.get('cooldown', 0)
                else:
                    max_cooldowns[i] = 0
            else:
                # legacy parsed skill entry
                try:
                    max_cooldowns[i] = slot_list[-1].get('cooldown', 0)
                except Exception:
                    max_cooldowns[i] = 0

        return max_cooldowns

    def get_skill_by_num(self, num):
        # Dynamic selection for skillSvts format: if we stored raw_candidates,
        # select appropriate candidate using current servant state.
        if 1 <= num < len(self.skills) + 1:
            slot_list = self.skills.get(num, [])
            if slot_list and isinstance(slot_list[0], dict) and 'raw_candidates' in slot_list[0]:
                raw_candidates = slot_list[0]['raw_candidates']
                selected = self._select_skill_from_candidates(raw_candidates, self.servant.variant_svt_id)
                if selected:
                    return self._parse_single_skill(selected, use_max_level=True)
                # fallback to legacy behavior if selection fails
            # Legacy parsed skills path
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
