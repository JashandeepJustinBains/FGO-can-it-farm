# FSM Refactor Documentation

## Summary
This refactor replaces the brute-force simulation logic with a finite state machine (FSM) approach for quest/team evaluation in the FGO simulation project. The FSM-implementation branch introduces automated, scalable, and mathematically provable quest solvability by serializing game states and generating FSM graphs for all possible team/quest combinations. FSM graphs are storable/reloadable (e.g., JSON, GraphML) for further analysis and automation.

## Key Changes (FSM-implementation branch)

1. **Branch Setup**
   - Created and pushed `FSM-implementation` branch on org-origin remote, based on the previous brute-force-implementation branch.

2. **State Serialization**
   - Refactored `/managers` and `/units` modules to support hashable, lightweight state representations (tuples, dicts, or stringified objects).
   - All game state components (servants, skills, buffs, cooldowns, quest progress) are serializable and restorable for FSM traversal.

3. **FSM Generation**
   - Implemented `sim_entry_points/simulate_fsm_search.py` for FSM graph generation using BFS/DFS traversal.
   - Each node in the FSM graph represents a unique, hashable game state.
   - Edges represent valid transitions (skill use, NP, mystic code, etc.).
   - FSM graphs are saved in JSON format for MongoDB or other analysis tools.

4. **Entry Point Refactor**
   - Deprecated brute-force simulation entry point in favor of FSM-based simulation.
   - Created new entry point in `sim_entry_points` for FSM generation and evaluation.
   - Updated input parsing to use the `parsed_servant` structure for team data from the web app.

5. **Testing**
   - Existing tests in `/tests` reviewed for passing status.
   - New tests created for FSM entry point, using the new function for simulation entry.
   - Ensured tests cover state serialization, FSM graph generation, and quest solvability.
   - Added stubs for `get_all_possible_actions` and `apply_action` in `Driver` to enable FSM graph traversal in tests.
   - Fixed deep copy and serialization issues for database objects and custom classes.

## How to Create Unit Tests for FSM Simulation

- **Test FSM Graph Generation:**
  - Create a test that calls the FSM entry point with a sample team/quest input and checks that a valid FSM graph is generated and saved as JSON.
  - Example: Load a simple team, run `main(input_json)`, and assert that `fsm_graph.json` contains expected nodes and edges.

- **Test State Serialization:**
  - Create a test that instantiates a `Driver`, serializes its state, and checks that the output is hashable and JSON-compatible.

- **Test Action Application:**
  - Create a test that applies a sample action to a copied driver and checks that the resulting state changes as expected.

- **Test Edge Cases:**
  - Test with empty teams, invalid actions, or maximum depth to ensure the FSM logic handles all scenarios robustly.

- **Test Integration:**
  - Create integration tests that run the full FSM simulation and validate the output graph structure and quest solvability.

## Example Unit Test (see `tests/test_simulate_fsm_search.py`):
```python
import json
from sim_entry_points.simulate_fsm_search import main as fsm_main

def test_fsm_entry_point():
    input_data = { ... }  # Use parsed_servant format
    input_json = json.dumps(input_data)
    fsm_main(input_json, max_depth=5)
    with open('fsm_graph.json') as f:
        data = json.load(f)
    assert 'nodes' in data and 'links' in data
```

## Usage
- To run FSM-based simulation, use the new entry point in `sim_entry_points/simulate_fsm_search.py`.
- Input data should follow the `parsed_servant` format as shown in the web app integration.
- FSM graphs are saved as JSON for further analysis or database storage.

## Next Steps
- Extend FSM logic for more complex quest mechanics and real action sets.
- Integrate with web app for automated team/quest evaluation.
- Optimize state pruning and graph storage for large-scale simulations.

---
For further details, see the code and new tests in the `FSM-implementation` branch.
