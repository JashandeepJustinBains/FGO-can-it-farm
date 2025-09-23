# Enhanced NP effect parser for FGO Noble Phantasms
# Provides normalized effect schema with OC/NP level matrix handling
# for the full diversity of NP effects from FGOCombatSim MongoDB servants collection.
#
# Extends the normalized effect schema for NP-specific features:
# - OC level variations (svals2, svals3, svals4, svals5)
# - NP level scaling (1-5)
# - Special NP damage calculation functions

# Import effect mapping for data-driven parsing
try:
    from effect_mapping import get_effect_for_func
    _HAS_EFFECT_MAPPING = True
except ImportError:
    _HAS_EFFECT_MAPPING = False

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
            # Use effect mapping for data-driven parsing if available
            if _HAS_EFFECT_MAPPING:
                normalized_effect = get_effect_for_func(func, source='np')
                # Set variant_id and NP-specific parameters
                normalized_effect['variant_id'] = np.get('id')
                normalized_effect['slot'] = None  # NPs don't have slots
            else:
                # Fallback to legacy parsing
                normalized_effect = self._parse_np_function_to_effect(
                    func, 
                    np_level=np_level,
                    overcharge_level=overcharge_level,
                    variant_id=np.get('id')
                )
            
            result.append(normalized_effect)
            
            # Keep legacy format for backward compatibility
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
            
            legacy_result = {
                'funcType': func['funcType'],
                'funcTargetType': func['funcTargetType'],
                'functvals': func.get('functvals', []),
                'fieldReq': func.get('fieldReq', []),
                'condTarget': func.get('condTarget', []),
                'svals': func_values,
                'buffs': buffs
            }
            
            # Add legacy data to normalized effect
            result[-1]['_legacy'] = legacy_result
        
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
        
    def _parse_np_function_to_effect(self, function, np_level=1, overcharge_level=1, variant_id=None):
        """Parse an NP function into normalized effect schema with OC/NP level handling."""
        try:
            # Extract base parameters
            func_type = function.get('funcType', 'unknown')
            target_type = function.get('funcTargetType', 'unknown')
            
            # Normalize svals structure - handle all OC variations
            svals_normalized = self._normalize_np_svals(function)
            
            # Extract numeric parameters for current NP/OC level
            parameters = self._extract_np_parameters(function, svals_normalized, np_level, overcharge_level)
            
            # Parse buffs
            buffs_normalized = []
            for buff in function.get('buffs', []):
                buff_normalized = self._normalize_np_buff(buff)
                buffs_normalized.append(buff_normalized)
            
            # Create normalized effect
            effect = {
                "source": "np",
                "slot": None,
                "variant_id": variant_id,
                "funcType": func_type,
                "targetType": target_type,
                "parameters": parameters,
                "svals": svals_normalized,
                "buffs": buffs_normalized,
                "raw": function
            }
            
            return effect
            
        except Exception as e:
            # Fallback to raw preservation if parsing fails
            return {
                "source": "np",
                "slot": None,
                "variant_id": variant_id,
                "funcType": function.get('funcType', 'unknown'),
                "targetType": function.get('funcTargetType', 'unknown'),
                "parameters": {},
                "svals": {"base": [], "oc": {}},
                "buffs": [],
                "raw": function,
                "_parse_error": str(e)
            }
    
    def _normalize_np_svals(self, function):
        """Normalize NP svals structure with OC level support."""
        normalized = {"base": [], "oc": {}}
        
        # Handle base svals (NP level 1-5)
        base_svals = function.get('svals', [])
        if base_svals:
            normalized["base"] = base_svals
        
        # Handle overcharge variations (svals2-svals5 for OC 2-5)
        for oc_level in range(2, 6):
            oc_key = f'svals{oc_level}'
            if oc_key in function:
                normalized["oc"][oc_level] = function[oc_key]
        
        return normalized
    
    def _extract_np_parameters(self, function, svals_normalized, np_level, overcharge_level):
        """Extract numeric parameters for specific NP/OC level."""
        parameters = {}
        
        # Extract common parameters from functvals
        functvals = function.get('functvals', [])
        if functvals:
            parameters['functvals'] = functvals
        
        # Get appropriate svals based on OC level
        if overcharge_level > 1 and overcharge_level in svals_normalized["oc"]:
            current_svals = svals_normalized["oc"][overcharge_level]
        else:
            current_svals = svals_normalized["base"]
        
        # Extract from current NP level
        if current_svals and np_level <= len(current_svals):
            np_level_svals = current_svals[np_level - 1]
            if isinstance(np_level_svals, dict):
                for key, value in np_level_svals.items():
                    if key in ['Value', 'Value2', 'Turn', 'Correction', 'Target', 'TargetList', 'Count', 'Rate']:
                        parameters[key.lower()] = value
        
        # Add level context
        parameters['np_level'] = np_level
        parameters['overcharge_level'] = overcharge_level
            
        return parameters
    
    def _normalize_np_buff(self, buff):
        """Normalize NP buff structure."""
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
    
    # NP-specific effect interpretation helpers
    def get_np_damage_multiplier(self, np_level=1, overcharge_level=1, new_id=None):
        """Get normalized damage multiplier for NP effects."""
        np_values = self.get_np_values(np_level, overcharge_level, new_id)
        damage_multiplier = 0
        
        for effect in np_values:
            func_type = effect.get('funcType', '').lower()
            if 'damage' in func_type:
                svals = effect.get('svals', {})
                if isinstance(svals, dict) and 'Value' in svals:
                    damage_multiplier = svals['Value'] / 1000
                elif hasattr(effect, '_legacy') and 'svals' in effect['_legacy']:
                    legacy_svals = effect['_legacy']['svals']
                    if isinstance(legacy_svals, dict) and 'Value' in legacy_svals:
                        damage_multiplier = legacy_svals['Value'] / 1000
                break
        
        return damage_multiplier
    
    def get_np_special_damage(self, np_level=1, overcharge_level=1, new_id=None):
        """Get special damage parameters (individual, sum, etc.)."""
        np_values = self.get_np_values(np_level, overcharge_level, new_id)
        special_damage = {}
        
        for effect in np_values:
            func_type = effect.get('funcType', '')
            if func_type in ['damageNpIndividual', 'damageNpStateIndividualFix', 'damageNpIndividualSum']:
                parameters = effect.get('parameters', {})
                special_damage.update(parameters)
                break
        
        return special_damage
