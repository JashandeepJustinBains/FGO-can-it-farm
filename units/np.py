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

    # def get_np_values(self, np_level=1, overcharge_level=1, new_id=None):
    #     np = self.get_np_by_id(new_id)
    #     result = []
    #     for func in np['functions']:
    #         # print("Debug Func Values: ", func)  # Debug print
    #         if overcharge_level == 1:
    #             svals_key = f'svals'  # Determine the key dynamically
    #         else:
    #             svals_key = f'svals{overcharge_level}'  # Determine the key dynamically
    #         if svals_key in func:
    #             func_values = func[svals_key][np_level - 1]  # Access the correct list element
    #         else:
    #             func_values = {}  # Default to an empty dict if key not found
    #         buffs = [
    #             {
    #                 'name': buff['name'],
    #                 'functvals': buff.get('functvals', ''),
    #                 'tvals': buff['tvals'],
    #                 'svals': buff.get('svals', {}),  # Use .get to avoid KeyError
    #                 'value' = buff.get('svals', {}).get('Value', 0)
    #                 'turns' = buff.get('svals', {}).get('Turn', 0)
    #             }
    #             for buff in func['buffs']
    #         ]
    #         result.append({
    #             'funcId': func['funcId'],
    #             'funcType': func['funcType'],
    #             'funcTargetType': func['funcTargetType'],
    #             'fieldReq': func.get('fieldReq', {}),
    #             'condTarget': func.get('condTarget', {}),
    #             'svals': func_values,
    #             'buffs': buffs
    #         })
    #     return result

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
            elif func['funcType'] == 'damageNpIndividual':
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
        np_gain = np.get('npgain', {}).get(card_type, [0])[0]  # Safely get npgain and divide by 100
        return np_gain / 100


    def get_npdist(self, new_id=None):
        np = self.get_np_by_id(new_id)
        return np.get('npDistribution', [])  # Safely get npDistribution as a list
