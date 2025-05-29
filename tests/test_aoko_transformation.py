from tests.TraverseAPIInput import traverse_api_input

def test_aoko_transformation():
    input_data = {
        "Team": [
            {"collectionNo": 413, "initialCharge": 20},
            {"collectionNo": 414, "np": 5},
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
    driver_state = traverse_api_input(servants, mc_id, quest_id, commands)

    # Now check for transformed Aoko (collectionNo 4132)
    found = False
    for servant in driver_state.game_manager.servants:
        if servant.id == 414:
            print(servant)
        if servant.id == 4132:
            found = True
            print("Transformed Aoko found:", servant)
    assert found, "Transformed Aoko (collectionNo 4132) not found in servants list"