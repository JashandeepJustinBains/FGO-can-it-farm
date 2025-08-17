# Heuristic Simulation Logic Documentation

## Summary of `simulate_heuristic_search.py`

This module implements a brute-force and heuristic search approach for evaluating FGO team/quest permutations. It generates all possible action token permutations for a given team and quest, evaluates each permutation, and uses simulated annealing to find the best-performing sequence. The results are saved to a JSON file for later analysis.

### Key Components

- **MongoDB Integration:**
  - Loads environment variables and connects to a MongoDB database to fetch servant and quest data.

- **Token Generation:**
  - `generate_tokens_for_positions(driver)`: Generates all possible skill, NP, and mystic code tokens for the current team.
  - `generate_tokens_for_skill` and `generate_tokens_for_mystic_code`: Helper functions to create tokens for each skill and mystic code, including target and swap options.

- **Permutation Generation:**
  - `generate_random_permutations(tokens, num_permutations)`: Creates random permutations of the available tokens for brute-force evaluation.

- **Permutation Evaluation:**
  - `evaluate_permutations(driver, permutations)`: Resets the game state and evaluates each permutation, scoring the results.

- **Simulated Annealing:**
  - `simulated_annealing(driver, initial_permutations, ...)`: Uses simulated annealing with random restarts to search for the best permutation, improving efficiency over pure brute-force.

- **Simulation Entry Point:**
  - `run_simulations(quest_id, mc_id, servant_init_dicts, ...)`: Initializes the driver, generates tokens, permutations, and runs the evaluation and annealing. Results are saved to `simulation_results.json`.

- **Input Parsing:**
  - `parse_input_data(input_data)`: Parses team, mystic code, and quest data from JSON input, converting web app format to simulation format.

- **Main Function:**
  - `main(input_data_json, ...)`: Loads input, parses data, and runs the simulation.

### Design Limitations
- Relies on random permutation generation and simulated annealing, which can be computationally expensive and non-deterministic.
- Does not use state serialization or FSM graph traversal, making it hard to reuse or analyze previous results.
- Code is monolithic and difficult to read/extend for new features (e.g., user-supplied FSMs, state restoration).

### Recommended Refactor
- Split logic into multiple files/modules:
  - Token generation
  - Permutation/evaluation
  - State serialization and FSM graph logic
  - Database and result management
- Implement FSM-based simulation for scalable, reusable, and mathematically provable quest evaluation.
- Allow user-supplied FSMs and cached results for faster searching and analysis.

---
This documentation serves as a reference for refactoring and tracking changes as you migrate from heuristic search to FSM-based simulation.
