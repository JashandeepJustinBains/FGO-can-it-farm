# Integration Patch for Servant.py

This patch shows how to integrate the servant parser with the existing Servant class.

## Option 1: Add parser as a utility method (minimal integration)

Add this import at the top of units/Servant.py:

```python
# Add after existing imports
from utils.servant_parser import select_ascension_data, extract_skill_summary, extract_np_summary
```

Add this method to the Servant class:

```python
def get_canonical_data(self, ascension=None):
    """
    Get canonical ascension-aware data using the servant parser.
    
    Args:
        ascension: Desired ascension level (1-based). If None, uses current ascension.
        
    Returns:
        Canonical servant data with ascension-specific skills/NPs
    """
    target_ascension = ascension if ascension is not None else getattr(self, 'ascension', 1)
    
    # Use the parser to get canonical data
    canonical_data = select_ascension_data(self.data, target_ascension)
    
    return canonical_data

def get_ascension_skills(self, ascension=1):
    """
    Get skills for specific ascension using the parser.
    
    Args:
        ascension: Desired ascension level (1-based)
        
    Returns:
        List of canonical skill descriptors
    """
    canonical_data = self.get_canonical_data(ascension)
    return canonical_data['ascensions'][0]['skills']

def get_ascension_nps(self, ascension=1):
    """
    Get noble phantasms for specific ascension using the parser.
    
    Args:
        ascension: Desired ascension level (1-based)
        
    Returns:
        List of canonical NP descriptors
    """
    canonical_data = self.get_canonical_data(ascension)
    return canonical_data['ascensions'][0]['noblePhantasms']
```

## Option 2: Enhanced initialization with parser integration

Modify the __init__ method to optionally use the parser:

```python
def __init__(self, collectionNo, np=1, ascension=1, lvl=0, initialCharge=0, attack=0, 
             atkUp=0, artsUp=0, quickUp=0, busterUp=0, npUp=0, damageUp=0, 
             busterDamageUp=0, quickDamageUp=0, artsDamageUp=0, append_5=False,
             use_parser=False):  # NEW: option to use parser
    
    self.id = collectionNo
    self.data = select_character(collectionNo)
    
    # NEW: Option to use parser for ascension-aware data
    if use_parser and self.data:
        try:
            self.canonical_data = select_ascension_data(self.data, ascension)
            logging.info(f"Using parser for servant {collectionNo} ascension {ascension}")
        except Exception as e:
            logging.warning(f"Parser failed for servant {collectionNo}: {e}")
            self.canonical_data = None
    else:
        self.canonical_data = None
    
    # ... rest of existing initialization code ...
```

## Option 3: Factory method for parser-based servants

Add this class method:

```python
@classmethod
def from_parsed_data(cls, collectionNo, ascension=1, **kwargs):
    """
    Create a Servant instance using the servant parser for ascension-aware data.
    
    Args:
        collectionNo: Servant collection number
        ascension: Desired ascension level (1-based)
        **kwargs: Additional arguments for Servant constructor
        
    Returns:
        Servant instance with parser-enhanced data
    """
    # Create instance with parser enabled
    servant = cls(collectionNo, ascension=ascension, use_parser=True, **kwargs)
    
    # If parser succeeded, validate the data
    if servant.canonical_data:
        ascension_data = servant.canonical_data['ascensions'][0]
        
        # Log parser results for debugging
        logging.info(f"Parser found {len(ascension_data['skills'])} skills for {collectionNo} asc {ascension}")
        logging.info(f"Parser found {len(ascension_data['noblePhantasms'])} NPs for {collectionNo} asc {ascension}")
        
        # Check for transforms
        if 'transforms' in servant.canonical_data:
            for transform in servant.canonical_data['transforms']:
                logging.info(f"Transform detected: {transform['description']}")
    
    return servant
```

## Usage Examples

```python
# Example 1: Get canonical data for current servant
servant = Servant(413)  # Aozaki Aoko
canonical = servant.get_canonical_data(ascension=3)
print(f"Aoko ascension 3 has {len(canonical['ascensions'][0]['skills'])} skills")

# Example 2: Create servant with parser integration
aoko = Servant.from_parsed_data(413, ascension=1)
if aoko.canonical_data and 'transforms' in aoko.canonical_data:
    print("Aoko can transform!")

# Example 3: Get ascension-specific skills
mash = Servant(1)
asc3_skills = mash.get_ascension_skills(ascension=3)
for skill in asc3_skills:
    upgraded = " (upgraded)" if skill['upgraded'] else ""
    print(f"Skill: {skill['display_name']}{upgraded}, CD: {skill['cooldown']}")
```

## Notes

- The parser integration is designed to be non-invasive and optional
- Existing code will continue to work without changes
- Parser provides additional ascension-aware functionality
- Transform detection is automatically available
- Logging helps debug parser behavior
- The parser preserves all original raw data for compatibility