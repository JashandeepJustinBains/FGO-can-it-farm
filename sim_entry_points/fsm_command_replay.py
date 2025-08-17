import json
from Driver import Driver

def replay_command_sequence(servant_init_dicts, mc_id, quest_id, commands):
    """
    Given a team, mystic code, quest, and a sequence of commands,
    replay the commands step-by-step and return the final state.
    """
    driver = Driver(servant_init_dicts=servant_init_dicts, quest_id=quest_id, mc_id=mc_id)
    driver.reset_state()
    for cmd in commands:
        driver.execute_token(cmd)
    # Optionally, serialize and return the final state
    return driver

def main_with_commands(input_data_json):
    input_data = json.loads(input_data_json)
    team = input_data["Team"]
    mc_id = input_data["Mystic Code ID"]
    quest_id = input_data["Quest ID"]
    commands = input_data.get("Commands", [])
    final_driver = replay_command_sequence(team, mc_id, quest_id, commands)
    # For test purposes, return a hashable state
    return str(final_driver.game_manager.servants)
