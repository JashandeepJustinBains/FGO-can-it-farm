import pytest
import json
from sim_entry_points.traverse_fsm_path import main_fsm_path

def test_traverse_fsm_path_runs_without_error():
    input_data = {
        "Team": [
            {"collectionNo": 373},
            {"collectionNo": 426, "attack": 2400, "atkUp": 15, "artsUp": 10, "quickUp": 10, "busterUp": 10, "npUp": 10, "initialCharge": 50, "busterDamageUp": 20, "quickDamageUp": 20, "artsDamageUp": 20, "append_5": True},
            {"collectionNo": 421},
            {"collectionNo": 426, "attack": 200, "atkUp": 0, "artsUp": 0, "artsDamageUp": 20, "initialCharge": 0, "append_5": False},
        ],
        "Mystic Code ID": 20,
        "Quest ID": 94091610,
        "FSMPath": ["a", "d", "g1", "h", "b", "c", "4", "#", "e", "f", "i1", "x23", "g1", "5", "#", "h", "i1", "4", "#", "Swap Servants", "x14"]
    }
    input_json = json.dumps(input_data)
    final_state, state_path = main_fsm_path(input_json)
    assert final_state is not None
    assert len(state_path) == len(input_data["FSMPath"]) + 1

def test_traverse_fsm_path_detailed_output():
    input_data = {
        "Team": [
            {"collectionNo": 364, "attack": 3000, "npUp": 80, "initialCharge": 20},
            {"collectionNo": 284},
            {"collectionNo": 284},
            {"collectionNo": 316},
        ],
        "Mystic Code ID": 210,
        "Quest ID": 94062608,
        "FSMPath": ["a", "b", "c", "d", "g", "e1", "h2", "f1", "i1", "4", "#", "x21", "g", "h1", "i1", "j", "5", "4", "#"]
    }
    input_json = json.dumps(input_data)
    final_state, state_details = main_fsm_path(input_json)
    assert final_state is not None
    assert len(state_details) == len(input_data["FSMPath"]) + 1
    # Print the detailed state info for inspection
    print(json.dumps(state_details, indent=2))
