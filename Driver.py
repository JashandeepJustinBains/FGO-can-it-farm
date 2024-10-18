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
    def __init__(self, servant_ids, quest_id, mc_id):
        self.servant_ids = servant_ids
        self.quest_id = quest_id
        self.mc_id = mc_id
        self.turn_manager = None
        self.skill_manager = None
        self.np_manager = None
        self.game_manager = GameManager(self.servant_ids, self.quest_id, self.mc_id)
        self.permutations_file = "test_permutations.json"
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
        print(f"Generated tokens: {self.usable_tokens}")  # Debugging



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

    def append_np_tokens(self):
        for i, servant in enumerate(self.game_manager.servants):
            print(f'{servant.name} has NP gauge of {servant.np_gauge}')
            if servant.np_gauge >= 100:
                self.execute_token(str(4 + i))

    def regenerate_tokens_based_on_cooldowns(self):
        self.all_tokens = []  # Reinitialize the list to store all tokens
        on_field = self.game_manager.servants[0:3]
        for i, servant in enumerate(on_field):
            servant_tokens = []
            for skill_num in range(len(servant.skills.skills)):
                if servant.skills.skill_available(skill_num):
                    tokens = self.generate_tokens_for_skill(servant, skill_num)
                    servant_tokens.extend(tokens)
            self.all_tokens.append(servant_tokens)
        self.usable_tokens = [token for sublist in self.all_tokens for token in sublist]
        print(f"Regenerated tokens: {[token for token in self.usable_tokens]}")  # Debugging

    def explore_permutation(self, perm):
        self.reset_state()
        print(f"Exploring permutation: {perm}")
        self.used_tokens = []  # Track used tokens in current permutation
        for token in perm:
            self.used_tokens.append(token)
            if self.execute_token(token) == False:
                print(f"Invalid permutation: {self.used_tokens}")
                return False
            if self.is_goal_state():
                print("Goal state reached.")
                return True
            self.append_np_tokens()
            self.regenerate_tokens_based_on_cooldowns()
        return False


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
            print(f"Executing token: {token}")
            retval = action()
            if retval == False:
                print(f"bad token permutation: {self.used_tokens}")
                return False
        else:
            print(f"Invalid token: {token}")

    def decrement_cooldowns(self):
        for servant in self.game_manager.servants:
            for i in range(len(servant.skills.cooldowns)):
                if servant.skills.cooldowns[i] > 0:
                    servant.skills.cooldowns[i] -= 1


# Example usage
if __name__ == '__main__':
    # servant_ids = [51, 314, 314]  # List of servant IDs
    # quest_id = 94086602  # Quest ID

    # driver = Driver(servant_ids=servant_ids, quest_id=quest_id)
    # driver.reset_state()

    # print(f"{driver.game_manager.enemies}")

    # driver.generate_tokens_for_positions()
    # driver.find_valid_permutation()

    quest_id = 94054911  # Quest ID

    # test: Does the following token string correctly defeat the enemy?
    driver = Driver(servant_ids=[51, 314, 314, 316], quest_id=94086602, mc_id=260)
    driver.reset_state()
    # driver.generate_tokens_for_positions()
    # Define the tokens to be used in the battle
    tokens = ["a","b","c","d1","e1","f1","g1","h1","i1","a", "x31", "g", "h1", "i1", "j", "4", "#"]
    for token in tokens:
        driver.execute_token(token)

    
    """
    # test: Servant is correctly initialized 
    # servant = Servant(collectionNo=400)
    # print(f"is this servant Uesugi Kenshin? {servant.name == "Uesugi Kenshin"}")
    """

    """
    # test: Quest correctly instantiates correct enemy data
    # quest = Quest(94086602)
    # wave = quest.get_wave()
    # print(f"printing wave :{wave}")
    # for enemy in wave:
    #     print(wave[enemy])
    """
 
