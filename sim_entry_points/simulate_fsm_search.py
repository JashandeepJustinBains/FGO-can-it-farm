import json
import networkx as nx
from Driver import Driver
from units.Servant import Servant

def serialize_state(driver):
    """Serialize the current game state into a hashable tuple."""
    def make_hashable(x):
        if isinstance(x, set):
            return tuple(sorted(x))
        if isinstance(x, dict):
            return tuple(sorted((k, make_hashable(v)) for k, v in x.items()))
        if isinstance(x, list):
            return tuple(make_hashable(i) for i in x)
        # Convert non-serializable objects to string
        if hasattr(x, '__dict__') or hasattr(x, '__class__'):
            return str(x)
        return x
    servants = tuple(
        tuple(make_hashable(attr) for attr in [
            getattr(s, 'id', None),
            getattr(s, 'np_level', None),
            getattr(s, 'ce_attack', None),
            getattr(s, 'atk_mod', None),
            getattr(s, 'a_up', None),
            getattr(s, 'q_up', None),
            getattr(s, 'b_up', None),
            getattr(s, 'user_np_damage_mod', None),
            getattr(s, 'power_mod', None),
            getattr(s, 'np_gauge', None),
            getattr(s, 'user_buster_damage_up', None),
            getattr(s, 'user_quick_damage_up', None),
            getattr(s, 'user_arts_damage_up', None),
            getattr(s, 'skills', None),
            getattr(s, 'passives', None),
            getattr(s, 'kill', None),
            getattr(s, 'user_atk_mod', None),
            getattr(s, 'append_5', None)
        ])
        for s in driver.game_manager.servants
    )
    quest = make_hashable(driver.game_manager.quest_id)
    mc = make_hashable(driver.mc_id)
    # Add more as needed for full state
    return (servants, quest, mc)

def generate_fsm_graph(driver, max_depth=20):
    """Generate FSM graph for all reachable states from initial state."""
    G = nx.DiGraph()
    initial_state = serialize_state(driver)
    queue = [(initial_state, driver.copy(), 0)]  # (state, driver, turn)
    visited = set()
    import logging
    logging.basicConfig(filename='./outputs/output.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
    step_counter = 0
    while queue:
        next_queue = []
        for state, drv, turn in queue:
            state_id = (state, turn)
            if state_id in visited:
                continue
            visited.add(state_id)
            G.add_node(state_id)
            step_counter += 1
            if step_counter % 100 == 0:
                logging.info(f"FSM Search Step {step_counter}: Turn={turn}, Action(s)={drv.get_all_possible_actions()}, State={state_id}")
            if step_counter > 1000:
                logging.error("FSM Search failed: Exceeded 1000 steps, possible infinite loop.")
                print("FSM Search failed: Exceeded 1000 steps, possible infinite loop.")
                return G
            quest_complete = False
            if hasattr(drv.game_manager, 'get_enemies') and all(e.get_hp() <= 0 for e in drv.game_manager.get_enemies()):
                if hasattr(drv.game_manager, 'total_waves') and hasattr(drv.game_manager, 'wave'):
                    if drv.game_manager.wave >= drv.game_manager.total_waves:
                        quest_complete = True
            if quest_complete or turn >= 3:
                continue
            actions = drv.get_all_possible_actions()
            if turn == 2 or quest_complete:
                actions = ['#']
            for action in actions:
                drv_next = drv.copy()
                drv_next.apply_action(action)
                next_state = serialize_state(drv_next)
                next_queue.append((next_state, drv_next, turn + 1))
                G.add_edge(state_id, (next_state, turn + 1), action=action)
        queue = next_queue
    logging.info(f"FSM Search completed after {step_counter} steps.")
    return G

def save_fsm_graph_json(G, filename):
    data = nx.node_link_data(G)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def main(input_data_json, max_depth=20):
    input_data = json.loads(input_data_json)
    team, mc_id, quest_id = parse_input_data(input_data)
    # Only pass accepted keys to Servant constructor
    servant_keys = [
        'collectionNo', 'np', 'initialCharge', 'attack', 'atkUp', 'artsUp', 'quickUp', 'busterUp',
        'npUp', 'damageUp', 'busterDamageUp', 'quickDamageUp', 'artsDamageUp', 'append_5'
    ]
    # For FSM, pass servant_init_dicts to Driver, not Servant objects
    driver = Driver(servant_init_dicts=team, quest_id=quest_id, mc_id=mc_id)
    G = generate_fsm_graph(driver, max_depth=max_depth)
    save_fsm_graph_json(G, 'fsm_graph.json')
    print(f"FSM graph generated and saved to 'fsm_graph.json'.")

# Helper function from previous entry point

def parse_input_data(input_data):
    team = input_data.get('Team', [])
    parsed_team = []
    for servant_data in team:
        collection_no = servant_data.get('collectionNo')
        if not collection_no:
            continue
        initial_charge = servant_data.get('initialCharge', 0)
        if servant_data.get('append_2', False):
            initial_charge += 20
        parsed_servant = {
            'collectionNo': collection_no,
            'np': servant_data.get('npLevel', 0),
            'attack': servant_data.get('attack', 0),
            'atkUp': servant_data.get('atkUp', 0),
            'artsUp': servant_data.get('artsUp', 0),
            'quickUp': servant_data.get('quickUp', 0),
            'busterUp': servant_data.get('busterUp', 0),
            'npUp': servant_data.get('npUp', 0),
            'damageUp': servant_data.get('damageUp', 0),
            'initialCharge': initial_charge,
            'busterDamageUp': servant_data.get('busterDamageUp', 0),
            'quickDamageUp': servant_data.get('quickDamageUp', 0),
            'artsDamageUp': servant_data.get('artsDamageUp', 0),
            'append_5': servant_data.get('append_5', False),
        }
        parsed_team.append(parsed_servant)
    mystic_code_id = input_data.get('Mystic Code ID')
    quest_id = input_data.get('Quest ID')
    return parsed_team, mystic_code_id, quest_id
