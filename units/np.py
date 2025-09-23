# Enhanced NP effect parser for FGO Noble Phantasms
# Provides normalized effect schema with OC/NP level matrix handling
# for the full diversity of NP effects from FGOCombatSim MongoDB servants collection.
#
# Extends the normalized effect schema for NP-specific features:
# - OC level variations (svals2, svals3, svals4, svals5)
# - NP level scaling (1-5)
# - Special NP damage calculation functions

class NP:
    def __init__(self, nps_data, servant=None):
        """
        Initialize NP with variant-aware selection.
        
        Args:
            nps_data: NP data from servant JSON (could be legacy or npSvts)
            servant: Servant instance (provides variant_svt_id for selection)
        """
        self.servant = servant
        self.nps = self.parse_noble_phantasms(nps_data)
        self.card = self.nps[-1]['card'] if self.nps else None  # Default to the highest ID NP

    def parse_noble_phantasms(self, nps_data):
        """
        Parse NPs with variant-aware selection.
        
        For npSvts format:
        1. Prefer npSvts matching variant_svt_id
        2. Use imageIndex mapping as fallback
        3. Use highest priority as final fallback
        4. When reading arrays, use last elements (most potent/upgraded)
        
        For legacy format: use as-is for backwards compatibility
        """
        if not nps_data:
            return []

        # Check if this is npSvts format or legacy
        if isinstance(nps_data, list) and len(nps_data) > 0:
            first_np = nps_data[0]
            is_np_svts = 'svtId' in first_np
            
            if is_np_svts and self.servant:
                # Use variant-aware selection for npSvts
                selected_nps = self._select_variant_nps(nps_data)
            else:
                # Use legacy parsing
                selected_nps = nps_data
        else:
            selected_nps = nps_data if isinstance(nps_data, list) else []

        # Sort NPs by their original ID to ensure the highest ID is last
        sorted_nps = sorted(selected_nps, key=lambda np: self._extract_number(np.get('id', 0)))

        # Assign new IDs from 1 to the highest upgrade
        for i, np in enumerate(sorted_nps):
            np['new_id'] = i + 1

        return sorted_nps
    
    def _extract_number(self, value):
        """Extract number handling MongoDB format."""
        if isinstance(value, dict) and '$numberInt' in value:
            return int(value['$numberInt'])
        return int(value) if value is not None else 0
    
    def _select_variant_nps(self, np_svts):
        """
        Select appropriate NP entries based on variant.
        
        Selection priority:
        1. npSvts with svtId == variant_svt_id
        2. npSvts with matching imageIndex
        3. npSvts with highest priority
        4. All npSvts (fallback)
        """
        variant_svt_id = self.servant.variant_svt_id
        
        # Step 1: Try exact svtId match
        variant_matches = [np for np in np_svts if self._extract_number(np.get('svtId')) == variant_svt_id]
        if variant_matches:
            return variant_matches
        
        # Step 2: Try imageIndex mapping (ascension-based)
        # Ascension 1-4 typically maps to imageIndex 0-3
        expected_image_index = self.servant.ascension - 1
        image_matches = [np for np in np_svts if self._extract_number(np.get('imageIndex')) == expected_image_index]
        if image_matches:
            return image_matches
        
        # Step 3: Use highest priority
        if np_svts:
            max_priority = max(self._extract_number(np.get('priority', 0)) for np in np_svts)
            priority_matches = [np for np in np_svts if self._extract_number(np.get('priority', 0)) == max_priority]
            if priority_matches:
                return priority_matches
        
        # Step 4: Fallback to all
        return np_svts

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
            # Parse into normalized effect schema
            normalized_effect = self._parse_np_function_to_effect(
                func, 
                np_level=np_level,
                overcharge_level=overcharge_level,
                variant_id=np.get('id')
            )
            result.append(normalized_effect)
            
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
    
    def _parse_np_function_to_effect(self, function, np_level=1, overcharge_level=1, variant_id=None):
        """Parse NP function into normalized effect schema."""
        # Handle svals variations for different overcharge levels
        svals_base_key = 'svals'
        svals_oc_key = f'svals{overcharge_level}' if overcharge_level > 1 else 'svals'
        
        base_svals = function.get(svals_base_key, [])
        oc_svals = function.get(svals_oc_key, [])
        
        # Use last element in arrays for most upgraded
        if base_svals and np_level <= len(base_svals):
            base_value = [base_svals[np_level - 1]]
        elif base_svals:
            base_value = [base_svals[-1]]
        else:
            base_value = []
        
        svals_data = {"base": base_value, "oc": {}}
        
        # Handle overcharge variations
        for oc_level in [2, 3, 4, 5]:
            oc_key = f'svals{oc_level}'
            if oc_key in function:
                oc_array = function[oc_key]
                if oc_array and np_level <= len(oc_array):
                    svals_data["oc"][oc_level] = [oc_array[np_level - 1]]
                elif oc_array:
                    svals_data["oc"][oc_level] = [oc_array[-1]]
        
        normalized_effect = {
            "source": "np",
            "slot": None,
            "variant_id": variant_id,
            "funcType": function.get('funcType', 'unknown'),
            "targetType": function.get('funcTargetType', 'unknown'),
            "parameters": {
                "np_level": np_level,
                "overcharge_level": overcharge_level
            },
            "svals": svals_data,
            "buffs": [],
            "raw": function
        }
        
        return normalized_effect
        
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
