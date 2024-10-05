import unittest
from Driver import Driver

class TestDriverFunctional(unittest.TestCase):

    def test_battle_with_tokens(self):
        # Initialize the Driver with known servants and quest_id
        driver = Driver(servant_ids=[51, 314, 314], quest_id=94086602)
        driver.reset_state()

        # Define the tokens to be used in the battle
        tokens = ["a","b","c","d1","e1","f1","g1","h1","i1","a", "4", "#"]

        # Execute each token
        for token in tokens:
            driver.execute_token(token)

        # Check if the goal state is achieved
        self.assertTrue(driver.is_goal_state())

if __name__ == '__main__':
    unittest.main()
