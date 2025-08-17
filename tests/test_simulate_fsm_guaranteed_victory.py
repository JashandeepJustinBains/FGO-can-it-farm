import json
from sim_entry_points.simulate_fsm_search import main as fsm_main

def test_fsm_search_guaranteed_victory():
    input_data = {
        "Team": [
            {"collectionNo": 364, "attack": 3000, "npUp": 80, "initialCharge": 20},
            {"collectionNo": 284},
            {"collectionNo": 284},
            {"collectionNo": 316},
        ],
        "Mystic Code ID": 210,
        "Quest ID": 94062608
    }
    input_json = json.dumps(input_data)
    # Run FSM search for this team/quest
    fsm_main(input_json, max_depth=10)
    with open('fsm_graph.json') as f:
        data = json.load(f)
    assert 'nodes' in data and 'links' in data
# ...existing code...
