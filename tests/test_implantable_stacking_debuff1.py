import pytest
from sim_entry_points.traverse_api_input import traverse_api_input

# test: Does SE work based on Roman trait work?, also tested 2 waves of enemies!
def test_implantable_stacking_debuff1():
    input_data = {
        "Team": [
            {"collectionNo": 314},
            {"collectionNo": 314},
            {"collectionNo": 280 , "attack": 2400, "atkUp": 0.15, "artsUp": 0.10, "quickUp": 0.10, "busterUp": 0.10, "npUp": 0.90, "initialCharge": 50, "busterDamageUp": 0.20, "quickDamageUp": 0.20, "artsDamageUp": 0.20, "append_5": True},
            {"collectionNo": 316, "attack": 200, "atkUp": 0, "artsUp": 0, "artsDamageUp": 20, "initialCharge": 0, "append_5": False},
        ],
        "Mystic Code ID": 20,
        "Quest ID": 94089601,
        "Commands": ["b3","c3","e3","f3","i", "a3", "d3", "6", "#", "h", "i", "g", "j", "x11", "a", "b3", "c3", "6", "#"]
    }
    servants = input_data["Team"]
    mc_id = input_data["Mystic Code ID"]
    quest_id = input_data["Quest ID"]
    commands = input_data["Commands"]
    # This will pass if no exception is raised
    traverse_api_input(servants, mc_id, quest_id, commands)

