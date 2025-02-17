import json
import random
from Driver import Driver

def generate_random_permutations(tokens, num_permutations):
    permutations = []
    for _ in range(num_permutations):
        perm = tokens[:]
        random.shuffle(perm)
        permutations.append(perm)
    return permutations

def run_simulations(servant_ids, quest_id, mc_id, num_permutations=10000):
    # initialize driver and recieve tokens
    init_driver = Driver(servant_ids=servant_ids, quest_id=quest_id, mc_id=mc_id)
    all_tokens = init_driver.generate_tokens_for_positions()
    # generate num_permutations of random permutations of the all_tokens list
    random_permutations = generate_random_permutations(all_tokens, num_permutations)
    results = []

    for perm in random_permutations:
        # reset driver each permutation test
        driver = Driver(servant_ids=servant_ids, quest_id=quest_id, mc_id=mc_id)
        driver.reset_state()
        total_score = driver.evaluate_permutation(perm)
        results.append({
            'permutation': perm,
            'total_score': total_score,
        })

    # Save results to a JSON file
    with open('simulation_results.json', 'w') as f:
        json.dump(results, f, indent=4)

    print(f"Simulations completed. Results saved to 'simulation_results.json'.")

if __name__ == '__main__':
    servant_ids = [413, 414, 284, 284, 316]  # Example servant IDs
    quest_id = 94095710  # Example quest ID
    mc_id = 260  # Example Mystic Code ID
    run_simulations(servant_ids, quest_id, mc_id, num_permutations=100)