import json
from sim_entry_points.simulate_fsm_search import main as fsm_main

def test_fsm_entry_point():
    # Example input matching parsed_servant structure
    input_data = {
        "Team": [
            {
                "collectionNo": 1,
                "npLevel": 2,
                "attack": 10000,
                "atkUp": 20,
                "artsUp": 10,
                "quickUp": 0,
                "busterUp": 0,
                "npUp": 0,
                "damageUp": 0,
                "initialCharge": 50,
                "busterDamageUp": 0,
                "quickDamageUp": 0,
                "artsDamageUp": 0,
                "append_2": False,
                "append_5": False
            }
        ],
        "Mystic Code ID": 20,
        "Quest ID": 101
    }
    input_json = json.dumps(input_data)
    fsm_main(input_json, max_depth=5)
    with open('fsm_graph.json') as f:
        data = json.load(f)
    assert 'nodes' in data and 'links' in data
    print("FSM entry point test passed.")
