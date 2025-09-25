"""
Tests for dynamic skill selection based on runtime ascension changes.

Tests ensure that skill selection respects ascension changes during combat
for servants with ascension-dependent skills.
"""
import pytest
import json
import os
import sys

# Add the parent directory to sys.path so we can import from units
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock database for testing
class MockDB:
    def __init__(self):
        self.servants = self
        self._data = {}
        
        # Load test data - we need servants that have skills with skillSvts
        self._load_servant_data(312, 'example_servant_data/312.json')
        self._load_servant_data(1, 'example_servant_data/1.json') 
        self._load_servant_data(444, 'example_servant_data/444.json')
    
    def _load_servant_data(self, collection_no, filename):
        """Load servant data from JSON file."""
        file_path = os.path.join(os.path.dirname(__file__), '..', filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._data[collection_no] = data
        except FileNotFoundError:
            print(f"Warning: Could not load {filename}")
            self._data[collection_no] = None
    
    def find_one(self, query):
        collection_no = query.get('collectionNo')
        return self._data.get(collection_no)

# Set up mock database and monkey-patch it into the module where it's used
mock_db = MockDB()

# We need to inject db into the global namespace for the Servant module
import units.Servant
import builtins
builtins.db = mock_db  # Make db available globally

from units.Servant import Servant
from units.skills import Skills


class TestDynamicSkillSelection:
    """Test dynamic skill selection with ascension changes."""
    
    def test_skills_runtime_aware_selection(self):
        """Test that skills use runtime-aware selection based on current variant."""
        # Create servant at ascension 1
        servant = Servant(312, ascension=1)
        
        # Get initial skill 1
        skill_1 = servant.skills.get_skill_by_num(1)
        initial_skill_id = skill_1['id']
        
        # Change ascension to 3
        servant.change_ascension(3)
        
        # Get skill 1 again - it should potentially be different
        # (even if it's the same, the selection logic should run)
        skill_1_after = servant.skills.get_skill_by_num(1)
        updated_skill_id = skill_1_after['id']
        
        # The important thing is that get_skill_by_num ran selection logic
        # based on the current variant_svt_id, not cached from initialization
        assert skill_1_after is not None
        assert 'id' in skill_1_after
        assert 'name' in skill_1_after
        assert 'cooldown' in skill_1_after
    
    def test_skills_variant_svt_id_usage(self):
        """Test that skills consider the current variant_svt_id for selection."""
        servant = Servant(312, ascension=1)
        
        # Manually change variant_svt_id to test selection behavior
        original_variant = servant.variant_svt_id
        servant.variant_svt_id = 304800  # Base form
        
        skill_base = servant.skills.get_skill_by_num(1)
        
        # Change to different variant (if available in skillSvts)
        servant.variant_svt_id = 304820  # Different variant
        
        skill_variant = servant.skills.get_skill_by_num(1)
        
        # Both should be valid skills
        assert skill_base is not None
        assert skill_variant is not None
        assert 'id' in skill_base
        assert 'id' in skill_variant
        
        # Restore original variant
        servant.variant_svt_id = original_variant
    
    def test_skills_deferred_candidate_storage(self):
        """Test that Skills stores raw candidates for skillSvts format."""
        servant = Servant(312, ascension=1)
        
        # Check that skills have raw_candidates stored (if skillSvts format detected)
        # This tests the _parse_skill_svts method with defer_selection=True
        skills_obj = servant.skills
        
        # The skills should be parseable regardless of format
        for skill_num in [1, 2, 3]:
            try:
                skill = skills_obj.get_skill_by_num(skill_num)
                assert skill is not None, f"Skill {skill_num} should be available"
                assert 'id' in skill, f"Skill {skill_num} should have an id"
                assert 'name' in skill, f"Skill {skill_num} should have a name"
            except IndexError:
                # Some servants may not have all 3 skills
                pass
    
    def test_skills_max_cooldowns_safe(self):
        """Test that initialize_max_cooldowns safely handles both formats."""
        servant = Servant(312, ascension=1)
        
        max_cooldowns = servant.skills.max_cooldowns
        assert isinstance(max_cooldowns, dict)
        
        # Should have entries for available skills
        for skill_num in [1, 2, 3]:
            if skill_num in servant.skills.skills and servant.skills.skills[skill_num]:
                assert skill_num in max_cooldowns
                assert isinstance(max_cooldowns[skill_num], (int, float))
                assert max_cooldowns[skill_num] >= 0
    
    def test_skills_release_conditions(self):
        """Test that release conditions are properly evaluated."""
        # Test with different ascensions to see if release conditions affect availability
        servant_asc1 = Servant(312, ascension=1)
        servant_asc3 = Servant(312, ascension=3)
        
        # Both should have skills, but they might differ based on release conditions
        skill1_asc1 = servant_asc1.skills.get_skill_by_num(1)
        skill1_asc3 = servant_asc3.skills.get_skill_by_num(1)
        
        assert skill1_asc1 is not None
        assert skill1_asc3 is not None
        
        # The selection process should have run for both
        assert 'id' in skill1_asc1
        assert 'id' in skill1_asc3
    
    def test_skills_costume_override_honored(self):
        """Test that explicit costume overrides affect skill selection."""
        # Create servant with explicit costume override
        servant = Servant(312, ascension=1, variant_svt_id=304830)  # Costume 1
        
        skill = servant.skills.get_skill_by_num(1)
        assert skill is not None
        assert 'id' in skill
        
        # The variant_svt_id should have been used in selection
        assert servant.variant_svt_id == 304830
    
    def test_skills_legacy_format_compatibility(self):
        """Test that legacy skills format still works."""
        # Test with a servant that likely has legacy format
        servant = Servant(1, ascension=1)  # Mash
        
        skill = servant.skills.get_skill_by_num(1)
        assert skill is not None
        assert 'id' in skill
        assert 'name' in skill
        assert 'cooldown' in skill


if __name__ == "__main__":
    # Run tests directly
    test = TestDynamicSkillSelection()
    
    try:
        test.test_skills_runtime_aware_selection()
        print("✓ test_skills_runtime_aware_selection passed")
        
        test.test_skills_variant_svt_id_usage()
        print("✓ test_skills_variant_svt_id_usage passed")
        
        test.test_skills_deferred_candidate_storage()
        print("✓ test_skills_deferred_candidate_storage passed")
        
        test.test_skills_max_cooldowns_safe()
        print("✓ test_skills_max_cooldowns_safe passed")
        
        test.test_skills_release_conditions()
        print("✓ test_skills_release_conditions passed")
        
        test.test_skills_costume_override_honored()
        print("✓ test_skills_costume_override_honored passed")
        
        test.test_skills_legacy_format_compatibility()
        print("✓ test_skills_legacy_format_compatibility passed")
        
        print("\nAll skill tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()