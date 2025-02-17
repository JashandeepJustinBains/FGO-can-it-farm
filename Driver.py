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
from collections import deque
import logging
import time
import heapq

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
        self.game_manager = GameManager(servant_ids=self.servant_ids, quest_id=self.quest_id, mc_id=self.mc_id)
        self.all_tokens = []
        self.usable_tokens = self.generate_tokens_for_positions()

    def reset_state(self):
        self.game_manager = GameManager(servant_ids=self.servant_ids, quest_id=self.quest_id, mc_id=self.mc_id)
        self.turn_manager = TurnManager(game_manager=self.game_manager)
        self.skill_manager = SkillManager(turn_manager=self.turn_manager)
        self.np_manager = npManager(skill_manager=self.skill_manager)

    def generate_tokens_for_positions(self):
        self.all_tokens = []  # Initialize the list to store all tokens
        on_field = self.game_manager.servants[0:3]
        for i, servant in enumerate(on_field):
            servant_tokens = []
            for skill_num, skill in enumerate(servant.skills.skills):
                tokens = self.generate_tokens_for_skill(servant, skill)
                servant_tokens.extend(tokens)
            self.all_tokens.append(servant_tokens)

        # Add Mystic Code Tokens
        mystic_code = self.game_manager.mc
        mystic_code_tokens = []
        for skill_num in range(len(mystic_code.skills)):
            tokens = self.generate_tokens_for_mystic_code(mystic_code, skill_num)
            mystic_code_tokens.extend(tokens)
        self.all_tokens.append(mystic_code_tokens)

        # Create multiple instances of each token
        self.all_tokens.append('#')
        self.all_tokens.append('#')
        self.all_tokens.append('#')
        self.usable_tokens = [token for sublist in self.all_tokens for token in sublist for _ in range(2)]

        return self.usable_tokens

    def generate_tokens_for_skill(self, servant, skill_num):
        skill_tokens = [['a', 'b', 'c'], ['d', 'e', 'f'], ['g', 'h', 'i']]
        servant_index = self.game_manager.servants.index(servant)
         # skill_num is '1:' '2:' or '3:' so just subtract 1 instead of adding a new parameter
        token = skill_tokens[servant_index][skill_num-1]
        skill = servant.skills.get_skill_by_num(skill_num)
        has_ptOne = any(func['funcTargetType'] == 'ptOne' for func in skill['functions'])

        if has_ptOne:
            return [(f"{token}{i}") for i in range(1, 4)]
        else:
            return [token]

    def generate_tokens_for_mystic_code(self, mystic_code, skill_num):
        if self.mc_id == 260 or self.mc_id == 20:
            skill_tokens = [['j', 'k', 'x']]  # Adjust according to the condition
        else:
            skill_tokens = [['j', 'k', 'l']]
        token = skill_tokens[0][skill_num]  # Use the first (and only) sub-array
        skill = mystic_code.skills[skill_num]

        has_ptOne = any(func['funcTargetType'] == 'ptOne' for func in skill['functions'])
        has_orderChange = any(func['funcTargetType'] == 'positionalSwap' for func in skill['functions'])

        if has_ptOne:
            return [(f"{token}{i}") for i in range(1, 4)]
        elif has_orderChange:
            return [f"{token}_swap_{i}{j}" for i in range(1, 4) for j in range(1, 4)]
        else:
            return [token]


    def decrement_cooldowns(self):
        for servant in self.game_manager.servants:
            for i in range(len(servant.skills.cooldowns)):
                if servant.skills.cooldowns[i] > 0:
                    servant.skills.cooldowns[i] -= 1

    def save_tree_to_json(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.root.to_dict(), f, indent=4)

    # heuristic for randomized permutation scoring
    def evaluate_permutation(self, perm):
        self.used_tokens = []  # Track used tokens in current permutation
        total_score = 0

        logging.info(f"\n ATTEMPTING TO RUN PERMUTATION:\n {perm}")
        print(f"\n ATTEMPTING TO RUN PERMUTATION:\n {perm}")

        for token in perm:
            if not self.execute_token(token):
                break
            # Evaluate the current state (e.g., check if a wave is cleared, calculate damage)
            total_score += self.turn_manager.get_score()

        return total_score



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
            'x'  : lambda: self.skill_manager.swap_servants(),
            
            # NPs
            '4': lambda:  self.np_manager.use_np(self.game_manager.servants[0]),
            '5': lambda:  self.np_manager.use_np(self.game_manager.servants[1]),
            '6': lambda:  self.np_manager.use_np(self.game_manager.servants[2]),
            '#': lambda:  self.turn_manager.end_turn(),
        }

        self.used_tokens.append(token)
        action = token_actions.get(token)
        if action:
            print(f"Executing TOKEN: {token}")
            logging.info(f"Executing TOKEN: {token}")
            retval = action()
            if retval is False:
                logging.info(f"bad token permutation: {self.used_tokens}")
                return False
        else:
            logging.info(f"Invalid token: {token}")
        return True


if __name__ == '__main__':
    servant_ids = [413, 414, 284, 284, 316]  # Aoko Soujurou castoria oberon castoria
    quest_id = 94095710  # witch on the holy night 90+



    print(f"Simulations completed. Results saved to 'simulation_results.json'.")



# TODO
#   Need to seperate running the program using the "randomized token list" because it appears to not reset the 
#       skill cooldowns correctly. 
#   if we instead run the entire program again it will have a fresh set to use.

# TODO
#   create assumptions for speresh's changing damage multiplier maybe Turn 1: 1.3, Turn 2: 1.4, Turn 3: 1.6?
#   program kazuradrop's class change to chose the highest HP target on the turn that the skill is used similar to how twink swordsperson's np is programmed
#   incorporate "chosable" skills, such as DuBBai's np change, space ishtar, etc
