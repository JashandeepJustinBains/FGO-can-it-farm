import unittest
from managers.Quest import Quest

class quest_enemy_test(unittest.TestCase):

    def import_enemy_exist(self):
        # first create Quest
        quest = Quest(94086602)
        wave = quest.get_wave()
        for enemy in wave:
            self.assertTrue(enemy.name == "")

if __name__ == '__main__':
    unittest.main()
