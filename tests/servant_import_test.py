import unittest
from units.Servant import Servant

class servant_import(unittest.TestCase):

    def servant_import(self):
        # Initialize the Driver with known servants and quest_id
        servant = Servant(collectionNo=400)

        # Check if the goal state is achieved
        self.assertTrue(servant.name == "Uesugi Kenshin")

if __name__ == '__main__':
    unittest.main()
