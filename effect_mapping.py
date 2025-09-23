"""
Effect mapping module for data-driven NP & skill parsing.

This module provides a canonical effect schema and mapping tables for normalizing
FGO function effects based on the discovery artifact data. It implements handlers
for the most frequent funcTypes to demonstrate the data-driven approach.

Canonical Effect Schema:
{
    "source": "np|skill|passive|transform",
    "slot": int|None,  # skill slot or None for NP
    "variant_id": int|None,  # original id/version if present
    "funcType": str,
    "targetType": str,
    "parameters": dict,  # normalized numeric parameters
    "svals": {
        "base": list,  # base svals indexed by level
        "oc": dict  # overcharge variations by OC level {2: [...], 3: [...], ...}
    },
    "buffs": list,  # normalized buff structures
    "raw": dict  # original raw object for full fidelity
}
"""

from typing import Dict, Any, List, Optional
import json
import os


class EffectMapping:
    """Handles mapping and normalization of FGO function effects."""
    
    def __init__(self, discovery_report_path: Optional[str] = None):
        """Initialize with discovery report data."""
        self.discovery_data = {}
        if discovery_report_path and os.path.exists(discovery_report_path):
            try:
                with open(discovery_report_path, 'r', encoding='utf-8') as f:
                    self.discovery_data = json.load(f)
            except Exception:
                pass  # Fallback to empty data if loading fails
        
        # Initialize mapping handlers for top funcTypes
        self._handlers = {
            'addStateShort': self._handle_add_state_short,
            'servantFriendshipUp': self._handle_servant_friendship_up,
            'addState': self._handle_add_state,
        }
    
    def get_effect_for_func(self, func: Dict[str, Any], source: str = 'np') -> Dict[str, Any]:
        """
        Map a function to canonical effect schema.
        
        Args:
            func: Raw function dictionary
            source: Source type ('np', 'skill', etc.)
            
        Returns:
            Canonical effect dictionary
        """
        func_type = func.get('funcType', 'unknown')
        
        # Use specific handler if available
        if func_type in self._handlers:
            return self._handlers[func_type](func, source)
        
        # Generic fallback for unmapped funcTypes
        return self._generic_handler(func, source)
    
    def _handle_add_state_short(self, func: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Handle addStateShort funcType - temporary buff application."""
        normalized_svals = self._normalize_svals(func)
        parameters = self._extract_parameters_from_svals(normalized_svals)
        
        # Extract buff information
        buffs = []
        for buff in func.get('buffs', []):
            buffs.append(self._normalize_buff(buff))
        
        return {
            "source": source,
            "slot": None,  # Will be set by caller for skills
            "variant_id": None,  # Will be set by caller
            "funcType": "addStateShort",
            "targetType": func.get('funcTargetType', 'unknown'),
            "parameters": parameters,
            "svals": normalized_svals,
            "buffs": buffs,
            "raw": func
        }
    
    def _handle_servant_friendship_up(self, func: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Handle servantFriendshipUp funcType - event-related friendship gain."""
        normalized_svals = self._normalize_svals(func)
        
        # Extract event-specific parameters
        parameters = {}
        if normalized_svals['base']:
            first_sval = normalized_svals['base'][0]
            if isinstance(first_sval, dict):
                parameters['eventId'] = first_sval.get('EventId', 0)
                parameters['rateCount'] = first_sval.get('RateCount', 0)
                parameters['applySupportSvt'] = first_sval.get('ApplySupportSvt', 0)
        
        return {
            "source": source,
            "slot": None,
            "variant_id": None,
            "funcType": "servantFriendshipUp",
            "targetType": func.get('funcTargetType', 'unknown'),
            "parameters": parameters,
            "svals": normalized_svals,
            "buffs": [],  # Friendship effects typically have no buffs
            "raw": func
        }
    
    def _handle_add_state(self, func: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Handle addState funcType - permanent/long-term buff application."""
        normalized_svals = self._normalize_svals(func)
        parameters = self._extract_parameters_from_svals(normalized_svals)
        
        # Extract buff information
        buffs = []
        for buff in func.get('buffs', []):
            buffs.append(self._normalize_buff(buff))
        
        return {
            "source": source,
            "slot": None,
            "variant_id": None,
            "funcType": "addState",
            "targetType": func.get('funcTargetType', 'unknown'),
            "parameters": parameters,
            "svals": normalized_svals,
            "buffs": buffs,
            "raw": func
        }
    
    def _generic_handler(self, func: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Generic handler for unmapped funcTypes."""
        normalized_svals = self._normalize_svals(func)
        parameters = self._extract_parameters_from_svals(normalized_svals)
        
        # Extract basic buff information
        buffs = []
        for buff in func.get('buffs', []):
            buffs.append(self._normalize_buff(buff))
        
        return {
            "source": source,
            "slot": None,
            "variant_id": None,
            "funcType": func.get('funcType', 'unknown'),
            "targetType": func.get('funcTargetType', 'unknown'),
            "parameters": parameters,
            "svals": normalized_svals,
            "buffs": buffs,
            "raw": func
        }
    
    def _normalize_svals(self, func: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize svals structure into base + OC matrix.
        
        Returns:
            {
                "base": [...],  # base svals (level 1-10)
                "oc": {2: [...], 3: [...], ...}  # overcharge variations
            }
        """
        result = {"base": [], "oc": {}}
        
        # Handle base svals
        base_svals = func.get('svals', [])
        if isinstance(base_svals, list):
            result["base"] = base_svals
        
        # Handle overcharge svals (svals2, svals3, svals4, svals5)
        for oc_level in range(2, 6):
            oc_key = f'svals{oc_level}'
            if oc_key in func:
                oc_svals = func[oc_key]
                if isinstance(oc_svals, list):
                    result["oc"][oc_level] = oc_svals
        
        return result
    
    def _extract_parameters_from_svals(self, normalized_svals: Dict[str, Any]) -> Dict[str, Any]:
        """Extract numeric parameters from normalized svals."""
        parameters = {}
        
        # Get parameters from the highest level base svals
        if normalized_svals["base"]:
            last_sval = normalized_svals["base"][-1]  # Highest level
            if isinstance(last_sval, dict):
                # Common parameter patterns
                if 'Value' in last_sval:
                    parameters['value'] = last_sval['Value']
                if 'Turn' in last_sval:
                    parameters['turn'] = last_sval['Turn']
                if 'Count' in last_sval:
                    parameters['count'] = last_sval['Count']
                if 'Rate' in last_sval:
                    parameters['rate'] = last_sval['Rate']
        
        return parameters
    
    def _normalize_buff(self, buff: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize buff structure."""
        return {
            "id": buff.get('id', 0),
            "name": buff.get('name', ''),
            "type": buff.get('type', ''),
            "detail": buff.get('detail', ''),
            "icon": buff.get('icon', ''),
            "maxRate": buff.get('maxRate', 0),
            "vals": buff.get('vals', []),
            "tvals": buff.get('tvals', []),
            "script": buff.get('script', {}),
        }


# Global instance for convenient access
_mapping_instance = None

def get_effect_for_func(func: Dict[str, Any], source: str = 'np') -> Dict[str, Any]:
    """
    Convenience function to map a function to canonical effect schema.
    
    Args:
        func: Raw function dictionary
        source: Source type ('np', 'skill', etc.)
        
    Returns:
        Canonical effect dictionary
    """
    global _mapping_instance
    if _mapping_instance is None:
        # Try to load discovery report from default location
        discovery_path = os.path.join(os.path.dirname(__file__), 'discovery_report.json')
        _mapping_instance = EffectMapping(discovery_path)
    
    return _mapping_instance.get_effect_for_func(func, source)