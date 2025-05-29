import pytest
from sim_entry_points.TraverseAPIInput import traverse_api_input

def test_traverse_api_input_runs_without_error():
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
    servants = input_data["Team"]
    mc_id = input_data["Mystic Code ID"]
    quest_id = input_data["Quest ID"]
    commands = input_data["Commands"]
    # This will pass if no exception is raised
    traverse_api_input(servants, mc_id, quest_id, commands)