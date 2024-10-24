from .Quest import Quest
from units.Servant import Servant
from .MysticCode import MysticCode
import copy

class GameManager:
    def __init__(self, servant_ids, quest_id, mc_id, gm_copy=None):
        if gm_copy:
            self.__dict__ = copy.deepcopy(gm_copy.__dict__)
        else:
            self.servant_ids = servant_ids
            self.quest_id = quest_id
            self.mc_id = mc_id
            self.servants = [Servant(collectionNo=servant_id) for servant_id in servant_ids]
            self.mc = MysticCode(mc_id)
            self.fields = []
            self.quest = None  # Initialize the Quest instance
            self.wave = 1
            self.total_waves = 0
            self.enemies = []
            self.init_quest()
            if 413 in servant_ids:
                self.saoko = Servant(collectionNo=4132)

    def add_field(self, state):
        name = state.get('field_name', 'Unknown')
        turns = state.get('turns', 0)
        self.fields.append([name, turns])

    def reset(self):
        self.servants = [Servant(collectionNo=servant_id) for servant_id in self.servant_ids]
        self.fields = []

    def swap_servants(self, frontline_idx, backline_idx):
        self.servants[frontline_idx], self.servants[backline_idx] = self.servants[backline_idx], self.servants[frontline_idx]

    def transform_aoko(self):
        print("What? \nAoko is transforming!")
        for i, servant in enumerate(self.servants):
            if servant.id == 413:
                self.saoko.buffs = servant.buffs
                self.saoko.skills.cooldowns = servant.skills.cooldowns
                self.servants[i] = self.saoko
                self.servants[i].set_npgauge(0)
                print(f"Contratulations! Your 'Aoko Aozaki' transformed into '{self.servants[i].name}' ")
            
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

    def copy(self):
        return GameManager(self.servant_ids, self.quest_id, gm_copy=self)
