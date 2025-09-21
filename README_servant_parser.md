# Servant Parser - Ascension-Aware Data Extraction

## Overview

The servant parser (`utils/servant_parser.py`) extracts ascension-aware canonical data from servant JSON files and produces both human-readable summaries and machine-readable JSON outputs for each ascension variant.

## Features

- **Ascension-aware parsing**: Handles different input shapes (legacy single-list, list-of-lists, ascensions arrays)
- **Transform detection**: Automatically detects servant transforms (e.g., Aoko → Super Aoko)
- **Canonical output**: Standardized JSON format preserving all numeric effect IDs and OC/NP matrices
- **Human-readable summaries**: Markdown files for each ascension
- **Comprehensive coverage**: Skills, Noble Phantasms, passives, stat overrides, and special flags

## Usage

### Command Line

Process all example files:
```bash
python utils/servant_parser.py
```

This creates a `parsed/` directory with outputs like:
- `413-asc1.md` - Human-readable summary for Aoko ascension 1
- `413-asc1.json` - Canonical JSON data for Aoko ascension 1

### Programmatic Usage

```python
from utils.servant_parser import select_ascension_data, extract_skill_summary

# Load servant data
with open('example_servant_data/413-Aozaki Aoko.json') as f:
    servant_data = json.load(f)

# Get ascension 3 data
canonical_data = select_ascension_data(servant_data, 3)

# Access structured data
meta = canonical_data['meta']
skills = canonical_data['ascensions'][0]['skills']
transforms = canonical_data.get('transforms', [])

print(f"{meta['name']} has {len(skills)} skills")
if transforms:
    print(f"Transforms into collection no. {transforms[0]['target_collection_no']}")
```

## Output Format

### JSON Structure

```json
{
  "meta": {
    "collectionNo": 413,
    "name": "Aozaki Aoko",
    "rarity": 5,
    "classId": 25,
    "className": "foreigner",
    "attribute": "human"
  },
  "ascensions": [{
    "ascension_index": 3,
    "skills": [...],
    "noblePhantasms": [...],
    "passives": [...],
    "stat_overrides": {},
    "transforms": [],
    "special_flags": []
  }],
  "global_traits": [...],
  "transforms": [{
    "trigger": "first_np_use",
    "type": "full_transform",
    "target_collection_no": 4132,
    "preserve_cooldowns": true
  }]
}
```

### Skill Descriptor

```json
{
  "id": 2352450,
  "display_name": "Magic Bullet Charging B",
  "cooldown": 2,
  "upgraded": false,
  "raw_effects": [...],
  "original_data": {...}
}
```

### Noble Phantasm Descriptor

```json
{
  "name": "Unfinished Blue",
  "card_type": "arts",
  "hits": [100],
  "effects": [...],
  "scope": "self",
  "se_flags": [],
  "oc_matrix": {
    "svals1": [...],
    "svals2": [...],
    "svals3": [...]
  },
  "raw": {...}
}
```

## Supported Input Shapes

1. **Legacy single-list**: Skills/NPs as simple arrays (most common)
2. **List-of-lists**: Each element is an ascension variant
3. **Ascensions array**: Explicit ascension objects with skills/NPs
4. **Mixed shapes**: Intelligent fallback and detection

## Transform Detection

The parser automatically detects servant transforms:

- **Aozaki Aoko (413) → Super Aozaki Aoko (4132)**
- Future transforms can be added to `TRANSFORM_MAPPING`

Transform information includes:
- Trigger condition (e.g., "first_np_use")
- Transform type ("full_transform" or "partial")
- Target collection number
- Cooldown preservation rules

## Testing

Run the comprehensive test suite:

```bash
python -m pytest tests/test_servant_parser.py -v
```

Tests cover:
- MongoDB format unwrapping
- Legacy single-list parsing
- Skill/NP extraction
- Transform detection
- Markdown generation
- File processing integration

## Assumptions Made

1. **Upgraded skills**: When multiple skill versions exist, the parser chooses the upgraded version by default and sets `upgraded: true`
2. **Ascension indexing**: Uses 1-based indexing (ascension 1-4)
3. **Cooldown extraction**: Uses index 9 from coolDown arrays (max skill level)
4. **Fallback behavior**: If requested ascension > available, returns highest available without raising errors
5. **Raw data preservation**: Always preserves original numeric effect IDs and OC/NP matrix shapes exactly

## Integration with Existing Code

See `servant_integration_patch.md` for detailed integration examples with the existing `Servant.py` class.

## File Structure

```
utils/
├── servant_parser.py          # Main parser module
tests/
├── test_servant_parser.py     # Unit tests
parsed/                        # Generated outputs
├── 1-asc1.md                  # Mash ascension 1 summary
├── 1-asc1.json                # Mash ascension 1 data
├── 413-asc3.md                # Aoko ascension 3 summary
└── ...
outputs/
└── parser.log                 # Parser debug logs
```

## Examples

### Mash Kyrielight (Collection No. 1) - Ascension 3

**Skills:**
- "Shield of Rousing Resolution" — cooldown 6 — ID: 133000 — 4 effects

**Noble Phantasm:**
- Name: "Lord Camelot" — card: arts — hits: 1 — OC scaling — 3 effects

**Class Passives:**
- Magic Resistance D — ID: 11

### Aozaki Aoko (Collection No. 413) - Ascension 3

**Skills:**
- "Magic Bullet Charging B" — cooldown 2 — ID: 2352450 — 5 effects
- "Magic Circuits (Rotation) A" — cooldown 7 — ID: 2354550 — 4 effects

**Noble Phantasm:**
- Name: "Unfinished Blue" — card: arts — hits: 1 — OC scaling — 6 effects

**Transforms:**
- On first NP use: full_transform → collectionNo 4132 (Super Aoko). Keep skill cooldowns as-is.

## Logging

Parser logs are written to `./outputs/parser.log` and include:
- Processing progress for each servant
- Fallback decisions (e.g., using legacy format)
- Transform detection
- Error handling

This provides full traceability for debugging and validation.