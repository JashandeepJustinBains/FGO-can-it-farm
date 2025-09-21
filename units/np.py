class NP:
    def __init__(self, nps_data):
        self.nps = self.parse_noble_phantasms(nps_data)
        self.card = self.nps[-1]['card'] if self.nps else None  # Default to the highest ID NP

    def parse_noble_phantasms(self, nps_data):
        if not nps_data:
            return []

        # Sort NPs by their original ID to ensure the highest ID is last
        sorted_nps = sorted(nps_data, key=lambda np: np.get('id', 0))

        # Assign new IDs from 1 to the highest upgrade
        for i, np in enumerate(sorted_nps):
            np['new_id'] = i + 1

        return sorted_nps

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
            # Determine the key dynamically
            svals_key = f'svals{overcharge_level}' if overcharge_level > 1 else 'svals'
            
            func_values = func[svals_key][np_level - 1] if svals_key in func else {}

            # Parse buffs with the same value names as parse_skills
            buffs = [
                {
                    'name': buff.get('name'),
                    'functvals': buff.get('functvals', ''),
                    'tvals': buff.get('tvals', []),
                    'svals': buff.get('svals', [None])[9] if len(buff.get('svals', [])) > 9 else None,
                    'value': buff.get('svals', [{}])[9].get('Value', 0) if len(buff.get('svals', [])) > 9 else 0,
                    'turns': buff.get('svals', [{}])[9].get('Turn', 0) if len(buff.get('svals', [])) > 9 else 0
                }
                for buff in func.get('buffs', [])
            ]
            
            result.append(
                {
                    'funcType': func['funcType'],
                    'funcTargetType': func['funcTargetType'],
                    'functvals': func.get('functvals', []),
                    'fieldReq': func.get('fieldReq', []),
                    'condTarget': func.get('condTarget', []),
                    'svals': func_values,
                    'buffs': buffs
                }
            )
        
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

        return 0, None, None, None, None  # Default values if no matching funcType is found




    def get_npgain(self, card_type, new_id=None):
        np = self.get_np_by_id(new_id)
        np_gain = np.get('npGain', {}).get(card_type, [0])[0]  # Safely get npgain and divide by 100
        return np_gain / 100


    def get_npdist(self, new_id=None):
        np = self.get_np_by_id(new_id)
        return np.get('npDistribution', [])  # Safely get npDistribution as a list
    
    def __repr__(self):
        return self._format_nps_repr()
    
    def _format_nps_repr(self):
        """Format NPs into human-readable representation showing OC/NP level matrices."""
        if not self.nps:
            return "NP(no noble phantasms available)"
        
        lines = ["Noble Phantasms:"]
        
        for i, np in enumerate(self.nps):
            np_name = np.get('name', 'Unknown NP')
            np_id = np.get('id', 'unknown')
            new_id = np.get('new_id', i + 1)
            card_type = np.get('card', 'unknown')
            
            lines.append(f"  NP ver {new_id} (original ID: {np_id}): {np_name} ({card_type})")
            
            # Show OC matrix information
            lines.append(f"    OC matrix: preserved (functions: {len(np.get('functions', []))})")
            
            # Show NP level effects indication
            sample_func = next((f for f in np.get('functions', []) if f.get('svals')), None)
            if sample_func and sample_func.get('svals'):
                np_levels_available = len(sample_func['svals'])
                lines.append(f"    NP-level effects: preserved raw keys (levels 1-{np_levels_available})")
            else:
                lines.append(f"    NP-level effects: preserved raw keys")
            
            # Show overcharge variations
            oc_keys = [key for key in np.get('functions', [{}])[0].keys() if key.startswith('svals') and key != 'svals']
            if oc_keys:
                oc_levels = sorted([int(key.replace('svals', '')) for key in oc_keys if key.replace('svals', '').isdigit()])
                if oc_levels:
                    lines.append(f"    OC variations: levels {', '.join(map(str, oc_levels))}")
        
        # Show current default
        if self.nps:
            default_np = self.nps[-1]
            lines.append(f"  Default card type: {self.card}")
            lines.append(f"  Default NP: ver {default_np.get('new_id', len(self.nps))}")
        
        return "\n".join(lines)
