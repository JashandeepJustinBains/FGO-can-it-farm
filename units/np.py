"""Minimal legacy-only NP helper (single implementation).

This module intentionally contains one compact NP helper that exposes the
legacy-compatible API. All variant-aware and duplicate code was removed to
keep the minimal branch focused on API-driven behavior.
"""

from typing import List, Dict, Any


class NP:
    def __init__(self, nps_data: List[Dict[str, Any]], servant=None):
        self.servant = servant
        self.nps = nps_data or []
        self.card = self.nps[0].get('card') if self.nps else None

    def _get_np_entry(self, new_id=None):
        if not self.nps:
            raise ValueError('No noblePhantasms available')
        if new_id is None:
            return self.nps[-1]
        idx = int(new_id) - 1
        if 0 <= idx < len(self.nps):
            return self.nps[idx]
        raise ValueError(f'NP id {new_id} not found')

    def get_np_values(self, np_level=1, overcharge_level=1, new_id=None):
        np_entry = self._get_np_entry(new_id)
        funcs = np_entry.get('functions', [])
        result = []
        for func in funcs:
            result.append(func)
            svals_key = f'svals{overcharge_level}' if overcharge_level > 1 else 'svals'
            svals_array = func.get(svals_key, func.get('svals', []))
            if svals_array and isinstance(svals_array, list):
                try:
                    svals_value = svals_array[np_level - 1]
                except Exception:
                    svals_value = svals_array[-1]
            else:
                svals_value = {}

            legacy = {
                'funcType': func.get('funcType'),
                'funcTargetType': func.get('funcTargetType'),
                'functvals': func.get('functvals', []),
                'fieldReq': func.get('fieldReq', []),
                'condTarget': func.get('condTarget', []),
                'svals': svals_value,
                'buffs': func.get('buffs', [])
            }
            result.append(legacy)
        return result

    def get_np_damage_values(self, oc=1, np_level=1, new_id=None):
        np_entry = self._get_np_entry(new_id)
        for func in np_entry.get('functions', []):
            ftype = func.get('funcType')
            svals = func.get('svals', [])
            try:
                val = svals[np_level - 1].get('Value', 0) if isinstance(svals, list) and svals else 0
            except Exception:
                val = 0
            if ftype in ('damageNp', 'damageNpPierce'):
                return val / 1000, None, None, None, None
            if ftype in ('damageNpIndividual', 'damageNpStateIndividualFix'):
                target = svals[np_level - 1].get('Target', 0) if isinstance(svals, list) and svals else 0
                corr = svals[np_level - 1].get('Correction', 0) if isinstance(svals, list) and svals else 0
                return val / 1000, None, corr / 1000 if corr else None, None, target
            if ftype == 'damageNpIndividualSum':
                init = svals[np_level - 1].get('Value2', 0) if isinstance(svals, list) and svals else 0
                corr = svals[np_level - 1].get('Correction', 0) if isinstance(svals, list) and svals else 0
                target = svals[np_level - 1].get('Target', 0) if isinstance(svals, list) and svals else 0
                ids = svals[np_level - 1].get('TargetList', []) if isinstance(svals, list) and svals else []
                return val / 1000, init / 1000 if init else None, corr / 1000 if corr else None, ids, target
        return 0, None, None, None, None

    def get_npgain(self, card_type, new_id=None):
        np_entry = self._get_np_entry(new_id)
        ng = np_entry.get('npGain', {})
        v = ng.get(card_type, []) if isinstance(ng, dict) else []
        try:
            return (v[0] / 100) if v else 0
        except Exception:
            return 0

    def get_npdist(self, new_id=None):
        np_entry = self._get_np_entry(new_id)
        return np_entry.get('npDistribution', [100])

"""Legacy-only NP helper.

This file intentionally keeps NP parsing minimal: it accepts legacy
`noblePhantasms` arrays and exposes the small set of methods consumers use:
- get_np_values(np_level, overcharge_level)
- get_np_damage_values(oc, np_level)
- get_npgain(card_type)
- get_npdist()

The complex variant-aware `npSvts` parsing was removed to start from a clean
slate on the `minimal` branch.
"""

from typing import List, Dict, Any


