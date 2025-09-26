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
            # Try to discover npSvts anywhere in the servant data as a fallback
            if self.servant and getattr(self.servant, 'data', None):
                discovered = self._collect_np_svts_from_data(self.servant.data)
                nps_data = discovered or []
            else:
                return []

        # Check if this is npSvts format or legacy
        if isinstance(nps_data, list) and len(nps_data) > 0:
            first_np = nps_data[0]
            is_np_svts = 'svtId' in first_np

            if is_np_svts and self.servant:
                # Use variant-aware selection for npSvts
                selected_nps = self._select_variant_nps(nps_data)
            else:
                # If caller provided a servant, try to discover npSvts in its data
                if self.servant and not is_np_svts:
                    discovered = self._collect_np_svts_from_data(self.servant.data)
                    if discovered:
                        selected_nps = self._select_variant_nps(discovered)
                    else:
                        selected_nps = nps_data
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
        Select appropriate NP entries based on variant and release conditions.
        
        Selection priority:
        1. Filter by release conditions (ascension/costume requirements)
        2. npSvts with svtId == variant_svt_id
        3. npSvts with matching imageIndex
        4. npSvts with highest priority
        5. All npSvts (fallback)
        """
        variant_svt_id = self.servant.variant_svt_id
        
        # Step 1: Filter by release conditions first
        available_nps = self._filter_by_release_conditions(np_svts)
        
        # Step 2: Try exact svtId match
        variant_matches = [np for np in available_nps if self._extract_number(np.get('svtId')) == variant_svt_id]
        if variant_matches:
            # If multiple entries share the same svtId, prefer the one(s) whose
            # imageIndex matches the current ascension (most common case). If no
            # exact imageIndex is available among them, fall back to priority.
            expected_image_index = self.servant.ascension - 1
            vm_image_matches = [np for np in variant_matches if self._extract_number(np.get('imageIndex')) == expected_image_index]
            if vm_image_matches:
                return vm_image_matches

            # No imageIndex match among variant_matches: pick highest priority
            max_priority = max(self._extract_number(np.get('priority', 0)) for np in variant_matches)
            priority_matches = [np for np in variant_matches if self._extract_number(np.get('priority', 0)) == max_priority]
            return priority_matches

        # Step 3: Try imageIndex mapping across all available entries
        expected_image_index = self.servant.ascension - 1
        image_matches = [np for np in available_nps if self._extract_number(np.get('imageIndex')) == expected_image_index]
        if image_matches:
            return image_matches

        # Step 4: Use highest priority among available NPs
        if available_nps:
            max_priority = max(self._extract_number(np.get('priority', 0)) for np in available_nps)
            priority_matches = [np for np in available_nps if self._extract_number(np.get('priority', 0)) == max_priority]
            if priority_matches:
                return priority_matches

        # Step 5: Fallback to all available NPs
        return available_nps if available_nps else np_svts
    
    def _filter_by_release_conditions(self, np_svts):
        """
        Filter NP entries by release conditions based on current servant state.
        
        Args:
            np_svts: List of NP entries to filter
            
        Returns:
            List of NP entries that meet their release conditions
        """
        if not self.servant:
            return np_svts
            
        available_nps = []
        
        for np in np_svts:
            release_conditions = np.get('releaseConditions', [])

            # If no release conditions, NP is always available
            if not release_conditions:
                available_nps.append(np)
                continue

            # Check if any release condition group is met (OR between groups, AND within group)
            condition_met = False
            condition_groups = {}

            # Group conditions by condGroup
            for condition in release_conditions:
                group = self._extract_number(condition.get('condGroup', 0))
                condition_groups.setdefault(group, []).append(condition)

            # Evaluate groups
            for group_conditions in condition_groups.values():
                group_met = True
                for condition in group_conditions:
                    if not self._check_release_condition(condition):
                        group_met = False
                        break
                if group_met:
                    condition_met = True
                    break

            if condition_met:
                available_nps.append(np)
        
        return available_nps
    
    def _check_release_condition(self, condition):
        """
        Check if a single release condition is met.
        
        Args:
            condition: Dict containing condition details
            
        Returns:
            bool: True if condition is met
        """
        cond_type = condition.get('condType', '')
        cond_num = self._extract_number(condition.get('condNum', 0))

        if cond_type == 'equipWithTargetCostume':
            # Robust handling for equipWithTargetCostume
            # condTargetId may be a costume svt id or missing; condNum sometimes encodes ascension as 10 + ascension
            cond_target = self._extract_number(condition.get('condTargetId', condition.get('condTarget', condition.get('condNum', 0))))

            # If servant context missing, conservatively assume False
            if not self.servant:
                return False

            base_svt_id = getattr(self.servant, 'original_base_svt_id', None) or getattr(self.servant, 'variant_svt_id', None)
            variant_id = getattr(self.servant, 'variant_svt_id', None)
            current_ascension = getattr(self.servant, 'ascension', 1)

            # Decode condNum if using 10+ encoding
            if cond_num > 10:
                required_ascension = cond_num - 10
            else:
                required_ascension = cond_num

            # If cond_target is small (<=10) it may represent an ascension threshold
            if cond_target and cond_target <= 10:
                # prefer explicit ascension check
                return current_ascension >= cond_target or current_ascension >= required_ascension

            # If cond_target matches base id and we're using a costume variant, allow some costume mappings
            if cond_target and base_svt_id and cond_target == base_svt_id and variant_id and variant_id != base_svt_id:
                # Some costume entries expect high condNum values; permit reasonable mappings
                # Accept if current ascension meets required or if variant has explicit matching svtId elsewhere
                if current_ascension >= required_ascension:
                    return True
                # Also allow when variant_id equals base+1 or base+2 as heuristic
                # (many costumes use base_svt_id+1/+2 encoding in example data)
                if variant_id in (base_svt_id + 1, base_svt_id + 2):
                    # accept medium/low ascension requirements for costumes
                    return required_ascension <= 8

            # If cond_target explicitly matches the variant_id, require ascension check
            if cond_target and variant_id and cond_target == variant_id:
                return current_ascension >= required_ascension

            # If no cond_target provided, fallback to ascension-only check
            return current_ascension >= required_ascension
        elif cond_type == 'questClear':
            # Quest completion conditions - assume met for now
            # In a full implementation, this would check quest completion status
            return True
        elif cond_type == 'friendshipRank':
            # Bond level conditions - assume met for now
            # In a full implementation, this would check bond level
            return True
        else:
            # Unknown condition type - assume met to avoid breaking functionality
            return True

    def _collect_np_svts_from_data(self, data):
        """Recursively search servant JSON for any `npSvts` arrays and return a flattened list.

        This ensures we find np entries whether they're top-level or nested in ascensions/forms.
        """
        found = []

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == 'npSvts' and isinstance(v, list):
                        found.extend(v)
                    else:
                        walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    walk(item)

        walk(data)
        return found

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
