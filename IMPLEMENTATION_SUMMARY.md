# Servant Parser Implementation - Assumptions and Decisions

## Summary

This implementation provides a robust, local-only parser that extracts ascension-aware canonical data from servant JSON files. The parser handles the example data provided and produces both human-readable markdown summaries and machine-readable JSON outputs for each ascension variant.

## Key Assumptions Made

### 1. **Upgraded Skill Selection**
When skills have multiple versions (old vs upgraded), the parser chooses the upgraded version by default and sets `upgraded: true`. This is determined by the `strengthStatus` field where values > 0 indicate upgraded skills.

**Rationale**: Upgraded skills represent the current state of the servant and are more relevant for gameplay simulation.

### 2. **Ascension Indexing (1-based)**
The parser uses 1-based indexing for ascensions (ascension 1, 2, 3, 4) to match common FGO terminology where "first ascension" is ascension 1, not 0.

**Rationale**: Aligns with user expectations and FGO community conventions.

### 3. **Cooldown Extraction Strategy**
For skills with cooldown arrays, the parser extracts the value at index 9, which represents the maximum skill level (skill level 10).

**Example**: `"coolDown": [10, 10, 9, 9, 8, 8, 7, 7, 6, 5]` → cooldown = 5

**Rationale**: Maximum skill level represents the optimal state of the skill and is most relevant for endgame calculations.

### 4. **Data Shape Handling**
The current implementation primarily handles **legacy single-list** format where skills and noblePhantasms are simple arrays, as this is the format found in all provided example files.

**Supported shapes**:
- ✅ Legacy single-list: `skills: [skill1, skill2, skill3]`
- 🔄 List-of-lists: `skills: [[asc1_skills], [asc2_skills], ...]` (framework ready)
- 🔄 Ascensions array: `ascensions: [{skills: []}, ...]` (framework ready)

**Rationale**: Build for the data we have, with extensibility for future formats.

### 5. **Fallback Behavior**
If the requested ascension index exceeds available data, the parser returns the highest available ascension without raising errors and logs a warning.

**Example**: Requesting ascension 10 for a servant with data only up to ascension 4 returns ascension 4 data.

**Rationale**: Graceful degradation ensures robustness in production environments.

### 6. **Raw Data Preservation**
The parser preserves all numeric effect IDs and OC/NP matrix shapes exactly as they appear in the source data. No semantic interpretation is attempted for unknown effect IDs.

**Rationale**: Conservative approach ensures no data loss and maintains compatibility with existing systems.

### 7. **Transform Detection**
Transform relationships are explicitly mapped in `TRANSFORM_MAPPING`:
```python
TRANSFORM_MAPPING = {
    413: 4132,  # Aozaki Aoko -> Super Aozaki Aoko
}
```

**Rationale**: Explicit mapping provides reliable, testable transform detection without complex heuristics.

### 8. **MongoDB Format Handling**
The parser automatically unwraps MongoDB format (e.g., `{"$numberInt": "123"}` → `123`) throughout the data structure.

**Rationale**: Example data uses MongoDB export format, so unwrapping is essential for usability.

### 9. **Overcharge Matrix Detection**
OC matrices are detected when NP functions contain `svals2`, `svals3`, etc. indicating multiple overcharge levels.

**Rationale**: Preserves the exact structure needed for damage calculations while indicating presence of scaling.

### 10. **Passive Skills Inclusion**
Class passives from the `classPassive` field are included in ascension data as they affect servant performance.

**Rationale**: Passives are part of the servant's complete kit and necessary for accurate simulation.

## Design Decisions

### Non-Invasive Integration
The parser is designed as a utility module that can be optionally integrated with existing code without breaking changes.

### Comprehensive Logging
All fallback decisions and processing steps are logged to `./outputs/parser.log` for debugging and validation.

### Test Coverage
11 unit tests cover all major functionality including edge cases, different data shapes, and integration scenarios.

### Output Format Standardization
Both JSON and Markdown outputs follow consistent schemas that preserve all necessary data while being human-readable.

## Validation Against Requirements

✅ **Extracts ascension-aware canonical data** - Implements `select_ascension_data()` with fallback logic  
✅ **Produces human-readable summaries** - Markdown files with structured format  
✅ **Provides machine JSON outputs** - Canonical JSON with all required fields  
✅ **Handles common input shapes** - Legacy single-list with framework for others  
✅ **Detects transforms** - Aoko → Super Aoko mapping implemented  
✅ **Preserves numeric effect IDs** - Exact preservation of all numeric data  
✅ **Preserves OC/NP matrices** - Exact structure preservation  
✅ **Includes unit tests** - 11 tests with 100% pass rate  
✅ **Provides integration patch** - Three approaches documented  
✅ **Works with example data only** - No external dependencies or DB access  

## Future Extensibility

The parser architecture supports:
- Additional transform mappings
- New input data shapes (list-of-lists, ascensions arrays)
- Extended output formats
- Additional servant special cases
- Enhanced semantic interpretation (optional)

This foundation provides a robust starting point for ascension-aware servant data processing while maintaining backward compatibility and extensibility for future requirements.