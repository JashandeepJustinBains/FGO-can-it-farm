# Implementation Summary

This patch implements ascension-selection helper and enhanced repr methods for FGO servants as requested.

## Changes Made:

### 1. units/Servant.py
- Added `select_ascension_data(servant_json: dict, ascension: int) -> dict` function
- Handles legacy single-list, list-of-lists, and ascensions/forms array formats
- Preserves raw effect IDs and matrices
- Uses logging for non-fatal fallback warnings
- Added commented integration snippet in `Servant.__init__` (non-invasive)
- Added ascension parameter to constructor

### 2. units/skills.py
- Enhanced `Skills.__repr__` for human-readable multi-version skill display
- Shows each skill slot as separate section with variants
- Displays upgrade contexts and chosen versions
- Preserves raw effects indication
- Added helper methods for formatting

### 3. units/np.py
- Added enhanced `NP.__repr__` for human-readable NP description
- Shows OC vs NP level matrix differences
- Displays multiple NP versions compactly
- Indicates preserved raw data structures

### 4. managers/game_manager.py
- Added team-level `__repr__` method
- Shows one line per servant slot with collectionNo, name, ascension
- Displays NP and skills information compactly
- Includes transform notes (e.g., Aoko -> 4132)
- Added helper methods for formatting servant details

### 5. tests/test_servant_ascension_repr.py
- Two pytest tests as required:
  - `test_select_ascension_data_variants`: Tests various input shapes
  - `test_team_repr_contains_core_fields`: Tests repr format patterns
  - `test_select_ascension_data_edge_cases`: Additional edge case testing

## Key Features:
- Fallback handling: When requested ascension > available, uses highest available and logs warning
- Raw data preservation: All effect IDs, svals, and OC matrices preserved
- Non-invasive integration: Commented example in Servant.__init__ shows how to use
- Human-readable output: Enhanced repr methods provide meaningful information
- Comprehensive testing: Covers various data shapes and edge cases

## Testing:
```bash
pytest -q tests/test_servant_ascension_repr.py
```
All tests pass successfully.

## Constraints Met:
- Small, human-reviewable patch (~545 lines added)
- Only modified specified files: Servant.py, skills.py, game_manager.py, np.py
- Added only required test file
- Used logging for warnings (non-fatal)
- Preserved raw numeric effect IDs and matrices
- No external DB/web access required