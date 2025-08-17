import pytest
import json
from sim_entry_points.fsm_command_replay import main_with_commands

def test_fsm_command_replay_runs_without_error():
    input_data = {
        "Team": [
            {"collectionNo": 373},
            {"collectionNo": 426, "attack": 2400, "atkUp": 15, "artsUp": 10, "quickUp": 10, "busterUp": 10, "npUp": 10, "initialCharge": 50, "busterDamageUp": 20, "quickDamageUp": 20, "artsDamageUp": 20, "append_5": True},
            {"collectionNo": 421},
            {"collectionNo": 426, "attack": 200, "atkUp": 0, "artsUp": 0, "artsDamageUp": 20, "initialCharge": 0, "append_5": False},
        ],
        "Mystic Code ID": 20,
        "Quest ID": 94091610,
        "Commands": ["a", "d", "g1", "h", "b", "c", "4", "#", "e", "f", "i1", "x23", "g1", "5", "#", "h", "i1", "4", "#", "Swap Servants", "x14"]
    }
    input_json = json.dumps(input_data)
    # This will pass if no exception is raised and a final state is returned
    final_state = main_with_commands(input_json)
    assert final_state is not None
# ...existing code...
