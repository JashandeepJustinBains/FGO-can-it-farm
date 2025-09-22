# FGO Effect Signature Extractor

This tool extracts and classifies effect signatures from the FGO MongoDB database for integration into the combat simulator.

## Usage

```bash
cd /path/to/FGO-can-it-farm
python tools/extract_effect_signatures.py
```

## Requirements

- Python 3.7+
- pymongo (already in requirements.txt)
- MongoDB read access (temporary credentials embedded)

## Output Files

- `outputs/effect_signatures.json` - Complete signature mappings with samples
- `outputs/effect_signatures.csv` - Human-readable summary table  
- `outputs/extraction_log.txt` - Audit log with queries and counts

## Classifications

The script uses conservative heuristics to classify effects:

- **immediate**: Effects applying when activated (e.g., NP gain, buff application)
- **on-hit**: Effects triggered on attack/hit (Count + TriggeredFuncPosition=2)
- **end-turn**: Effects at turn end (TriggeredFuncPosition=3)
- **counter**: Limited-use effects (Count without trigger position)
- **unknown**: Ambiguous cases requiring manual review

## Integration Next Steps

1. Review JSON output for accuracy
2. Import high-confidence signatures into `skill_manager.py` trigger registry
3. Implement trigger handlers for new classifications
4. Create unit tests for new effect types
5. Extend heuristics based on domain knowledge

## Safety Features

- Read-only database access
- 30-second socket timeout
- Configurable document limits (5000/collection)
- Comprehensive error handling
- Audit logging for reproducibility