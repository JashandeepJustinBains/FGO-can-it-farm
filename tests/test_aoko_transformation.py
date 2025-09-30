from pymongo import MongoClient
from dotenv import load_dotenv
import sys, os
load_dotenv()
mongo_uri = os.getenv('MONGO_URI_READ')
if not mongo_uri:
    raise ValueError("No MONGO_URI_READ environment variable set")
client = MongoClient(mongo_uri)
db = client['FGOCanItFarmDatabase']
servants_collection = db['servants']
quests_collection = db['quests']
mysticcode_collection = db['mysticcodes']
sys.stdout.reconfigure(encoding='utf-8')
import tests.test_db_setup
import logging
import os
os.makedirs("outputs", exist_ok=True)
logging.basicConfig(
    filename="outputs/output.log",
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
from sim_entry_points.traverse_api_input import traverse_api_input

def test_aoko_transformation():
    input_data = {
        "Team": [
            {"collectionNo": 413, "initialCharge": 20, "attack": 2400, "damageUp": 0.3},
            {"collectionNo": 414, "np": 5, "attack": 2000, "initialCharge": 20},
            {"collectionNo": 284},
            {"collectionNo": 284},
            {"collectionNo": 316}
        ],
        "Mystic Code ID": 210,
        "Quest ID": 94095710,
        "Commands": ["a", "c1", "g", "h1", "i1", "x32", "h1", "g", "i2", "d", "e", "4", "5", "#", "b", "4", "#", "a", "d", "e1", "f1", "j", "4", "#"]
    }
    servants = [s for s in input_data["Team"] if s.get("collectionNo")]
    mc_id = input_data["Mystic Code ID"]
    quest_id = input_data["Quest ID"]
    commands = input_data["Commands"]
    import logging
    logging.basicConfig(
        filename="outputs/aoko_transformation_full_debug.log",
        filemode="w",
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    driver_state = traverse_api_input(servants, mc_id, quest_id, commands)
    final_ids = [s.id for s in driver_state.game_manager.servants]
    output_lines = []
    output_lines.append("--- Team representation (team_repr) ---\n")
    output_lines.append(driver_state.game_manager.team_repr() + "\n")
    output_lines.append("--- GameManager repr() ---\n")
    output_lines.append(repr(driver_state.game_manager) + "\n")
    output_lines.append("--- Final ids ---\n")
    output_lines.append(str(final_ids) + "\n")
    # Write output to a temp file in /outputs
    import os
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/aoko_transformation_test_output.txt", "w", encoding="utf-8") as f:
        f.writelines(line + "\n" if not line.endswith("\n") else line for line in output_lines)
    # Expected final ordering and members (exact): 4132, 284, 316, 284
    assert final_ids == [4132, 284, 316, 284], f"Final party mismatch, got {final_ids}"
    assert 414 not in final_ids, "Servant 414 should have been removed from the party"
    assert 413 not in final_ids, "Original 413 should no longer be present after transform"
    assert driver_state == True
