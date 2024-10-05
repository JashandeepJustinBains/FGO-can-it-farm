class NP:
    def __init__(self, nps_data):
        self.nps = self.parse_noble_phantasms(nps_data)
        self.card = self.nps[0]['card']

    def parse_noble_phantasms(self, nps_data):
        nps = []
        for np in nps_data:
            parsed_np = {
                'id': np.get('id'),
                'name': np.get('name'),
                'card': np.get('card'),
                'npgain': np.get('npGain'),
                'npdist': np.get('npDistribution'),
                'aoe': np.get('effectFlags')[0],
                'functions': self.parse_np_functions(np.get('functions'))
            }
            nps.append(parsed_np)
            # Log the parsing of noble phantasms
            # debug(f"Parsed Noble Phantasm: {parsed_np['name']}")
        return nps

    def parse_np_functions(self, functions_data):
        np_values_list = []
        for func in functions_data:
            func_dict = {
                'funcId': func['funcId'],
                'funcType': func['funcType'],
                'funcTargetType': func['funcTargetType'],
                'fieldReq': func.get('funcquestTvals', {}),
                'condTarget': func.get('functvals', {}),
                'values': {
                    1: {i+1: func['svals'][i] for i in range(5)},
                    2: {i+1: func['svals2'][i] for i in range(5)},
                    3: {i+1: func['svals3'][i] for i in range(5)},
                    4: {i+1: func['svals4'][i] for i in range(5)},
                    5: {i+1: func['svals5'][i] for i in range(5)}
                },
                'buffs': self.parse_np_buffs(func.get('buffs', []), func.get('svals', {}))
            }
            np_values_list.append(func_dict)
            # Log the parsing of NP functions
            # debug(f"Parsed NP function: {func_dict['funcId']}")
        return np_values_list

    def parse_np_buffs(self, buffs_data, svals_data):
        buffs_list = []
        for buff in buffs_data:
            buff_dict = {
                'type': buff['type'],
                'tvals': buff['tvals'],
                'functvals': buff.get('functvals', None),
                'values': buff['vals'],
                'svals': svals_data  # Include svals data
            }
            buffs_list.append(buff_dict)
            # Log the parsing of buffs
            # debug(f"Parsed buff: {buff_dict['type']}")
        return buffs_list    

    def get_np_values(self, np_level=1, overcharge_level=1):
        result = []
        for np in self.nps:
            for func in np['functions']:
                func_values = func['values'].get(overcharge_level, {}).get(np_level, {})
                buffs = [
                    {
                        'type': buff['type'],
                        'tvals': buff['tvals'],
                        'svals': buff['values']
                    }
                    for buff in func['buffs']
                ]
                result.append({
                    'funcId': func['funcId'],
                    'funcType': func['funcType'],
                    'funcTargetType': func['funcTargetType'],
                    'fieldReq': func.get('fieldReq', {}),
                    'condTarget': func.get('condTarget', {}),
                    'svals': func_values,
                    'buffs': buffs
                })
                # Log the retrieval of NP values
                # debug(f"Retrieved NP values for function: {func['funcId']}")
        return result

    def get_np_damage_values(self, oc=1, np_level=1):
        funcs = self.get_np_values(np_level, oc)
        for func in funcs:
            if func['funcType'] == 'damageNp':
                np_damage = func['svals'].get('Value', 0)
                # Log the NP damage calculation
                # info(f"Calculated NP damage: {np_damage / 1000} ")
                return np_damage / 1000, None, None
            if func['funcType'] == 'damageNpIndividual':
                np_damage = func['svals'].get('Value', 0)
                np_correction_target = func['svals'].get('Target', 0)
                np_correction = func['svals'].get('Correction', 0)
                # Log the NP individual damage calculation
                # info(f"Calculated NP SE damage: {np_damage / 1000}, np_correction_init={np_correction/1000} on units with trait={np_correction_target} ")
                return np_damage / 1000, np_correction_target, np_correction / 1000
            if func['funcType'] == 'damageNpIndividualSum':
                np_damage = func['svals'].get('Value', 0)
                np_damage_correction_init = func['svals'].get('Value2', 0)
                np_correction = func['svals'].get('Correction', 0)
                np_correction_target = func['svals'].get('Target', 0)
                np_correction_id = func['svals'].get('TargetList', 0)
                # Log the NP individual sum damage calculation
                # info(f"Calculated NP individual sum damage: {np_damage / 1000}, np_correction_init={np_damage_correction_init/1000}, np_correction increase={np_correction/1000} on units={'enemy' if np_correction_target==0 else 'self'} with trait/buff ID of={np_correction_id} ")
                return np_damage / 1000, np_damage_correction_init/1000, np_correction/1000, np_correction_id, np_correction_target
        return None
