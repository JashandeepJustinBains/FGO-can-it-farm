from GameState import GameState
from Quest import Quest
from connectDB import db
from data import character_list_support
from data import character_list_multicore_actuallygood
from Servant import Servant
import numpy as np
from itertools import product
from tabulate import tabulate

class Driver:
    def __init__(self, servant_ids, quest_id):
        self.servant_ids = servant_ids
        self.quest_id = quest_id
        self.game_state = None
        self.quest = None

    def setup_game_state(self):
        # Instantiate the GameState class
        self.game_state = GameState()

        # Instantiate a Quest instance and retrieve enemies
        self.quest = Quest(self.quest_id)
        # self.game_state.enemies = quest.get_wave(self.game_state.wave)
        self.quest.pretty_print_waves()

        # Add servants to the game state
        # for servant_id in self.servant_ids:
            # self.game_state.add_servant(servant_id=servant_id)

    def run(self):
        self.setup_game_state()
        
        # Generate all permutations of buffs
        buff_ranges = {
            "attack_up": range(0, 121, 10),
            "x_up": range(0, 201, 10),
            "np_damage_up": range(0, 251, 10)
        }
        base_attack = 12000
        results = []
        attribute_multiplier = [0.9, 1.0, 1.1]
        for attack_up, x_up, np_damage_up in product(buff_ranges["attack_up"], buff_ranges["x_up"], buff_ranges["np_damage_up"]):
            self.game_state.attack_up = attack_up
            self.game_state.x_up = x_up
            self.game_state.np_damage_up = np_damage_up
            total_damage = self.game_state.calculate_damage(base_attack, attribute_multiplier)
            if total_damage >= self.quests.get_wave().enemy.get_hp():
                results.append([attack_up, x_up, np_damage_up, total_damage])

        # Display results in a table
        headers = ["Attack Up", "X Up", "NP Damage Up", "Total Damage"]
        results_array = np.array(results)
        formatted_results = [[f"{x:.2f}" for x in row] for row in results_array]
        print(tabulate(formatted_results, headers=headers, tablefmt="grid"))

if __name__ == '__main__':
    # Example usage
    servant_ids = [51, 314, 314, 316]  # List of servant IDs
    quest_id = 94086602  # Quest ID
   
    driver = Driver(servant_ids, quest_id)
    driver.run()
    # game_state = GameState()  # Create a new GameState instance

