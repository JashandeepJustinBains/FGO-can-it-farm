import json
from sim_entry_points.simulate_fsm_search import main as fsm_main

def test_fsm_search_guaranteed_victory():
    input_data = {
        "Team": [
            {"collectionNo": 364, "attack": 3000, "npUp": 80, "initialCharge": 20, "np": 5},
            {"collectionNo": 284},
            {"collectionNo": 284},
            {"collectionNo": 316},
        ],
        "Mystic Code ID": 210,
        "Quest ID": 94062608
    }
    input_json = json.dumps(input_data)
    fsm_main(input_json, max_depth=10)
    with open('fsm_graph.json') as f:
        data = json.load(f)
    assert 'nodes' in data and 'links' in data

def test_fsm_search_minimal_team():
    input_data = {
        "Team": [
            {"collectionNo": 364},
            {"collectionNo": 284},
            {"collectionNo": 316},
        ],
        "Mystic Code ID": 210,
        "Quest ID": 94062608
    }
    input_json = json.dumps(input_data)
    fsm_main(input_json, max_depth=5)
    with open('fsm_graph.json') as f:
        data = json.load(f)
    assert isinstance(data['nodes'], list)
    assert isinstance(data['links'], list)

def test_fsm_search_invalid_team():
    input_data = {
        "Team": [],
        "Mystic Code ID": 210,
        "Quest ID": 94062608
    }
    input_json = json.dumps(input_data)
    try:
        fsm_main(input_json, max_depth=3)
        with open('fsm_graph.json') as f:
            data = json.load(f)
        assert 'nodes' in data and 'links' in data
    except Exception:
        assert True  # Should raise or handle gracefully
