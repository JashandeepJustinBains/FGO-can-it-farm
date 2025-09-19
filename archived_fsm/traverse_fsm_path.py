import json
from Driver import Driver
from units.Servant import Servant

def get_servant_state(servant):
    return {
        "collectionNo": getattr(servant, "id", None),
        "attack": getattr(servant, "ce_attack", None),
        "np_level": getattr(servant, "np_level", None),
        "np_gauge": getattr(servant, "np_gauge", None),
        "damage": getattr(servant, "last_damage", None) if hasattr(servant, "last_damage") else None
    }

def traverse_fsm_path(servant_init_dicts, mc_id, quest_id, fsm_path):
    """
    Given a team, mystic code, quest, and a path of FSM states (or actions),
    traverse the FSM graph by applying each action in sequence.
    Returns the final state and optionally the full state path.
    """
    driver = Driver(servant_init_dicts=servant_init_dicts, quest_id=quest_id, mc_id=mc_id)
    driver.reset_state()
    state_details = []
    # Record initial state before any actions
    servants_state = [get_servant_state(s) for s in driver.game_manager.servants]
    state_details.append({
        "turn": 0,
        "action": None,
        "servants": servants_state
    })
    for idx, action in enumerate(fsm_path):
        driver.execute_token(action)
        servants_state = [get_servant_state(s) for s in driver.game_manager.servants]
        state_details.append({
            "turn": idx + 1,
            "action": action,
            "servants": servants_state
        })
    # Save to JSON for inspection
    with open("fsm_path_details.json", "w") as f:
        json.dump(state_details, f, indent=2)
    return state_details[-1] if state_details else None, state_details

def main_fsm_path(input_data_json):
    input_data = json.loads(input_data_json)
    team = input_data["Team"]
    mc_id = input_data["Mystic Code ID"]
    quest_id = input_data["Quest ID"]
    fsm_path = input_data.get("FSMPath", [])
    final_state, state_details = traverse_fsm_path(team, mc_id, quest_id, fsm_path)
    return final_state, state_details
