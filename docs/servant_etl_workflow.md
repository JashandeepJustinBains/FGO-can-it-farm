# FGO Servant Data ETL and MongoDB Upload Workflow

## Overview
This document describes the workflow for extracting, transforming, and loading (ETL) Fate/Grand Order servant data from raw JSON files into the MongoDB `servants` collection, ensuring all necessary fields (including `atkGrowth`) are present for accurate simulation.

## Workflow Steps

### 1. Raw Data Source
- Raw servant data is stored as individual JSON files in the `example_servant_data/` directory.
- Each file contains the full data for a servant, including fields like `collectionNo`, `name`, `skills`, `noblePhantasms`, `traits`, and `atkGrowth` (an array of attack values for each level).

### 2. Data Transformation
- The script `scripts/process_all_servants.py` processes each JSON file in `example_servant_data/`.
- It uses the function `create_structured_servant_data` from `scripts/parse_servant_ascensions_corrected.py` to transform the raw data into a structured format suitable for simulation and database storage.
- **Patch Requirement:** Ensure that `atkGrowth` is extracted from the raw JSON and included in the structured output.
- The structured servant data is saved as `<collectionNo>_structured.json` in the `servants/` directory.

### 3. Upload to MongoDB
- The script `scripts/upload_servants_to_mongodb.py` uploads all structured servant JSON files from the `servants/` directory to the MongoDB `servants` collection.
- Each document is upserted (inserted or replaced) based on `collectionNo`.
- After upload, each servant document in MongoDB will contain all required fields, including `atkGrowth`.

## Why `atkGrowth` Matters
- The `atkGrowth` array is essential for calculating a servant's attack at any level (1-120).
- Without this field, simulations cannot accurately reflect user-specified servant levels.

## Summary of Key Scripts
- `scripts/process_all_servants.py`: Processes raw JSONs and creates structured servant data.
- `scripts/parse_servant_ascensions_corrected.py`: Contains the transformation logic (must include `atkGrowth`).
- `scripts/upload_servants_to_mongodb.py`: Uploads structured data to MongoDB.

## Update Procedure
1. **Patch** the transformation logic to include `atkGrowth`.
2. **Re-run** `process_all_servants.py` to regenerate structured servant files.
3. **Run** `upload_servants_to_mongodb.py` to update the MongoDB collection.

---
This ensures all simulation and API logic can access accurate, level-dependent servant stats from the database.