class NP:
    def __init__(self, nps_data: List[Dict[str, Any]], servant=None):
        # Expect legacy format: a list of NP dicts. Keep as-is.
        self.servant = servant
        self.nps = nps_data or []
        # default card type is taken from the first NP entry when present
        self.card = self.nps[0].get('card') if self.nps else None

    def _get_np_entry(self, new_id=None):
        if not self.nps:
            raise ValueError('No noblePhantasms available')
        # legacy: new_id None -> last element (most upgraded) or first
        if new_id is None:
            return self.nps[-1]
        # new_id corresponds to index+1 in legacy code; support that mapping
        idx = int(new_id) - 1
        if 0 <= idx < len(self.nps):
            return self.nps[idx]
        raise ValueError(f'NP id {new_id} not found')

    def get_np_values(self, np_level=1, overcharge_level=1, new_id=None):
        np_entry = self._get_np_entry(new_id)
        # In legacy format, functions is the list of effect dicts
        funcs = np_entry.get('functions', [])
        # Build a conservative legacy-style list: return the raw functions and a
        # simplified legacy dict per function for compatibility
        result = []
        for func in funcs:
            result.append(func)
            # add legacy-compatible dict
            svals_key = f'svals{overcharge_level}' if overcharge_level > 1 else 'svals'
            svals_array = func.get(svals_key, func.get('svals', []))
            # pick appropriate svals element
            if svals_array and isinstance(svals_array, list):
                try:
                    svals_value = svals_array[np_level - 1]
                except Exception:
                    svals_value = svals_array[-1]
            else:
                svals_value = {}

            legacy = {
                'funcType': func.get('funcType'),
                'funcTargetType': func.get('funcTargetType'),
                'functvals': func.get('functvals', []),
                'fieldReq': func.get('fieldReq', []),
                'condTarget': func.get('condTarget', []),
                'svals': svals_value,
                'buffs': func.get('buffs', [])
            }
            result.append(legacy)
        return result

    def get_np_damage_values(self, oc=1, np_level=1, new_id=None):
        np_entry = self._get_np_entry(new_id)
        for func in np_entry.get('functions', []):
            ftype = func.get('funcType')
            svals = func.get('svals', [])
            try:
                val = svals[np_level - 1].get('Value', 0) if isinstance(svals, list) and svals else 0
            except Exception:
                val = 0
            if ftype in ('damageNp', 'damageNpPierce'):
                return val / 1000, None, None, None, None
            if ftype in ('damageNpIndividual', 'damageNpStateIndividualFix'):
                target = svals[np_level - 1].get('Target', 0) if isinstance(svals, list) and svals else 0
                corr = svals[np_level - 1].get('Correction', 0) if isinstance(svals, list) and svals else 0
                return val / 1000, None, corr / 1000 if corr else None, None, target
            if ftype == 'damageNpIndividualSum':
                init = svals[np_level - 1].get('Value2', 0) if isinstance(svals, list) and svals else 0
                corr = svals[np_level - 1].get('Correction', 0) if isinstance(svals, list) and svals else 0
                target = svals[np_level - 1].get('Target', 0) if isinstance(svals, list) and svals else 0
                ids = svals[np_level - 1].get('TargetList', []) if isinstance(svals, list) and svals else []
                return val / 1000, init / 1000 if init else None, corr / 1000 if corr else None, ids, target
        return 0, None, None, None, None

    def get_npgain(self, card_type, new_id=None):
        np_entry = self._get_np_entry(new_id)
        ng = np_entry.get('npGain', {})
        # legacy npGain may be a dict mapping card type -> list
        v = ng.get(card_type, []) if isinstance(ng, dict) else []
        try:
            return (v[0] / 100) if v else 0
        except Exception:
            return 0

    def get_npdist(self, new_id=None):
        np_entry = self._get_np_entry(new_id)
        return np_entry.get('npDistribution', [100])
"""Legacy-only NP helper.

This file intentionally keeps NP parsing minimal: it accepts legacy
`noblePhantasms` arrays and exposes the small set of methods consumers use:
- get_np_values(np_level, overcharge_level)
- get_np_damage_values(oc, np_level)
- get_npgain(card_type)
- get_npdist()

The complex variant-aware `npSvts` parsing was removed to start from a clean
slate on the `minimal` branch.
"""

from typing import List, Dict, Any


