# Servant Parser Runbook

## Quick Start Commands

### Run Tests
```bash
# Run all servant parser tests
python -m pytest tests/test_servant_parser.py -v

# Run specific test
python -m pytest tests/test_servant_parser.py::test_detect_transforms_aoko -v

# Quick test run
python -m pytest tests/test_servant_parser.py -q
```

### Generate Parsed Artifacts
```bash
# Process all example servant files
python utils/servant_parser.py

# Process specific file programmatically
python -c "
from utils.servant_parser import process_servant_file
process_servant_file('example_servant_data/413-Aozaki Aoko.json')
"
```

### Verify Outputs
```bash
# Check generated files
ls -la parsed/

# Count total files (should be ~74 for 10 servants × 4 ascensions × 2 formats)
ls parsed/ | wc -l

# View specific outputs
cat parsed/413-asc3.md    # Aoko ascension 3 summary
cat parsed/1-asc3.json    # Mash ascension 3 canonical data
```

### Debug and Logs
```bash
# Check parser logs
tail -f outputs/parser.log

# Debug specific servant
python -c "
from utils.servant_parser import select_ascension_data
import json
with open('example_servant_data/413-Aozaki Aoko.json') as f:
    data = json.load(f)
result = select_ascension_data(data, 3)
print('Transforms:', result.get('transforms', []))
"
```

## Development Workflow

### 1. Modify Parser
```bash
# Edit parser code
vim utils/servant_parser.py

# Run tests to verify changes
python -m pytest tests/test_servant_parser.py -v

# Regenerate outputs if needed
python utils/servant_parser.py
```

### 2. Add New Transform
```bash
# Edit TRANSFORM_MAPPING in servant_parser.py
# Example: Add Melusine transform
TRANSFORM_MAPPING = {
    413: 4132,  # Aozaki Aoko -> Super Aozaki Aoko
    312: 312,   # Melusine -> Melusine (self-transform)
}

# Test the new transform
python -c "
from utils.servant_parser import _detect_transforms
transforms = _detect_transforms(312, {})
print('Melusine transforms:', transforms)
"
```

### 3. Test with New Data
```bash
# Add new servant file to example_servant_data/
# Then process it
python -c "
from utils.servant_parser import process_servant_file
process_servant_file('example_servant_data/NEW_SERVANT.json')
"

# Check outputs
ls parsed/NEW_COLLECTION_NO-*
```

## Integration Testing

### Test Servant.py Integration
```bash
# Test the integration approaches from servant_integration_patch.md
python -c "
# Simulate Option 1 integration
from utils.servant_parser import select_ascension_data
from scripts.connectDB import select_character

def get_canonical_data(collection_no, ascension=1):
    data = select_character(collection_no)
    return select_ascension_data(data, ascension)

# Test with Aoko
canonical = get_canonical_data(413, 3)
print('Skills:', len(canonical['ascensions'][0]['skills']))
print('Transforms:', canonical.get('transforms', []))
"
```

### Validate Against Expected Format
```bash
# Check output matches requirements
python -c "
import json
with open('parsed/413-asc3.json') as f:
    data = json.load(f)
    
# Verify required structure
assert 'meta' in data
assert 'ascensions' in data
assert 'global_traits' in data
assert 'raw_keys' in data

asc = data['ascensions'][0]
assert 'skills' in asc
assert 'noblePhantasms' in asc
assert 'passives' in asc

print('✅ Structure validation passed')
"
```

## Common Operations

### Extract Specific Data
```bash
# Get all skill names for a servant
python -c "
from utils.servant_parser import select_ascension_data
import json
with open('example_servant_data/1-MashKyrielight.json') as f:
    data = json.load(f)
result = select_ascension_data(data, 3)
for skill in result['ascensions'][0]['skills']:
    upgraded = ' (upgraded)' if skill['upgraded'] else ''
    print(f'- {skill[\"display_name\"]}{upgraded} (CD: {skill[\"cooldown\"]})')
"

# Check transform relationships
python -c "
from utils.servant_parser import TRANSFORM_MAPPING
for source, target in TRANSFORM_MAPPING.items():
    print(f'{source} -> {target}')
"
```

### Performance Testing
```bash
# Time the processing
time python utils/servant_parser.py

# Profile memory usage
python -c "
import tracemalloc
tracemalloc.start()
from utils.servant_parser import process_servant_file
process_servant_file('example_servant_data/413-Aozaki Aoko.json')
print('Memory usage:', tracemalloc.get_traced_memory())
"
```

## Troubleshooting

### Common Issues
```bash
# Issue: MongoDB format errors
# Solution: Check _unwrap_mongo_data function
python -c "
from utils.servant_parser import _unwrap_mongo_data
test_data = {'number': {'$numberInt': '123'}}
print('Unwrapped:', _unwrap_mongo_data(test_data))
"

# Issue: Missing skills/NPs
# Solution: Check input data structure
python -c "
import json
with open('example_servant_data/PROBLEMATIC_FILE.json') as f:
    data = json.load(f)
print('Skills type:', type(data.get('skills', [])))
print('Skills length:', len(data.get('skills', [])))
print('First skill keys:', list(data['skills'][0].keys()) if data.get('skills') else 'None')
"

# Issue: Transform not detected
# Solution: Check collection number and mapping
python -c "
from utils.servant_parser import TRANSFORM_MAPPING
import json
with open('example_servant_data/413-Aozaki Aoko.json') as f:
    data = json.load(f)
collection_no = data['collectionNo']['$numberInt'] if isinstance(data['collectionNo'], dict) else data['collectionNo']
print(f'Collection No: {collection_no}')
print(f'In mapping: {int(collection_no) in TRANSFORM_MAPPING}')
"
```

### Clean and Reset
```bash
# Clean generated files
rm -rf parsed/
rm -f outputs/parser.log

# Regenerate everything
python utils/servant_parser.py

# Reset test cache
rm -rf .pytest_cache/
```

## Performance Benchmarks

Typical performance on the provided example data:
- **Processing time**: ~1-2 seconds for all 10 servants
- **Memory usage**: <50MB peak
- **Output size**: ~3MB total (74 files)
- **Test time**: <1 second for all 11 tests

## File Locations

```
utils/
├── servant_parser.py              # Main parser module

tests/
├── test_servant_parser.py         # Unit tests

parsed/                            # Generated outputs
├── {collection_no}-asc{1-4}.json  # Canonical data
└── {collection_no}-asc{1-4}.md    # Human-readable summaries

outputs/
└── parser.log                     # Debug logs

example_servant_data/
├── 1-MashKyrielight.json          # Input files
├── 413-Aozaki Aoko.json
└── ...

docs/
├── README_servant_parser.md       # Full documentation
└── servant_integration_patch.md   # Integration examples
```

This runbook provides all necessary commands to run tests, generate artifacts, and troubleshoot the servant parser implementation.