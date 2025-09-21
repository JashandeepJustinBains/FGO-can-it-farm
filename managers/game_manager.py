from .Quest import Quest
from units.Servant import Servant
from .MysticCode import MysticCode
import copy
import logging

# Configure logging
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class GameManager:
    def __init__(self, servant_init_dicts, quest_id, mc_id):
        self.servant_init_dicts = servant_init_dicts  # List of dicts
        self.quest_id = quest_id
        self.mc_id = mc_id
        self.servants = [Servant(**params) for params in self.servant_init_dicts]
        self.mc = MysticCode(mc_id)
        self.fields = []
        self.quest = None  # Initialize the Quest instance
        self.wave = 1
        self.total_waves = 0
        self.enemies = []
        self.init_quest()
        if any(servant['collectionNo'] == 413 for servant in servant_init_dicts):
            # TODO if aoko is in the team init her super form with 
            #   Servant(**params) for params in self.servant_init_dicts for aoko's params only
            self.saoko = Servant(collectionNo=4132)

    def reset_servants(self):
        self.servants = [Servant(**params) for params in self.servant_init_dicts]

    def add_field(self, state):
        name = state.get('field_name', 'Unknown')
        turns = state.get('turns', 0)
        self.fields.append([name, turns])

    def reset(self):
        self.reset_servants()
        self.fields = []

    def swap_servants(self, frontline_idx, backline_idx):
        self.servants[frontline_idx], self.servants[backline_idx] = self.servants[backline_idx], self.servants[frontline_idx]

    # TODO part of the transformation refactoring mega todo
    def transform_aoko(self, aoko_buffs, aoko_cooldowns, aoko_np_gauge=None):
        print("What? \nAoko is transforming!")
        servants_list = [servant.name for servant in self.servants]
        logging.info(f"servants are: {servants_list}")
        for i, servant in enumerate(self.servants):
            if servant.id == 413:
                # Create a fresh transformed Aoko instance
                transformed = Servant(collectionNo=4132)
                # Copy buffs, cooldowns, and optionally NP gauge
                transformed.buffs.buffs = copy.deepcopy(aoko_buffs)
                transformed.skills.cooldowns = copy.deepcopy(aoko_cooldowns)
                if aoko_np_gauge is not None:
                    transformed.np_gauge = aoko_np_gauge
                # Replace in the party
                self.servants[i] = transformed
                print(f"Contratulations! Your 'Aoko Aozaki' transformed into '{transformed.name}' ")
        servants_list = [servant.name for servant in self.servants]
        logging.info(f"servants are: {servants_list}")
    
    def init_quest(self):
        self.quest = Quest(self.quest_id)
        self.total_waves = self.quest.total_waves
        self.enemies = self.quest.get_wave(self.wave)  # Set the initial wave enemies

    def get_next_wave(self):
        try:
            self.wave += 1
            next_wave = self.quest.get_wave(self.wave)  # Fetch the next wave
            self.enemies = next_wave  # Update self.enemies with the new wave
            print(f"Advancing to wave {self.wave}")  # Debug statement
        except StopIteration:
            print("All waves completed. Ending program.")
            exit(0)  # Ends the program
        return 

    def get_enemies(self):
        return self.enemies
    
    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove database connection if present
        if 'mc' in state and hasattr(state['mc'], '__dict__'):
            mc_state = state['mc'].__dict__.copy()
            if 'db' in mc_state:
                mc_state['db'] = None
            state['mc'].__dict__ = mc_state
        if 'quest' in state and hasattr(state['quest'], '__dict__'):
            quest_state = state['quest'].__dict__.copy()
            if 'db' in quest_state:
                quest_state['db'] = None
            state['quest'].__dict__ = quest_state
        return state

    def __repr__(self):
        """
        Human-readable team representation showing each servant slot with:
        - Collection number and ascension 
        - Noble Phantasm name and card type
        - Skills with names and cooldowns
        - Transform flags or notes
        """
        lines = []
        for i, servant in enumerate(self.servants, 1):
            # Basic servant info
            slot_line = f"Slot {i}: #{servant.id} {servant.name} (asc {servant.ascension})"
            
            # NP info
            if hasattr(servant, 'nps') and servant.nps and servant.nps.nps:
                np = servant.nps.nps[0]  # Use first/main NP
                np_name = np.get('name', 'Unknown NP')
                np_card = np.get('card', 'unknown')
                slot_line += f" | NP: {np_name} ({np_card})"
            else:
                slot_line += " | NP: None"
            
            # Skills info
            skills_info = []
            if hasattr(servant, 'skills') and servant.skills:
                for skill_num in [1, 2, 3]:
                    try:
                        skill = servant.skills.get_skill_by_num(skill_num - 1)  # 0-indexed
                        skill_name = skill.get('name', f'Skill {skill_num}')
                        cooldown = servant.skills.cooldowns.get(skill_num, 0)
                        max_cd = servant.skills.max_cooldowns.get(skill_num, 0)
                        cd_display = cooldown if cooldown > 0 else max_cd
                        skills_info.append(f"{skill_name} (CD {cd_display})")
                    except (IndexError, KeyError):
                        skills_info.append(f"Skill {skill_num} (unavailable)")
            
            if skills_info:
                slot_line += f" | Skills: {', '.join(skills_info)}"
            else:
                slot_line += " | Skills: None"
            
            # Transform info
            transform_info = "none"
            if servant.id == 413:  # Aoko
                transform_info = "transforms->4132 on first NP use"
            elif servant.id == 4132:  # Super Aoko
                transform_info = "transformed from 413"
            
            slot_line += f" | transforms: {transform_info}"
            
            lines.append(slot_line)
        
        return "\n".join(lines)

