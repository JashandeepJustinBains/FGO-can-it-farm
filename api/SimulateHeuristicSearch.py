import json
import random
import argparse
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from Driver import Driver
from units.Servant import Servant

# TODO this is scary ass code I do not even want to try to remember

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
mongo_uri = os.getenv('MONGO_URI_READ')
if not mongo_uri:
    raise ValueError("No MONGO_URI_READ environment variable set")

# Connect to MongoDB
client = MongoClient(mongo_uri)
db = client['FGOCanItFarmDatabase']

def generate_tokens_for_positions(driver):
    driver.all_tokens = []  # Initialize the list to store all tokens
    on_field = driver.game_manager.servants[0:3]
    for i, servant in enumerate(on_field):
        servant_tokens = []
        for skill_num, skill in enumerate(servant.skills.skills):
            tokens = generate_tokens_for_skill(driver, servant, skill_num)
            servant_tokens.extend(tokens)
        driver.all_tokens.append(servant_tokens)

    # Add Mystic Code Tokens
    mystic_code = driver.game_manager.mc
    mystic_code_tokens = []
    for skill_num in range(len(mystic_code.skills)):
        tokens = generate_tokens_for_mystic_code(driver, mystic_code, skill_num)
        mystic_code_tokens.extend(tokens)
    driver.all_tokens.append(mystic_code_tokens)

    # Create multiple instances of each token
    driver.all_tokens.append('#')
    driver.all_tokens.append('#')
    driver.all_tokens.append('#')
    driver.usable_tokens = [token for sublist in driver.all_tokens for token in sublist for _ in range(2)]

    return driver.usable_tokens

def generate_tokens_for_skill(driver, servant, skill_num):
    skill_tokens = [['a', 'b', 'c'], ['d', 'e', 'f'], ['g', 'h', 'i']]
    servant_index = driver.game_manager.servants.index(servant)
    token = skill_tokens[servant_index][skill_num]
    skill = servant.skills.get_skill_by_num(skill_num)
    has_ptOne = any(func['funcTargetType'] == 'ptOne' for func in skill['functions'])

    if has_ptOne:
        return [(f"{token}{i}") for i in range(1, 4)]
    else:
        return [token]

def generate_tokens_for_mystic_code(driver, mystic_code, skill_num):
    if driver.mc_id == 260 or driver.mc_id == 20:
        skill_tokens = [['j', 'k', 'x']]  # Adjust according to the condition
    else:
        skill_tokens = [['j', 'k', 'l']]
    token = skill_tokens[0][skill_num]  # Use the first (and only) sub-array
    skill = mystic_code.skills[skill_num]

    has_ptOne = any(func['funcTargetType'] == 'ptOne' for func in skill['functions'])
    has_orderChange = any(func['funcTargetType'] == 'positionalSwap' for func in skill['functions'])

    if has_ptOne:
        return [(f"{token}{i}") for i in range(1, 4)]
    elif has_orderChange:
        return [f"{token}_swap_{i}{j}" for i in range(1, 4) for j in range(1, 4)]
    else:
        return [token]

def generate_random_permutations(tokens, num_permutations):
    permutations = []
    for _ in range(num_permutations):
        perm = tokens[:]
        random.shuffle(perm)
        permutations.append(perm)
    return permutations

def evaluate_permutations(driver, permutations):
    results = []
    for perm in permutations:
        driver.reset_state()
        total_score = driver.evaluate_permutation(perm)
        results.append({
            'permutation': perm,
            'total_score': total_score,
        })
    return results

def simulated_annealing(driver, initial_permutations, max_iterations=1000, restart_probability=0.1):
    best_permutation = None
    best_score = float('inf')
    current_permutation = random.choice(initial_permutations)
    current_score = driver.evaluate_permutation(current_permutation)

    for iteration in range(max_iterations):
        if random.random() < restart_probability:
            current_permutation = random.choice(initial_permutations)
            current_score = driver.evaluate_permutation(current_permutation)
        else:
            neighbor_permutation = current_permutation[:]
            random.shuffle(neighbor_permutation)
            neighbor_score = driver.evaluate_permutation(neighbor_permutation)

            if neighbor_score < current_score:
                current_permutation = neighbor_permutation
                current_score = neighbor_score

        if current_score < best_score:
            best_permutation = current_permutation
            best_score = current_score

    return best_permutation, best_score

def run_simulations(quest_id, mc_id, servant_init_dicts, num_permutations=10000, max_iterations=1000, restart_probability=0.1):
    # Initialize driver and receive tokens

    # init servants using truth source dictionary
    servants = [Servant(**params) for params in servant_init_dicts]

    init_driver = Driver(servants=servants, quest_id=quest_id, mc_id=mc_id)
    all_tokens = generate_tokens_for_positions(init_driver)
    # Generate initial random permutations
    initial_permutations = generate_random_permutations(all_tokens, num_permutations)
    # Evaluate initial permutations
    initial_results = evaluate_permutations(init_driver, initial_permutations)
    # Run simulated annealing with random restarts
    best_permutation, best_score = simulated_annealing(init_driver, initial_permutations, max_iterations, restart_probability)

    # Save results to a JSON file
    results = {
        'initial_results': initial_results,
        'best_permutation': best_permutation,
        'best_score': best_score,
    }
    with open('simulation_results.json', 'w') as f:
        json.dump(results, f, indent=4)

    print(f"Simulations completed. Results saved to 'simulation_results.json'.")

def parse_input_data(input_data):
    # Parse the team data
    team = input_data.get('Team', [])
    parsed_team = []
    for servant_data in team:
        collection_no = servant_data.get('collectionNo')
        if not collection_no:
            continue
        parsed_servant = {
            'collectionNo': collection_no,
            'np': servant_data.get('npLevel', 0),
            'attack': servant_data.get('attack', 0),
            'atkUp': servant_data.get('atkUp', 0),
            'artsUp': servant_data.get('artsUp', 0),
            'quickUp': servant_data.get('quickUp', 0),
            'busterUp': servant_data.get('busterUp', 0),
            'npUp': servant_data.get('npUp', 0),
            'damageUp': servant_data.get('damageUp', 0),
            'initialCharge': servant_data.get('initialCharge', 0),
            'busterDamageUp': servant_data.get('busterDamageUp', 0),
            'quickDamageUp': servant_data.get('quickDamageUp', 0),
            'artsDamageUp': servant_data.get('artsDamageUp', 0),
            'append_2': servant_data.get('append_2', False),
            'append_5': servant_data.get('append_5', False),
        }
        parsed_team.append(parsed_servant)

    # Parse the Mystic Code ID and Quest ID
    mystic_code_id = input_data.get('Mystic Code ID')
    quest_id = input_data.get('Quest ID')

    return parsed_team, mystic_code_id, quest_id

def main(input_data_json, num_permutations=10000, max_iterations=1000, restart_probability=0.1):
    input_data = json.loads(input_data_json)
    servant_init_dicts, mc_id, quest_id = parse_input_data(input_data)
    # Ignore commands for simulation; use only servant_init_dicts, mc_id, quest_id
    run_simulations(quest_id, mc_id, servant_init_dicts, num_permutations, max_iterations, restart_probability)
