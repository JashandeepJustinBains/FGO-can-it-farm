Here is my code for the Driver class of my program that is responsible for setting up the simualtion as well as going through each permutation to see if it yields a valid string of tokens that can complete the wave. My initial idea is to include 3 copies of each token so that we do not need to add any additional code for managing "generating" new tokens when a skill comes off cooldown. I am assuming that a skill will be used at most once per wave of the battle and atmost 3 NPs aswell because there are only 3 waves/turns in the battles I am interested in. I know it will be inneficient but I have some pruning and randomly selecting the next pemrutaiton to use so that the pruning may be more efficient in finding bad outcomes and ensuring token strings that begin with the same prefix will not be executed. How can I implement that? 

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
    def __init__(self, servant_ids, quest_id, mc_id):
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
        # TODO MAKE 4 COPIES OF EACH SKILL TOKEN EVEN THOUGH IT IS INNEFFICIENT
        if has_ptOne:
            return [(f"{token}{i}") for i in range(1, 4)]
        else:
            return [(token)]

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
            return [(f"{token}{i}") for i in range(1, 4)]
        elif has_ptAll:
            return [(f"{token}")]
        elif has_orderChange:
            return [(f"{token}_swap_x31")]
        else:
            return [(token)]


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

    def explore_permutation(self, perm):
        self.reset_state()
        logging.info(f"Exploring permutation: {perm}")
        self.used_tokens = []  # Track used tokens in current permutation
        for token in perm:
            self.used_tokens.append(token)
            if self.execute_token(token) == False:
                logging.info(f"Invalid permutation: {self.used_tokens}")
                return False
            
        return False


    def execute_token(self, token):
        token_actions = {
            # servant 1 skills
            'a': lambda:  self.skill_manager.use_skill(self.game_manager.servants[0], 0),
            'a1': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 0, self.game_manager.servants[0]),
            'a2': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 0, self.game_manager.servants[1]),
            'a3': lambda: self.skill_manager.use_skill(self.game_manager.servants[0], 0, self.game_manager.servants[2]),
            ...
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


    quest_id = 94095710 # witch on the holy night 90+
    driver = Driver(servant_ids=servant_ids, quest_id=quest_id, mc_id=260)
    driver.reset_state()
    # a b c
    # d e f
    # g h i
    # j k l or j k x{servant123}{servant123}

    
