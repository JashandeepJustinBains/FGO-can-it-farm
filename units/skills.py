from typing import List, Dict, Any


class Skills:
    @classmethod
    def from_skills_by_priority(cls, skills_by_priority: dict, servant=None, append_5=False, mystic_code=None):
        """
        Construct Skills from skillsByPriority dict, selecting the highest available priority for each slot.
        """
        # Find all priorities (as ints), sort descending
        priorities = sorted([int(p) for p in skills_by_priority.keys()], reverse=True)
        selected_skills = []
        used_slots = set()
        # For each slot 1,2,3
        for slot in [1,2,3]:
            # For each priority, high to low
            for p in priorities:
                slot_dict = skills_by_priority.get(str(p), {})
                skill = slot_dict.get(str(slot))
                if skill:
                    selected_skills.append(skill)
                    used_slots.add(slot)
                    break
        # Now selected_skills is a list of the best skill for each slot (may be <3 if missing)
        return cls(selected_skills, servant=servant, append_5=append_5, mystic_code=mystic_code)

    def __init__(self, skills_data: List[Dict[str, Any]], servant=None, append_5=False, mystic_code=None, skills_by_priority: dict = None):
        self.servant = servant
        self.append_5 = append_5
        self.skills = {1: [], 2: [], 3: []}
        # If skills_by_priority is provided, use the FGO logic
        if skills_by_priority:
            obj = Skills.from_skills_by_priority(skills_by_priority, servant=servant, append_5=append_5, mystic_code=mystic_code)
            self.skills = obj.skills
            self.cooldowns = obj.cooldowns
            self.max_cooldowns = obj.max_cooldowns
            self.cooldown_reduction_applied = obj.cooldown_reduction_applied
            return
        for s in (skills_data or []):
            num = int(s.get('num', 1)) if s.get('num') is not None else 1
            parsed = self._parse_single_skill(s)
            if num in self.skills:
                self.skills[num].append(parsed)

        self.cooldowns = {1: 0, 2: 0, 3: 0}
        self.max_cooldowns = self.initialize_max_cooldowns()
        self.cooldown_reduction_applied = {1: False, 2: False, 3: False}

    def _extract_number(self, value):
        """Extract number handling MongoDB format."""
        if isinstance(value, dict) and '$numberInt' in value:
            return int(value['$numberInt'])
        elif isinstance(value, dict) and '$numberLong' in value:
            return int(value['$numberLong'])
        elif isinstance(value, dict) and '$numberDouble' in value:
            return int(float(value['$numberDouble']))
        elif isinstance(value, (int, float)):
            return int(value)
        elif isinstance(value, str) and value.isdigit():
            return int(value)
        elif value is None:
            return 0
        else:
            # Fallback for other types
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0

    def _parse_single_skill(self, skill: Dict[str, Any]):
        cooldowns = skill.get('coolDown', [])
        cooldown = self._extract_number(cooldowns[-1]) if cooldowns else 0
        return {
            'id': self._extract_number(skill.get('id', 0)),
            'name': skill.get('name'),
            'cooldown': cooldown,
            'functions': skill.get('functions', [])
        }

    def initialize_max_cooldowns(self):
        max_cd = {}
        for i in [1, 2, 3]:
            lst = self.skills.get(i, [])
            max_cd[i] = lst[-1].get('cooldown', 0) if lst else 0
        return max_cd

    def get_skill_by_num(self, num: int):
        if num not in self.skills:
            raise IndexError(f'Skill number {num} out of range')
        lst = self.skills.get(num, [])
        return lst[-1] if lst else None

    def get_skill_names(self):
        return [self.get_skill_by_num(i).get('name') if self.get_skill_by_num(i) else None for i in [1, 2, 3]]

    def get_skill_cooldowns(self):
        return self.cooldowns

    def decrement_cooldowns(self, turns: int):
        for k in self.cooldowns:
            if self.cooldowns[k] > 0:
                self.cooldowns[k] = max(0, self.cooldowns[k] - turns)

    def skill_available(self, skill_num):
        return self.cooldowns.get(skill_num, 0) == 0

    def set_skill_cooldown(self, skill_num):
        if not self.cooldown_reduction_applied.get(skill_num, False) and self.append_5:
            self.cooldowns[skill_num] = max(0, self.max_cooldowns.get(skill_num, 0) - 1)
            self.cooldown_reduction_applied[skill_num] = True
        else:
            self.cooldowns[skill_num] = self.max_cooldowns.get(skill_num, 0)


    def __repr__(self):
        return f"Skills(skills={self.skills}, cooldowns={self.cooldowns})"
