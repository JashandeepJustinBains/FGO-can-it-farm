from sim_entry_points.traverse_api_input import traverse_api_input

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
    # Final party should reflect that 414 sacrificed themself and 413 transformed.
    final_ids = [s.id for s in driver_state.game_manager.servants]
    # Print the human-readable team representation added to GameManager
    print("\n--- Team representation (team_repr) ---\n")
    print(driver_state.game_manager.team_repr())
    print("\n--- GameManager repr() ---\n")
    print(repr(driver_state.game_manager))
    print("\n--- Final ids ---\n")
    print(final_ids)
    # Expected final ordering and members (exact): 4132, 284, 316, 284
    assert final_ids == [4132, 284, 316, 284], f"Final party mismatch, got {final_ids}"

    # Sanity checks
    assert 414 not in final_ids, "Servant 414 should have been removed from the party"
    assert 413 not in final_ids, "Original 413 should no longer be present after transform"