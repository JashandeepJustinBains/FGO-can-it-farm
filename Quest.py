from Enemy import Enemy
from connectDB import db
from pprint import pprint
import numpy as np

# Define the Quest class
class Quest:
    def __init__(self, quest_id):
        self.db = db
        self.quest_id = quest_id
        self.fields = []
        self.waves = []
        self.retrieve_quest()

    def retrieve_quest(self):
        query = { "id": self.quest_id }
        document = self.db.quests.find_one(query)
        if document:
            self.process_quest(document)

    def process_quest(self, document):
        waves = document['stages']
        for field in document['individuality']:
            self.fields.append(field['id'])
        for i, wave in enumerate(waves): 
            for enemy in wave['enemies']:
                enemydata = [
                    enemy['name'],
                    enemy['hp'],
                    enemy['svt']['className'],
                    [trait['id'] for trait in enemy['svt']['traits']],
                    enemy['svt']['attribute'],
                    enemy['state'] if 'state' in enemy else None
                ]
                wave_data = []
                wave_data.append(Enemy(enemydata))
            self.waves.append(wave_data)

    def pretty_print_waves(self):
        for wave, enemies in enumerate(self.waves):
            print(f"field:{self.fields} Wave {wave}:")
            headers = ["Name", "HP", "Class", "Traits", "Attribute"]
            data = [[enemy.get_name(), enemy.get_hp(), enemy.get_class(), ", ".join(map(str, enemy.get_traits())), enemy.attribute] for enemy in enemies]
            table = np.array([headers] + data)
            for row in table:
                print(" | ".join(map(str, row)))
        print("\n")

    def get_wave(self, wave_no=1):
        print(self.waves)