class NP:
    def __init__(self, nps_data: List[Dict[str, Any]], servant=None):
        # Expect legacy format: a list of NP dicts. Keep as-is.
        self.servant = servant
        self.nps = nps_data or []
        # default card type is taken from the first NP entry when present
        # TODO should be changed when skill/NP changing to a new NP
        self.card = self.nps[0].get('card') if self.nps else None

    def _get_np_entry(self, new_id=None):
        if not self.nps:
            raise ValueError('No noblePhantasms available')
        # legacy: new_id None -> last element (most upgraded) or first
        if new_id is None:
            return self.nps[-1]
        # new_id corresponds to index+1 in legacy code; support that mapping
        idx = int(new_id) - 1
        if 0 <= idx < len(self.nps):
            return self.nps[idx]
        raise ValueError(f'NP id {new_id} not found')

    def get_np_values(self, np_level=1, overcharge_level=1, new_id=None):
        # unfinished
        return

    def get_np_by_id(self, new_id=None):
        if new_id is None:
            return self.nps[-1]  # Default to the highest ID NP
        for np in self.nps:
            if np['new_id'] == new_id:
                return np
        raise ValueError(f"No NP found with new_id {new_id}")

    def get_np_values(self, np_level=1, overcharge_level=1, new_id=None):
        np = self.get_np_by_id(new_id)
        result = []
        for func in np['functions']:
            # Keep legacy format for backward compatibility
            svals_key = f'svals{overcharge_level}' if overcharge_level > 1 else 'svals'
            svals_array = func.get(svals_key, [])
            
            # Use last element in array for most potent/upgraded version
            if svals_array and np_level <= len(svals_array):
                func_values = svals_array[np_level - 1]
            elif svals_array:
                # Use last available level if requested level exceeds available
                func_values = svals_array[-1]
            else:
                func_values = {}

            # Parse buffs with the same value names as parse_skills
            buffs = []
            for buff in func.get('buffs', []):
                buff_svals = buff.get('svals', [])
                # Use last svals element for most upgraded
                if buff_svals:
                    buff_svals_value = buff_svals[-1]
                else:
                    buff_svals_value = None
                
                parsed_buff = {
                    'name': buff.get('name'),
                    'functvals': buff.get('functvals', ''),
                    'tvals': buff.get('tvals', []),
                    'svals': buff_svals_value,
                    'value': buff_svals_value.get('Value', 0) if buff_svals_value else 0,
                    'turns': buff_svals_value.get('Turn', 0) if buff_svals_value else 0
                }
                buffs.append(parsed_buff)
            
            legacy_result = {
                'funcType': func['funcType'],
                'funcTargetType': func['funcTargetType'],
                'functvals': func.get('functvals', []),
                'fieldReq': func.get('fieldReq', []),
                'condTarget': func.get('condTarget', []),
                'svals': func_values,
                'buffs': buffs
            }
            result.append(legacy_result)

        return result
    

    def get_np_damage_values(self, oc=1, np_level=1, new_id=None):
        np = self.get_np_by_id(new_id)
        np_damage = 0
        np_damage_correction_init = 0
        np_correction = 0
        np_correction_id = []
        np_correction_target = 0

        for func in np['functions']:
            if func['funcType'] in ['damageNp', 'damageNpPierce']:
                if oc == 1:
                    np_damage = func['svals'][np_level - 1].get('Value', 0)
                else:
                    np_damage = func[f'svals{oc}'][np_level - 1].get('Value', 0)
                return np_damage / 1000, None, None, None, None
            elif func['funcType'] in ['damageNpIndividual', 'damageNpStateIndividualFix']:
                np_damage = func['svals'][np_level - 1].get('Value', 0)
                np_correction_target = func['svals'][np_level - 1].get('Target', 0)
                np_correction = func['svals'][np_level - 1].get('Correction', 0)
                return np_damage / 1000, None, np_correction / 1000, None, np_correction_target
            elif func['funcType'] == 'damageNpIndividualSum':
                np_damage = func['svals'][np_level - 1].get('Value', 0)
                np_damage_correction_init = func['svals'][np_level - 1].get('Value2', 0)
                np_correction = func['svals'][np_level - 1].get('Correction', 0)
                np_correction_target = func['svals'][np_level - 1].get('Target', 0)
                np_correction_id = func['svals'][np_level - 1].get('TargetList', 0)
                return np_damage / 1000, np_damage_correction_init / 1000, np_correction / 1000, np_correction_id, np_correction_target

        # TODO we need to parse for NPs that have different damage functions
        # example 1: romulus quirinus has an NP that counts "ROMAN" traits/buffs applied to enemy. base np damage= 1 + max{2, 0.2x(ROMAN)}
        # example 2: super aoko NP counts "Magic Bullets" on self to increase damage by. base np damage = 1 + 0.?x(Magic Bullets)
        return 0, None, None, None, None  # Default values if no matching funcType is found

    def get_npgain(self, card_type, new_id=None):
        np = self.get_np_by_id(new_id)
        np_gain = np.get('npGain', {}).get(card_type, [0])[0]  # Safely get npgain and divide by 100
        return np_gain / 100

    def get_npdist(self, new_id=None):
        np = self.get_np_by_id(new_id)
        return np.get('npDistribution', [])  # Safely get npDistribution as a list
