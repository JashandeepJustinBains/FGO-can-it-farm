"""
Tests for dynamic NP selection based on runtime ascension changes.

Tests ensure that Noble Phantasm selection respects ascension changes
during combat for servants with ascension-dependent NPs like Mélusine (312).
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
        
        # Load test data
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


class TestDynamicNPSelection:
    """Test dynamic NP selection with ascension changes."""
    
    def test_servant_312_ascension_change(self):
        """Test Mélusine (312) NP changes from Arts to Buster on ascension change."""
        # Create servant at ascension 1
        servant = Servant(312, ascension=1)
        
        # Verify initial NP selection (ascension 1 should be Arts)
        assert len(servant.nps.nps) > 0, "Servant should have at least one NP"
        initial_np = servant.nps.nps[-1]  # Default to highest ID NP
        
        # Expected: Arts NP "Innocence Arondight" (id: 304801)
        expected_arts_id = 304801
        actual_id = servant.nps._extract_number(initial_np.get('id', 0))
        assert actual_id == expected_arts_id, f"Expected Arts NP {expected_arts_id}, got {actual_id}"
        assert initial_np.get('card') == 'arts', f"Expected Arts card type, got {initial_np.get('card')}"
        
        # Change to ascension 3
        servant.change_ascension(3)
        
        # Verify NP changed to Buster
        updated_np = servant.nps.nps[-1]  # Default to highest ID NP
        expected_buster_id = 304802
        actual_id = servant.nps._extract_number(updated_np.get('id', 0))
        assert actual_id == expected_buster_id, f"Expected Buster NP {expected_buster_id}, got {actual_id}"
        assert updated_np.get('card') == 'buster', f"Expected Buster card type, got {updated_np.get('card')}"
    
    def test_servant_312_reverse_ascension_change(self):
        """Test Mélusine (312) NP changes from Buster back to Arts."""
        # Create servant at ascension 3
        servant = Servant(312, ascension=3)
        
        # Verify initial NP selection (ascension 3 should be Buster)
        initial_np = servant.nps.nps[-1]
        expected_buster_id = 304802
        actual_id = servant.nps._extract_number(initial_np.get('id', 0))
        assert actual_id == expected_buster_id, f"Expected Buster NP {expected_buster_id}, got {actual_id}"
        
        # Change back to ascension 1
        servant.change_ascension(1)
        
        # Verify NP changed back to Arts
        updated_np = servant.nps.nps[-1]
        expected_arts_id = 304801
        actual_id = servant.nps._extract_number(updated_np.get('id', 0))
        assert actual_id == expected_arts_id, f"Expected Arts NP {expected_arts_id}, got {actual_id}"
        assert updated_np.get('card') == 'arts', f"Expected Arts card type, got {updated_np.get('card')}"
    
    def test_servant_1_mash_variant_handling(self):
        """Test Mash (1) variant handling with different ascensions."""
        # Test various ascensions for Mash
        for ascension in [0, 1, 2, 3]:
            servant = Servant(1, ascension=ascension)
            
            # Verify Mash has NPs regardless of ascension
            assert len(servant.nps.nps) > 0, f"Mash should have NPs at ascension {ascension}"
            
            # Mash's NP should be consistent across ascensions
            np = servant.nps.nps[-1]
            assert np.get('card') in ['arts', 'buster', 'quick'], f"NP should have valid card type at ascension {ascension}"
    
    def test_servant_444_static_ascension_mapping(self):
        """Test U-Olga Marie (444) static NP validation by ascension."""
        # Test ascension 1
        servant_asc1 = Servant(444, ascension=1)
        assert len(servant_asc1.nps.nps) > 0, "Servant 444 should have NPs at ascension 1"
        np_asc1 = servant_asc1.nps.nps[-1]
        
        # Test ascension 3
        servant_asc3 = Servant(444, ascension=3)
        assert len(servant_asc3.nps.nps) > 0, "Servant 444 should have NPs at ascension 3"
        np_asc3 = servant_asc3.nps.nps[-1]
        
        # The NP selection should be consistent for different ascensions
        # (since 444 doesn't have ascension-dependent NP changes like 312)
        assert np_asc1.get('card') == np_asc3.get('card'), "Servant 444 should have same NP card type across ascensions"
    
    def test_ascension_state_persistence(self):
        """Test that ascension changes persist in servant state."""
        servant = Servant(312, ascension=1)
        initial_ascension = servant.ascension
        
        # Change ascension
        new_ascension = 3
        servant.change_ascension(new_ascension)
        
        # Verify ascension state changed
        assert servant.ascension == new_ascension, f"Ascension should be {new_ascension}, got {servant.ascension}"
        assert servant.ascension != initial_ascension, "Ascension should have changed"
    
    def test_variant_svt_id_update(self):
        """Test that variant_svt_id updates correctly on ascension change."""
        servant = Servant(312, ascension=1)
        initial_variant = servant.variant_svt_id
        
        # Change ascension
        servant.change_ascension(3)
        
        # variant_svt_id should update (may be same or different depending on servant data)
        # The important thing is that it gets recomputed
        assert hasattr(servant, 'variant_svt_id'), "Servant should have variant_svt_id attribute"
        
        # Verify the variant computation was called by checking the NP selection changed
        np = servant.nps.nps[-1]
        expected_buster_id = 304802
        actual_id = servant.nps._extract_number(np.get('id', 0))
        assert actual_id == expected_buster_id, "variant_svt_id update should affect NP selection"

    def test_current_np_accessibility(self):
        """Test that current NP can be accessed easily."""
        servant = Servant(312, ascension=1)
        
        # Should be able to get current NP
        current_np = servant.nps.nps[-1] if servant.nps.nps else None
        assert current_np is not None, "Should be able to get current NP"
        
        # Should have basic NP properties
        assert 'card' in current_np, "NP should have card type"
        assert 'id' in current_np, "NP should have ID"
        
        # After ascension change, should get different NP
        servant.change_ascension(3)
        updated_np = servant.nps.nps[-1] if servant.nps.nps else None
        assert updated_np is not None, "Should be able to get updated NP"
        
        # NPs should be different
        initial_id = servant.nps._extract_number(current_np.get('id', 0))
        updated_id = servant.nps._extract_number(updated_np.get('id', 0))
        assert initial_id != updated_id, "NP should change after ascension change"


if __name__ == "__main__":
    # Run tests directly
    test = TestDynamicNPSelection()
    
    try:
        test.test_servant_312_ascension_change()
        print("✓ test_servant_312_ascension_change passed")
        
        test.test_servant_312_reverse_ascension_change()
        print("✓ test_servant_312_reverse_ascension_change passed")
        
        test.test_servant_1_mash_variant_handling()
        print("✓ test_servant_1_mash_variant_handling passed")
        
        test.test_servant_444_static_ascension_mapping()
        print("✓ test_servant_444_static_ascension_mapping passed")
        
        test.test_ascension_state_persistence()
        print("✓ test_ascension_state_persistence passed")
        
        test.test_variant_svt_id_update()
        print("✓ test_variant_svt_id_update passed")
        
        test.test_current_np_accessibility()
        print("✓ test_current_np_accessibility passed")
        
        print("\nAll tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()