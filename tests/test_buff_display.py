import unittest
from units.buffs import Buffs

class DummyServant:
    def __init__(self):
        self.name = 'TestServant'
        self.fields = []
        self.set_npgauge_called = False
        self.kill = False
        self.user_atk_mod = 0
        self.user_b_up = 0
        self.user_a_up = 0
        self.user_q_up = 0
        self.user_damage_mod = 0
        self.user_np_damage_mod = 0
        self.user_buster_damage_up = 0
        self.user_arts_damage_up = 0
        self.user_quick_damage_up = 0
        self.atk_mod = 0
        self.b_up = 0
        self.a_up = 0
        self.q_up = 0
        self.power_mod = {}
        self.np_damage_mod = 0
        self.oc_level = 1
        self.np_gain_mod = 1
        self.buster_card_damage_up = 0
        self.arts_card_damage_up = 0
        self.quick_card_damage_up = 0
        self.np_gauge = 0
        self.star_count = 0
    def set_npgauge(self, value):
        self.set_npgauge_called = True
        self.np_gauge += value

class TestBuffsDisplay(unittest.TestCase):
    def test_buff_display_fgo_accurate(self):
        buffs = Buffs(servant=DummyServant())
        # Add skill buff
        buffs.add_buff({'buff': 'ATK Up', 'value': 200, 'turns': 3, 'source': 'skill'})
        # Add passive buff
        buffs.add_buff({'buff': 'ATK Up', 'value': 20, 'turns': -1, 'source': 'passive', 'is_passive': True})
        # Add user-inputted buff (value 0, permanent)
        buffs.add_buff({'buff': 'Arts Up', 'value': 0, 'turns': -1, 'source': 'user', 'user_input': True})
        # Add another skill buff, same value/duration as first
        buffs.add_buff({'buff': 'ATK Up', 'value': 200, 'turns': 3, 'source': 'skill'})
        # Add a temporary buff with value 0 (should not show unless user/passive)
        buffs.add_buff({'buff': 'Buster Up', 'value': 0, 'turns': 2, 'source': 'skill'})
        # Add a critical strength up buff
        buffs.add_buff({'buff': 'Critical Strength Up', 'value': 250, 'turns': 3, 'source': 'skill'})
        # Display
        output = buffs.grouped_str()
        print(output)
        # Check that all buffs are present and formatted correctly
        self.assertIn('ATK Up: {value=0.200, turns=3, source=skill}', output)
        self.assertIn('ATK Up: {value=0.020, turns=-1, source=passive}', output)
        self.assertIn('Arts Up: {value=0, turns=-1, source=user}', output)
        self.assertIn('ATK Up: {value=0.200, turns=3, source=skill}', output)
        self.assertIn('Critical Strength Up: {value=0.250, turns=3, source=skill}', output)
        # Buster Up with value 0 and not user/passive/permanent should not show
        self.assertNotIn('Buster Up: {value=0, turns=2, source=skill}', output)

if __name__ == '__main__':
    unittest.main()
