# Traits runtime API for FGO servants
# Handles trait parsing and dynamic updates for ascension/costume changes and mid-combat transformations

class TraitSet:
    """
    Manages a servant's traits with support for runtime modifications.
    
    Supports:
    - Base traits from servant definition
    - Ascension/costume-specific trait additions
    - Dynamic trait changes during combat (transformations)
    - Event-specific trait additions with time constraints
    """
    
    def __init__(self, base_traits=None):
        """
        Initialize trait set with base traits.
        
        Args:
            base_traits: List of trait dicts with 'id' and 'name' fields
        """
        self.base_traits = set()
        self.active_traits = set()
        self.ascension_traits = set()
        self.costume_traits = set()
        self.dynamic_traits = set()  # For mid-combat changes
        
        if base_traits:
            for trait in base_traits:
                trait_id = self._extract_trait_id(trait)
                if trait_id:
                    self.base_traits.add(trait_id)
        
        self._update_active_traits()
    
    def _update_active_traits(self):
        """Recalculate active traits from all sources."""
        self.active_traits = (
            self.base_traits | 
            self.ascension_traits | 
            self.costume_traits | 
            self.dynamic_traits
        )
    
    def _extract_trait_id(self, trait):
        """Extract trait ID handling MongoDB format and regular format."""
        if isinstance(trait, dict):
            trait_id = trait.get('id')
            # Handle MongoDB format with $numberInt
            if isinstance(trait_id, dict) and '$numberInt' in trait_id:
                return int(trait_id['$numberInt'])
            elif isinstance(trait_id, (int, str)):
                return int(trait_id)
        return int(trait) if isinstance(trait, (int, str)) else 0
    
    def apply_ascension_traits(self, ascension_data, ascension_level):
        """
        Apply traits for specific ascension level.
        
        Args:
            ascension_data: ascensionAdd individuality data from servant JSON
            ascension_level: Current ascension level (0-4 typically)
        """
        self.ascension_traits.clear()
        
        if not ascension_data or 'individuality' not in ascension_data:
            self._update_active_traits()
            return
        
        individuality = ascension_data['individuality']
        
        # Apply ascension-specific traits
        ascension_key = str(ascension_level)
        if 'ascension' in individuality and ascension_key in individuality['ascension']:
            for trait in individuality['ascension'][ascension_key]:
                trait_id = self._extract_trait_id(trait)
                if trait_id:
                    self.ascension_traits.add(trait_id)
        
        self._update_active_traits()
    
    def apply_costume_traits(self, ascension_data, costume_svt_id):
        """
        Apply traits for specific costume.
        
        Args:
            ascension_data: ascensionAdd individuality data from servant JSON
            costume_svt_id: Costume svtId (e.g., 304830)
        """
        self.costume_traits.clear()
        
        if not ascension_data or 'individuality' not in ascension_data:
            self._update_active_traits()
            return
        
        individuality = ascension_data['individuality']
        
        # Apply costume-specific traits
        if 'costume' in individuality:
            costume_key = str(costume_svt_id)
            if costume_key in individuality['costume']:
                for trait in individuality['costume'][costume_key]:
                    trait_id = self._extract_trait_id(trait)
                    if trait_id:
                        self.costume_traits.add(trait_id)
        
        self._update_active_traits()
    
    def apply_trait_changes(self, changes):
        """
        Apply dynamic trait changes (mid-combat transformations).
        
        Args:
            changes: Dict with 'add' and/or 'remove' keys containing trait lists
        """
        if 'add' in changes:
            for trait in changes['add']:
                trait_id = self._extract_trait_id(trait)
                if trait_id:
                    self.dynamic_traits.add(trait_id)
        
        if 'remove' in changes:
            for trait in changes['remove']:
                trait_id = self._extract_trait_id(trait)
                if trait_id:
                    self.dynamic_traits.discard(trait_id)
        
        self._update_active_traits()
    
    def remove_dynamic_traits(self, trait_ids):
        """Remove specific dynamic traits."""
        for trait_id in trait_ids:
            self.dynamic_traits.discard(trait_id)
        self._update_active_traits()
    
    def contains(self, trait_id):
        """Check if trait is currently active."""
        return trait_id in self.active_traits
    
    def get_traits(self):
        """Get all currently active trait IDs."""
        return self.active_traits.copy()
    
    def get_trait_breakdown(self):
        """Get traits organized by source for debugging."""
        return {
            'base': self.base_traits.copy(),
            'ascension': self.ascension_traits.copy(),
            'costume': self.costume_traits.copy(),
            'dynamic': self.dynamic_traits.copy(),
            'active': self.active_traits.copy()
        }


def parse_trait_add_data(trait_add_list):
    """
    Parse traitAdd data for event-specific or conditional traits.
    
    Args:
        trait_add_list: List of traitAdd entries from servant JSON
        
    Returns:
        Dict of parsed trait addition rules
    """
    parsed_rules = []
    
    for entry in trait_add_list:
        rule = {
            'idx': entry.get('idx'),
            'traits': [trait.get('id') for trait in entry.get('trait', [])],
            'limit_count': entry.get('limitCount', -1),
            'cond_type': entry.get('condType', 'none'),
            'cond_id': entry.get('condId', 0),
            'cond_num': entry.get('condNum', 0),
            'event_id': entry.get('eventId', 0),
            'started_at': entry.get('startedAt', 0),
            'ended_at': entry.get('endedAt', 0)
        }
        parsed_rules.append(rule)
    
    return parsed_rules


def get_applicable_trait_adds(trait_add_rules, current_ascension=None, current_time=None):
    """
    Filter trait addition rules based on current conditions.
    
    Args:
        trait_add_rules: Parsed traitAdd rules
        current_ascension: Current ascension level for filtering
        current_time: Current timestamp for event filtering
        
    Returns:
        List of trait IDs that should be added
    """
    applicable_traits = set()
    
    for rule in trait_add_rules:
        # Check ascension/limit requirements
        if rule['limit_count'] != -1:
            if current_ascension is not None and current_ascension != rule['limit_count']:
                continue
        
        # Check time constraints for events
        if rule['event_id'] != 0 and current_time is not None:
            if current_time < rule['started_at'] or current_time > rule['ended_at']:
                continue
        
        # Add applicable traits
        applicable_traits.update(rule['traits'])
    
    return list(applicable_traits)