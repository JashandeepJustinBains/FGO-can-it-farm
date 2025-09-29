import logging
import os
import sys
os.makedirs("outputs", exist_ok=True)
logging.basicConfig(
    filename="outputs/output.log",
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
from sim_entry_points.traverse_api_input import traverse_api_input
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
import connectDB

# Ensure global db is set in this test's global scope
if hasattr(connectDB, 'db'):
    globals()['db'] = connectDB.db

def test_paladin_mash():
    input_data = {
        "Team": [
            {"collectionNo": 1, "attack": 2000, "initialCharge": 20, "np": 3},
            {"collectionNo": 16, "lvl": 100, "attack": 2400, "initialCharge": 20, "np": 5, "npUp": 0.80, "oc": 1},
            {"collectionNo": 150},
            {"collectionNo": 316},
            {"collectionNo": 314}
        ],
        "Mystic Code ID": 210,
        "Quest ID": 94095710,
        "Commands": [
                    # Turn 1
                    "a", "b1", "f", "g", "h", "i1", "4", "5", "#",
                    # Turn 2, collectionNo:16 should sacrifice and turn_manager should slide over 316 into the position he was in
                    "x31", "d", "e1", "g1", "i1", "4", "#",
                    # Turn 3
                    "b", "f1", "j", "4", "#"
                    ]
    }
    servants = [s for s in input_data["Team"] if s.get("collectionNo")]
    mc_id = input_data["Mystic Code ID"]
    quest_id = input_data["Quest ID"]
    commands = input_data["Commands"]
    driver_state = traverse_api_input(servants, mc_id, quest_id, commands)
    final_ids = [s.id for s in driver_state.game_manager.servants]
    output_lines = []
    output_lines.append("--- Team representation (team_repr) ---\n")
    output_lines.append(driver_state.game_manager.team_repr() + "\n")
    output_lines.append("--- GameManager repr() ---\n")
    output_lines.append(repr(driver_state.game_manager) + "\n")
    output_lines.append("--- Final ids ---\n")
    output_lines.append(str(final_ids) + "\n")



    # Assert Paladin Mash (collectionNo==1, class Shielder, Paladin skills/NPs) is present
    paladin_mash = None
    for servant in driver_state.game_manager.servants:
        if getattr(servant, 'collectionNo', None) == 1:
            paladin_mash = servant
            break
    assert paladin_mash is not None, "Paladin Mash (collectionNo==1) should be present in the final team"
    assert getattr(paladin_mash, 'class_name', '').lower() == 'shielder', "Paladin Mash should be class Shielder"



    # Assert all waves are cleared (quest defeated)
    gm = driver_state.game_manager
    assert gm.wave > gm.total_waves, f"All waves should be cleared (got wave={gm.wave}, total_waves={gm.total_waves})"

    # Expected final ordering and members (exact): 4132, 284, 316, 284
    assert 16 not in final_ids, "Servant 16 should have been removed from the party"