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

import logging

# Configure logging
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class Driver:
    def __init__(self, servant_ids, quest_id, mc_id=260):
        self.servant_ids = servant_ids
        self.quest_id = quest_id
        self.mc_id = mc_id
        self.turn_manager = None
        self.skill_manager = None
        self.np_manager = None
        self.game_manager = GameManager(self.servant_ids, self.quest_id, self.mc_id)
        self.all_tokens = []
        self.usable_tokens = []  # Track currently usable tokens
        self.used_tokens = []

    def reset_state(self):
        self.game_manager = GameManager(self.servant_ids, self.quest_id, self.mc_id)
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

        # Add Mystic Code Tokens
        mystic_code = self.game_manager.mc
        mystic_code_tokens = []
        for skill_num in range(len(mystic_code.skills)):
            tokens = self.generate_tokens_for_mystic_code(mystic_code, skill_num)
            mystic_code_tokens.extend(tokens)
        self.all_tokens.append(mystic_code_tokens)

        self.usable_tokens = [token for sublist in self.all_tokens for token in sublist]
        logging.info(f"Generated tokens: {self.usable_tokens}")  # Debugging

    def generate_tokens_for_skill(self, servant, skill_num):
        skill_tokens = [['a', 'b', 'c'], ['d', 'e', 'f'], ['g', 'h', 'i']]
        servant_index = self.game_manager.servants.index(servant)
        token = skill_tokens[servant_index][skill_num]
        skill = servant.skills.get_skill_by_num(skill_num)
        has_ptOne = any(func['funcTargetType'] == 'ptOne' for func in skill['functions'])

        if has_ptOne:
            return [(f"{token}{i}") for i in range(1, 5)]
        else:
            return [token] * 4

    def generate_tokens_for_mystic_code(self, mystic_code, skill_num):
        if self.mc_id == 260 or self.mc_id == 20:
            skill_tokens = [['j', 'k', 'x']]  # Adjust according to the condition
        else:
            skill_tokens = [['j', 'k', 'l']]
        token = skill_tokens[0][skill_num]  # Use the first (and only) sub-array
        skill = mystic_code.skills[skill_num]

        has_ptOne = any(func['funcTargetType'] == 'ptOne' for func in skill['functions'])
        has_ptAll = any(func['funcTargetType'] == 'ptAll' for func in skill['functions'])
        has_orderChange = any(func['funcTargetType'] == 'positionalSwap' for func in skill['functions'])

        if has_ptOne:
            return [(f"{token}{i}") for i in range(1, 5)]
        elif has_ptAll:
            return [token] * 4
        elif has_orderChange:
            return [f"{token}_swap_{i}{j}" for i in range(1, 4) for j in range(1, 4)]
        else:
            return [token] * 4

    def find_valid_permutation(self):
        self.reset_state()
        self.generate_tokens_for_positions()

        # Generate all possible permutations of tokens
        permutations = list(itertools.permutations(self.usable_tokens))
        random.shuffle(permutations)

        # Split into smaller chunks and save to files
        chunk_size = 1000  # Or any other manageable size
        chunk_files = []
        for i in range(0, len(permutations), chunk_size):
            chunk = permutations[i:i + chunk_size]
            filename = f"permutations_chunk_{i // chunk_size}.txt"
            chunk_files.append(filename)
            with open(filename, 'w') as f:
                for perm in chunk:
                    f.write(f"{','.join(perm)}\n")

        # Process each chunk file
        for chunk_file in chunk_files:
            with open(chunk_file, 'r') as f:
                for line in f:
                    perm = tuple(line.strip().split(','))
                    if self.explore_permutation(perm):
                        print(f"Valid permutation found: {perm}")
                        return perm

        print("No valid permutation found.")
        return None

    def explore_permutation(self, perm):
        self.reset_state()
        logging.info(f"Exploring permutation: {perm}")
        self.used_tokens = []  # Track used tokens in current permutation
        for token in perm:
            self.used_tokens.append(token)
            if not self.execute_token(token):
                logging.info(f"Invalid permutation: {self.used_tokens}")
                return False
        return True


    def execute_token(self, token):
        token_actions = {
            # servant 1 skills
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
            
            # servant 2 skills
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

            # servant 3 skills
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

            # mystic codes
            'j': lambda:  self.skill_manager.use_mystic_code_skill(0),
            'j1': lambda: self.skill_manager.use_mystic_code_skill(0, self.game_manager.servants[0]),
            'j2': lambda: self.skill_manager.use_mystic_code_skill(0, self.game_manager.servants[1]),
            'j3': lambda: self.skill_manager.use_mystic_code_skill(0, self.game_manager.servants[2]),

            'k': lambda:  self.skill_manager.use_mystic_code_skill(1),
            'k1': lambda: self.skill_manager.use_mystic_code_skill(1, self.game_manager.servants[0]),
            'k2': lambda: self.skill_manager.use_mystic_code_skill(1, self.game_manager.servants[1]),
            'k3': lambda: self.skill_manager.use_mystic_code_skill(1, self.game_manager.servants[2]),

            'l': lambda:  self.skill_manager.use_mystic_code_skill(2),
            'l1': lambda: self.skill_manager.use_mystic_code_skill(2, self.game_manager.servants[0]),
            'l2': lambda: self.skill_manager.use_mystic_code_skill(2, self.game_manager.servants[1]),
            'l3': lambda: self.skill_manager.use_mystic_code_skill(2, self.game_manager.servants[2]),

            'x11': lambda: self.skill_manager.swap_servants(1,1),
            'x12': lambda: self.skill_manager.swap_servants(1,2),
            'x13': lambda: self.skill_manager.swap_servants(1,3),
            'x21': lambda: self.skill_manager.swap_servants(2,1),
            'x22': lambda: self.skill_manager.swap_servants(2,2),
            'x23': lambda: self.skill_manager.swap_servants(2,3),
            'x31': lambda: self.skill_manager.swap_servants(3,1),
            'x32': lambda: self.skill_manager.swap_servants(3,2),
            'x33': lambda: self.skill_manager.swap_servants(3,3),
            
            # NPs
            '4': lambda:  self.np_manager.use_np(self.game_manager.servants[0]),
            '5': lambda:  self.np_manager.use_np(self.game_manager.servants[1]),
            '6': lambda:  self.np_manager.use_np(self.game_manager.servants[2]),
            '#': lambda:  self.turn_manager.end_turn(),
        }

        # action = token_actions.get(token, lambda: print(f"Unknown token: {token}"))
        self.used_tokens.append(token)
        action = token_actions.get(token)
        if action:
            logging.info(f"Executing TOKEN: {token}")
            retval = action()
            if retval == False:
                logging.info(f"bad token permutation: {self.used_tokens}")
                return False
        else:
            logging.info(f"Invalid token: {token}")

    def decrement_cooldowns(self):
        for servant in self.game_manager.servants:
            for i in range(len(servant.skills.cooldowns)):
                if servant.skills.cooldowns[i] > 0:
                    servant.skills.cooldowns[i] -= 1


# Example usage
if __name__ == '__main__':
    # to check ordeal call quests use this link https://apps.atlasacademy.io/db/JP/war/401


    