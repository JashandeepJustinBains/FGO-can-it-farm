"""
Tests for ascension-aware skill and NP selection.

This test suite validates that servants correctly select skills and NPs 
based on their current ascension level, ensuring proper release condition 
checking and priority handling.
"""

import unittest
import os
import sys

# Add repo root to path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from units.Servant import Servant
from tools.per_ascension_diag import enhanced_diag_servant


class TestAscensionSelection(unittest.TestCase):
    """Test ascension-aware skill and NP selection for canonical servants."""

    def test_mash_ascension_skills(self):
        """Test Mash (collectionNo 1) skill selection across ascensions."""
        # Ascension 1 should have basic skills
        mash_asc1 = Servant(1, ascension=1)
        skill1_asc1 = mash_asc1.skills.get_skill_by_num(1)
        self.assertEqual(skill1_asc1['id'], 1000, "Mash ascension 1 should have basic skill 1 (id=1000)")
        
        # Ascension 2+ should have upgraded skills  
        mash_asc2 = Servant(1, ascension=2)
        skill1_asc2 = mash_asc2.skills.get_skill_by_num(1)
        self.assertEqual(skill1_asc2['id'], 459550, "Mash ascension 2+ should have upgraded skill 1 (id=459550)")

    def test_uolga_marie_ascension_skills(self):
        """Test U-Olga Marie (collectionNo 444) skill selection across ascensions."""
        # Ascensions 1-2 should have priority 1 skills
        olga_asc1 = Servant(444, ascension=1)
        skill1_asc1 = olga_asc1.skills.get_skill_by_num(1)
        self.assertEqual(skill1_asc1['id'], 2516650, "U-Olga Marie ascension 1 should have priority 1 skill (id=2516650)")
        
        olga_asc2 = Servant(444, ascension=2)
        skill1_asc2 = olga_asc2.skills.get_skill_by_num(1)
        self.assertEqual(skill1_asc2['id'], 2516650, "U-Olga Marie ascension 2 should have priority 1 skill (id=2516650)")
        
        # Ascension 3+ should have priority 2 skills (with condNum=3 requirement)
        olga_asc3 = Servant(444, ascension=3)
        skill1_asc3 = olga_asc3.skills.get_skill_by_num(1)
        self.assertEqual(skill1_asc3['id'], 2512650, "U-Olga Marie ascension 3+ should have priority 2 skill (id=2512650)")

    def test_servant_construction_no_errors(self):
        """Test that servant construction doesn't crash for canonical examples."""
        test_servants = [1, 444]  # Mash, U-Olga Marie
        
        for servant_id in test_servants:
            with self.subTest(servant_id=servant_id):
                for ascension in [1, 2, 3, 4]:
                    with self.subTest(ascension=ascension):
                        try:
                            servant = Servant(servant_id, ascension=ascension)
                            # Basic validation
                            self.assertIsNotNone(servant.name, f"Servant {servant_id} ascension {ascension} should have a name")
                            self.assertEqual(servant.ascension, ascension, f"Servant ascension should match input")
                            
                            # Should have skills for all 3 slots
                            for slot in [1, 2, 3]:
                                skill = servant.skills.get_skill_by_num(slot)
                                self.assertIsNotNone(skill, f"Servant {servant_id} ascension {ascension} should have skill in slot {slot}")
                                self.assertIn('id', skill, f"Skill should have an id")
                                
                        except Exception as e:
                            self.fail(f"Servant {servant_id} ascension {ascension} construction failed: {e}")


class TestDiagnosticSweep(unittest.TestCase):
    """Sweep test to run diagnostics on all example servant data."""

    def test_diagnostic_sweep_no_crashes(self):
        """Run enhanced diagnostic on all example servants to ensure no runtime crashes."""
        example_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'example_servant_data')
        
        if not os.path.exists(example_dir):
            self.skipTest("example_servant_data directory not found")
        
        json_files = [f for f in os.listdir(example_dir) if f.endswith('.json')]
        collection_nos = []
        
        for filename in json_files:
            try:
                collection_no = int(filename[:-5])  # Remove .json extension
                collection_nos.append(collection_no)
            except ValueError:
                continue  # Skip non-numeric filenames
        
        self.assertGreater(len(collection_nos), 0, "Should find at least some example servants")
        
        # Test first few servants to avoid long test times
        test_servants = sorted(collection_nos)[:5]  # Test first 5 servants
        
        for servant_id in test_servants:
            with self.subTest(servant_id=servant_id):
                try:
                    # Run diagnostic - should not crash
                    results = enhanced_diag_servant(servant_id, 1, 4, output_json=False)
                    
                    # Basic validation of results
                    self.assertIn("collection_no", results)
                    self.assertIn("ascensions", results)
                    self.assertEqual(results["collection_no"], servant_id)
                    
                    # Should have tested ascensions 1-4
                    for asc in [1, 2, 3, 4]:
                        self.assertIn(asc, results["ascensions"], f"Should have results for ascension {asc}")
                        
                except Exception as e:
                    self.fail(f"Diagnostic for servant {servant_id} failed: {e}")


if __name__ == '__main__':
    unittest.main()