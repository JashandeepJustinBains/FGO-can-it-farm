# FGO Simulation Project: Prompt Crafting

This document is for building the ideal prompt for Claude Opus (or similar LLMs) to assist with the FGO ETL and simulation project. Add or refine sections as needed to maximize clarity and efficiency.

---

## Project Overview

I am performing ETL on Fate Grand Order (FGO) servant data, extracting from JSON files in `example_servant_data/` (each file represents a servant, with some containing variant data). The goal is to transform and upload this data to the `servants` collection in the `FGOCombatSim` database on MongoDB Atlas. The ETL process includes normalizing field names, handling variants, and ensuring compatibility with the target schema.

I also have a simulation program (`sim_entry_points/traverse_api_input.py`) that takes API-like input and simulates FGO game mechanics to predict quest outcomes. This will help users find optimal teams and will be used to populate a database of successful team compositions for quick reference.

---

## Simulation Architecture

- The simulation entry point (`sim_entry_points/traverse_api_input.py`) calls `Driver`, which sets up the simulation environment by generating the necessary managers and instantiating `Servant` and `Enemy` objects.
- The `game_manager` is responsible for parsing skills and Noble Phantasms (NPs), then executing the corresponding code to accurately simulate FGO’s game mechanics and outcomes.
- In-depth knowledge of FGO’s combat, skills, NP effects, buffs/debuffs, and turn order is required for accurate simulation.

---

## Function Types and Descriptions

(Add a table or list here describing each function type, its parameters, and its effect. Example:)

| Function Type | Description | Key Parameters | Notes |
|---------------|-------------|---------------|-------|
| addState      | Applies a buff or debuff to one or more targets. | funcTargetType (e.g., ptAll, ptOne), stateId, value, turns | ptAll = all frontline allies |
| dealDamage    | Deals damage to one or more targets. | funcTargetType, damageValue, npType | Handles NP and normal attacks |
| ...           | ...         | ...           | ...   |

---

## Data Schema and Examples

(Add summaries of the JSON schema, unique types, and representative examples here. Only include what is necessary for the model to reason about or generate code for the project.)

---

## Additional Notes

(Add any special requirements, edge cases, or instructions for the model here.)

---

Continue to add or refine sections as you gather more information or requirements.
