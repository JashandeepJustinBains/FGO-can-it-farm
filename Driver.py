from GameState import GameState
from Quest import Quest
from connectDB import db
from data import character_list_support
from data import character_list_multicore_actuallygood
from beaver import Beaver
from Servant import Servant

from itertools import permutations

class Driver:
    def __init__(self, servant_ids, quest_id):
        self.servant_ids = servant_ids
        self.quest_id = quest_id
        self.game_state = None

    def setup_game_state(self):
        # Instantiate the GameState class
        self.game_state = GameState()

        # Instantiate a Quest instance and retrieve enemies
        quest = Quest(self.quest_id)
        self.game_state.enemies = quest.get_wave(self.game_state.wave)
        quest.pretty_print_waves()

        # Add servants to the game state
        for servant_id in self.servant_ids:
            self.game_state.add_servant(servant_id=servant_id)


    def generate_tokens_for_positions(self):
        all_tokens = []
        skill_tokens = [['a', 'b', 'c', 4], ['d', 'e', 'f', 5], ['g', 'h', 'i', 6]]
        
        for i in range(3):  # Only 3 positions on the field
            servant = Servant(self.servant_ids[i])
            servant_tokens = []
            for skill, token in zip(servant.get_skills(), skill_tokens[i]):
                has_ptOne = any(func['funcTargetType'] == 'ptOne' for func in skill['functions'])
                if has_ptOne:
                    for j in range(1, 4):
                        servant_tokens.append(f"{token}{j}")
                else:
                    servant_tokens.append(token)
            all_tokens.append(servant_tokens)

        for i, tokens in enumerate(all_tokens):
            print(f"Position {i+1} tokens: {tokens}")
        return all_tokens

    def find_valid_permutation(self):
        all_tokens = self.generate_tokens_for_positions()
        flat_tokens = [token for sublist in all_tokens for token in sublist]
        
        for perm in permutations(flat_tokens):
            # game_state = GameState()  # Create a new GameState instance
            if self.game_state.simulate_permutation(perm):
                return perm
        return None

    def run(self):
        self.setup_game_state()
        self.generate_tokens_for_positions()
        valid_permutation = self.find_valid_permutation()
        if valid_permutation:
            print("Valid permutation found:", valid_permutation)
        else:
            print("No valid permutation found.")

if __name__ == '__main__':
    # Example usage
    servant_ids = [51, 314, 314, 316]  # List of servant IDs
    quest_id = 94086602  # Quest ID
    beaver_instance = Beaver("test")
   
    driver = Driver(servant_ids, quest_id)
    driver.run()
