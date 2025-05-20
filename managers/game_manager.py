from .Quest import Quest
from units.Servant import Servant
from .MysticCode import MysticCode
import copy
import logging

# Configure logging
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class GameManager:
    def __init__(self, servant_init_dicts, quest_id, mc_id, gm_copy=None):
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

