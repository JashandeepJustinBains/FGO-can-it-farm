from units.Enemy import Enemy
from scripts.connectDB import db
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
        if self.db is not None:
            document = self.db.quests.find_one(query)
            if document:
                self.process_quest(document)
                return
        
        # Fallback to basic quest for offline mode
        basic_quest = {
            'id': self.quest_id,
            'individuality': [],
            'stages': [
                {
                    'enemies': [
                        {'name': 'Enemy 1', 'hp': 10000, 'deathRate': 100, 'svt': {'className': 'saber', 'traits': [], 'attribute': 'man'}, 'state': None},
                        {'name': 'Enemy 2', 'hp': 15000, 'deathRate': 100, 'svt': {'className': 'archer', 'traits': [], 'attribute': 'man'}, 'state': None},
                        {'name': 'Enemy 3', 'hp': 20000, 'deathRate': 100, 'svt': {'className': 'lancer', 'traits': [], 'attribute': 'man'}, 'state': None}
                    ]
                },
                {
                    'enemies': [
                        {'name': 'Enemy 4', 'hp': 25000, 'deathRate': 100, 'svt': {'className': 'rider', 'traits': [], 'attribute': 'man'}, 'state': None},
                        {'name': 'Enemy 5', 'hp': 30000, 'deathRate': 100, 'svt': {'className': 'caster', 'traits': [], 'attribute': 'man'}, 'state': None},
                    ]
                },
                {
                    'enemies': [
                        {'name': 'Boss', 'hp': 100000, 'deathRate': 100, 'svt': {'className': 'berserker', 'traits': [], 'attribute': 'man'}, 'state': None}
                    ]
                }
            ]
        }
        self.process_quest(basic_quest)

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
                    enemy['deathRate'],
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
