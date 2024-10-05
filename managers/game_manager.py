from .Quest import Quest
from units.Servant import Servant
import copy

class GameManager:
    def __init__(self, servant_ids, quest_id, gm_copy=None):
        if gm_copy:
            self.__dict__ = copy.deepcopy(gm_copy.__dict__)          
        else:
            self.servant_ids = servant_ids
            self.quest_id = quest_id
            self.enemies = []
            self.servants = [Servant(collectionNo=servant_id) for servant_id in servant_ids]
            self.fields = []
            self.quest = Quest(self.quest_id)  # Initialize the Quest instance
            self.wave = 1

    def add_field(self, state):
        name = state.get('field_name', 'Unknown')
        turns = state.get('turns', 0)
        self.fields.append([name, turns])

    def reset(self):
        self.enemies = self.quest.get_wave(self.wave)
        self.servants = [Servant(collectionNo=servant_id) for servant_id in self.servant_ids]
        self.fields = []

    def copy(self):
        return GameManager(self.servant_ids, self.quest_id, gm_copy=self)