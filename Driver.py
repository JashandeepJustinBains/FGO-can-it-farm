from managers.turn_manager import TurnManager
from managers.skill_manager import SkillManager
from managers.game_manager import GameManager
from managers.np_manager import npManager
from managers.Quest import Quest
from units.Servant import Servant
from units.Enemy import Enemy
from itertools import permutations, product
import json
import itertools
import random


class Driver:
    def __init__(self, servant_ids, quest_id):
        self.servant_ids = servant_ids
        self.quest_id = quest_id
        self.turn_manager = None
        self.skill_manager = None
        self.np_manager = None
        self.game_manager = GameManager(self.servant_ids, self.quest_id)
        self.permutations_file = "test_permutations.json"
        self.all_tokens = []
        self.usable_tokens = []  # Track currently usable tokens
        self.max_depth = 3  # Maximum depth for recursion

    def reset_state(self):
        self.game_manager = GameManager(self.servant_ids, self.quest_id)
        self.turn_manager = TurnManager(self.game_manager)
        self.skill_manager = SkillManager(self.turn_manager)
        self.np_manager = npManager(self.skill_manager)

    def generate_tokens_for_positions(self):
        self.all_tokens = []  # Initialize the list to store all tokens

        on_field = self.game_manager.servants[0:3]

        for i, servant in enumerate(on_field):
            servant_tokens = []
            for skill_num in range(len(servant.skills.skills)):
                tokens = self.generate_tokens_for_skill(servant, skill_num)
                servant_tokens.extend(tokens)
            
            self.all_tokens.append(servant_tokens)

        self.usable_tokens = [token for sublist in self.all_tokens for token in sublist]
        print(f"Generated tokens: {[token for token in self.usable_tokens]}")  # Debugging

    def generate_tokens_for_skill(self, servant, skill_num):
        skill_tokens = [['a', 'b', 'c'], ['d', 'e', 'f'], ['g', 'h', 'i']]
        servant_index = self.game_manager.servants.index(servant)
        token = skill_tokens[servant_index][skill_num]
        skill = servant.skills.get_skill_by_num(skill_num)
        has_ptOne = any(func['funcTargetType'] == 'ptOne' for func in skill['functions'])
        
        if has_ptOne:
            return [(f"{token}{i}") for i in range(1, 4)]
        else:
            return [(token)]

    def explore_permutation(self, perm):
        self.reset_state()
        print(f"Exploring permutation: {perm}")
        for token in perm:
            
            self.execute_token(token)
            if self.is_goal_state():
                print("Goal state reached.")
                return True
            self.append_np_tokens()

        """
            # Save the current state before evaluating NP tokens
            if token in ['4', '5', '6']:
                saved_state = self.game_manager.copy()
                # Evaluate all combinations of NP tokens
                np_tokens = self.get_available_np_tokens()
                for np_combination in self.generate_combinations(np_tokens):
                    self.game_manager = saved_state.copy()
                    if self.evaluate_np_combination(np_combination):
                        return True
        """
        return False

    def generate_combinations(self, np_tokens):
        # Generate all combinations of NP tokens
        combinations = []
        for r in range(1, len(np_tokens) + 1):
            combinations.extend(itertools.permutations(np_tokens, r))
        return combinations

    def evaluate_np_combination(self, np_combination):
        #TODO useless code
        for np_token in np_combination:
            if not self.can_use_token(np_token):
                return False
            self.execute_token(np_token)
        return False

    def find_valid_permutation(self):
        self.reset_state()
        self.generate_tokens_for_positions()
        
        # Generate combinations of skill variations
        skills = {}
        for token in self.usable_tokens:
            key = token[0]
            if key in skills:
                skills[key].append(token)
            else:
                skills[key] = [token]

        # Combine the lists into a single list of lists
        combined_lists = [skills[key] for key in skills]

        # Shuffle the combined lists to introduce randomness
        for lst in combined_lists:
            random.shuffle(lst)

        # Generator function to yield permutations
        def generate_permutations(combined_lists):
            for combination in itertools.product(*combined_lists):
                for perm in itertools.permutations(combination):
                    yield perm

        # Use the generator to process permutations
        for perm in generate_permutations(combined_lists):
            if self.explore_permutation(perm):
                print(f"Valid permutation found: {perm}")
                return perm
        
        print("No valid permutation found.")
        return None

    def append_np_tokens(self):
        for i, servant in enumerate(self.game_manager.servants):
            print(f'{servant.name} has NP gauge of {servant.np_gauge}')
            if servant.np_gauge >= 100:
                self.execute_token(str(4 + i))


    def is_goal_state(self):
        # Check if the enemy's HP is reduced to 0 or below
        for enemy in self.game_manager.enemies:
            print(enemy)
            if enemy.get_hp() > 0:
                return False
        return True

    def execute_token(self, token):
        token_actions = {
            'a': lambda:  self.skill_manager.use_skill(self.game_manager.servants[0], 0),
            'a1': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 0, self.game_manager.servants[0]),
            'a2': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 0, self.game_manager.servants[1]),
            'a3': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 0, self.game_manager.servants[2]),

            'b': lambda:  self.skill_manager.use_skill(self.game_manager.servants[0], 1),
            'b1': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 1, self.game_manager.servants[0]),
            'b2': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 1, self.game_manager.servants[1]),
            'b3': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 1, self.game_manager.servants[2]),

            'c': lambda:  self.skill_manager.use_skill(self.game_manager.servants[0], 2),
            'c1': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 2, self.game_manager.servants[0]),
            'c2': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 2, self.game_manager.servants[1]),
            'c3': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 2, self.game_manager.servants[2]),
            
            'd': lambda:  self.skill_manager.use_skill(self.game_manager.servants[1], 0),
            'd1': lambda: self.skill_manager.use_skill(self.game_manager.servants[1], 0, self.game_manager.servants[0]),
            'd2': lambda: self.skill_manager.use_skill(self.game_manager.servants[1], 0, self.game_manager.servants[1]),
            'd3': lambda: self.skill_manager.use_skill(self.game_manager.servants[1], 0, self.game_manager.servants[2]),

            'e': lambda:  self.skill_manager.use_skill(self.game_manager.servants[1], 1),
            'e1': lambda: self.skill_manager.use_skill(self.game_manager.servants[1], 1, self.game_manager.servants[0]),
            'e2': lambda: self.skill_manager.use_skill(self.game_manager.servants[1], 1, self.game_manager.servants[1]),
            'e3': lambda: self.skill_manager.use_skill(self.game_manager.servants[1], 1, self.game_manager.servants[2]),
            
            'f': lambda:  self.skill_manager.use_skill(self.game_manager.servants[1], 2),
            'f1': lambda: self.skill_manager.use_skill(self.game_manager.servants[1], 2, self.game_manager.servants[0]),
            'f2': lambda: self.skill_manager.use_skill(self.game_manager.servants[1], 2, self.game_manager.servants[1]),
            'f3': lambda: self.skill_manager.use_skill(self.game_manager.servants[1], 2, self.game_manager.servants[2]),

            'g': lambda:  self.skill_manager.use_skill(self.game_manager.servants[2], 0),
            'g1': lambda: self.skill_manager.use_skill(self.game_manager.servants[2], 0, self.game_manager.servants[0]),
            'g2': lambda: self.skill_manager.use_skill(self.game_manager.servants[2], 0, self.game_manager.servants[1]),
            'g3': lambda: self.skill_manager.use_skill(self.game_manager.servants[2], 0, self.game_manager.servants[2]),
            
            'h': lambda:  self.skill_manager.use_skill(self.game_manager.servants[2], 1),
            'h1': lambda: self.skill_manager.use_skill(self.game_manager.servants[2], 1, self.game_manager.servants[0]),
            'h2': lambda: self.skill_manager.use_skill(self.game_manager.servants[2], 1, self.game_manager.servants[1]),
            'h3': lambda: self.skill_manager.use_skill(self.game_manager.servants[2], 1, self.game_manager.servants[2]),
            
            'i': lambda:  self.skill_manager.use_skill(self.game_manager.servants[2], 2),
            'i1': lambda: self.skill_manager.use_skill(self.game_manager.servants[2], 2, self.game_manager.servants[0]),
            'i2': lambda: self.skill_manager.use_skill(self.game_manager.servants[2], 2, self.game_manager.servants[1]),
            'i3': lambda: self.skill_manager.use_skill(self.game_manager.servants[2], 2, self.game_manager.servants[2]),
            
            '4': lambda:  self.np_manager.use_np(self.game_manager.servants[0]),
            '5': lambda:  self.np_manager.use_np(self.game_manager.servants[1]),
            '6': lambda:  self.np_manager.use_np(self.game_manager.servants[2]),
            '#': lambda:  self.turn_manager.end_turn(),
        }

        # action = token_actions.get(token, lambda: print(f"Unknown token: {token}"))
        action = token_actions.get(token)
        if action:
            # print(f"Executing token: {token}")
            action()
        else:
            print(f"Invalid token: {token}")

    def decrement_cooldowns(self):
        for servant in self.game_manager.servants:
            for i in range(len(servant.skills.cooldowns)):
                if servant.skills.cooldowns[i] > 0:
                    servant.skills.cooldowns[i] -= 1


# Example usage
if __name__ == '__main__':
    servant_ids = [51, 314, 314]  # List of servant IDs
    quest_id = 94086602  # Quest ID

    driver = Driver(servant_ids, quest_id)
    driver.generate_tokens_for_positions()
    driver.find_valid_permutation()

