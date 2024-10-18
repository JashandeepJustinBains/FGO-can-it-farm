from units.Enemy import Enemy
from connectDB import db
import numpy as np

class Quest:
    def __init__(self, quest_id):
        self.db = db
        self.quest_id = quest_id
        self.fields = []
        self.waves = {}
        self.total_waves = 0
        self.current_wave_index = 1  # Initialize wave index to 1
        self.retrieve_quest()

    def retrieve_quest(self):
        query = {"id": self.quest_id}
        document = self.db.quests.find_one(query)
        if document:
            self.process_quest(document)

    def process_quest(self, document):
        waves = document['stages']
        for field in document['individuality']:
            self.fields.append(field['id'])
        for i, wave in enumerate(waves):
            wave_data = []  # Initialize wave_data here
            for enemy in wave['enemies']:
                enemydata = [
                    enemy['name'],
                    enemy['hp'],
                    enemy['svt']['className'],
                    [trait['id'] for trait in enemy['svt']['traits']],
                    enemy['svt']['attribute'],
                    enemy['state'] if 'state' in enemy else None
                ]
                wave_data.append(Enemy(enemydata))
            self.waves[i + 1] = wave_data
        self.total_waves = len(self.waves)

    def get_wave(self, wave_no=0):
        if wave_no == 0:
            return self.waves
        return self.waves.get(wave_no, [])
