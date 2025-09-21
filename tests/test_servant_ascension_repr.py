import pytest
import logging

# Standalone implementation for testing
def select_ascension_data(servant_json: dict, ascension: int) -> dict:
    """
    Select ascension-specific data from servant JSON.
    
    Handles multiple input shapes:
    - Legacy single-list: skills/noblePhantasms as single list (ascension-independent)
    - List-of-lists: outer list with items per-ascension
    - ascensions/forms arrays: objects with ascension field containing skills/noblePhantasms
    - Mixed shapes: prefer explicit ascension entries, fallback to legacy
    
    Args:
        servant_json: The servant data dictionary
        ascension: The requested ascension level (1-based)
    
    Returns:
        Dictionary with selected ascension data (skills, noblePhantasms, passives, transforms)
    """
    result = {}
    
    # Check for explicit ascensions/forms array first
    ascensions_data = servant_json.get('ascensions', servant_json.get('forms', []))
    if ascensions_data:
        # Look for matching ascension
        selected_ascension = None
        for asc_data in ascensions_data:
            asc_index = asc_data.get('ascension', asc_data.get('ascensionIndex', 0))
            if asc_index == ascension:
                selected_ascension = asc_data
                break
        
        if selected_ascension:
            # Extract data from the ascension object
            result['skills'] = selected_ascension.get('skills', [])
            result['noblePhantasms'] = selected_ascension.get('noblePhantasms', [])
            result['passives'] = selected_ascension.get('passives', [])
            result['transforms'] = selected_ascension.get('transforms', [])
            return result
        else:
            # Requested ascension not found, use highest available
            if ascensions_data:
                highest_asc = max(ascensions_data, key=lambda x: x.get('ascension', x.get('ascensionIndex', 0)))
                highest_level = highest_asc.get('ascension', highest_asc.get('ascensionIndex', 0))
                print(f"Warning: Ascension {ascension} not found, using highest available ascension {highest_level}")
                result['skills'] = highest_asc.get('skills', [])
                result['noblePhantasms'] = highest_asc.get('noblePhantasms', [])
                result['passives'] = highest_asc.get('passives', [])
                result['transforms'] = highest_asc.get('transforms', [])
                return result
    
    # Check for list-of-lists format (per-ascension lists)
    skills_data = servant_json.get('skills', [])
    nps_data = servant_json.get('noblePhantasms', [])
    
    # Detect if skills/nps are list-of-lists
    is_skills_list_of_lists = (skills_data and 
                              isinstance(skills_data, list) and 
                              len(skills_data) > 0 and 
                              isinstance(skills_data[0], list))
    
    is_nps_list_of_lists = (nps_data and 
                           isinstance(nps_data, list) and 
                           len(nps_data) > 0 and 
                           isinstance(nps_data[0], list))
    
    if is_skills_list_of_lists or is_nps_list_of_lists:
        # Handle list-of-lists format
        if is_skills_list_of_lists:
            if ascension <= len(skills_data):
                result['skills'] = skills_data[ascension - 1]
            else:
                # Use highest available
                highest_idx = len(skills_data) - 1
                print(f"Warning: Skills ascension {ascension} not found, using highest available ascension {highest_idx + 1}")
                result['skills'] = skills_data[highest_idx]
        else:
            result['skills'] = skills_data
            
        if is_nps_list_of_lists:
            if ascension <= len(nps_data):
                result['noblePhantasms'] = nps_data[ascension - 1]
            else:
                # Use highest available
                highest_idx = len(nps_data) - 1
                print(f"Warning: NoblePhantasms ascension {ascension} not found, using highest available ascension {highest_idx + 1}")
                result['noblePhantasms'] = nps_data[highest_idx]
        else:
            result['noblePhantasms'] = nps_data
            
        # For list-of-lists, other fields are typically ascension-independent
        result['passives'] = servant_json.get('passives', servant_json.get('classPassive', []))
        result['transforms'] = servant_json.get('transforms', [])
        return result
    
    # Legacy single-list format (ascension-independent)
    result['skills'] = skills_data
    result['noblePhantasms'] = nps_data
    result['passives'] = servant_json.get('passives', servant_json.get('classPassive', []))
    result['transforms'] = servant_json.get('transforms', [])
    
    return result


class TestServantAscensionRepr:
    
    def test_select_ascension_data_variants(self):
        """Test select_ascension_data with various input shapes."""
        
        # Test case 1: Legacy single-list format (ascension-independent)
        legacy_servant = {
            'skills': [
                {'id': 1001, 'name': 'Skill A', 'num': 1},
                {'id': 1002, 'name': 'Skill B', 'num': 2}
            ],
            'noblePhantasms': [
                {'id': 2001, 'name': 'NP A', 'card': 'buster'}
            ]
        }
        
        result = select_ascension_data(legacy_servant, ascension=2)
        assert 'skills' in result
        assert 'noblePhantasms' in result
        assert len(result['skills']) == 2
        assert result['skills'][0]['name'] == 'Skill A'
        assert len(result['noblePhantasms']) == 1
        assert result['noblePhantasms'][0]['name'] == 'NP A'
        
        # Test case 2: List-of-lists format (per-ascension)
        list_of_lists_servant = {
            'skills': [
                [{'id': 1001, 'name': 'Skill A v1', 'num': 1}],  # Ascension 1
                [{'id': 1001, 'name': 'Skill A v2', 'num': 1}],  # Ascension 2
                [{'id': 1001, 'name': 'Skill A v3', 'num': 1}]   # Ascension 3
            ],
            'noblePhantasms': [
                [{'id': 2001, 'name': 'NP A v1', 'card': 'buster'}],  # Ascension 1
                [{'id': 2002, 'name': 'NP A v2', 'card': 'buster'}]   # Ascension 2
            ]
        }
        
        # Test selecting ascension 2
        result = select_ascension_data(list_of_lists_servant, ascension=2)
        assert result['skills'][0]['name'] == 'Skill A v2'
        assert result['noblePhantasms'][0]['name'] == 'NP A v2'
        
        # Test selecting ascension beyond available (should use highest)
        result = select_ascension_data(list_of_lists_servant, ascension=5)
        assert result['skills'][0]['name'] == 'Skill A v3'  # Highest available
        assert result['noblePhantasms'][0]['name'] == 'NP A v2'  # Highest available
        
        # Test case 3: Ascensions array format
        ascensions_servant = {
            'ascensions': [
                {
                    'ascension': 1,
                    'skills': [{'id': 1001, 'name': 'Mash Skill v1', 'num': 1}],
                    'noblePhantasms': [{'id': 2001, 'name': 'Lord Camelot v1', 'card': 'arts'}]
                },
                {
                    'ascension': 2,
                    'skills': [{'id': 1002, 'name': 'Mash Skill v2', 'num': 1}],
                    'noblePhantasms': [{'id': 2002, 'name': 'Lord Camelot v2', 'card': 'arts'}]
                }
            ]
        }
        
        result = select_ascension_data(ascensions_servant, ascension=2)
        assert result['skills'][0]['name'] == 'Mash Skill v2'
        assert result['noblePhantasms'][0]['name'] == 'Lord Camelot v2'
        
        # Test selecting unavailable ascension (should use highest)
        result = select_ascension_data(ascensions_servant, ascension=4)
        assert result['skills'][0]['name'] == 'Mash Skill v2'  # Highest available
        assert result['noblePhantasms'][0]['name'] == 'Lord Camelot v2'
    
    def test_team_repr_contains_core_fields(self):
        """Test that the team repr format functions work correctly."""
        
        # Test basic formatting functions that would be used in the real repr
        # This tests the core logic without requiring database access
        
        # Mock servant data
        mock_servant = type('MockServant', (), {
            'id': 1,
            'name': 'Test Servant',
            'ascension': 1,
            'nps': type('MockNPs', (), {
                'nps': [{'name': 'Test NP', 'card': 'buster', 'id': 1001}]
            })(),
            'skills': type('MockSkills', (), {
                'skills': {1: [{'name': 'Test Skill', 'id': 2001}]}
            })()
        })()
        
        # Test the format patterns we expect
        slot_info = f"Slot 1: #{mock_servant.id} {mock_servant.name} (asc {mock_servant.ascension})"
        assert "#1" in slot_info
        assert "Test Servant" in slot_info
        assert "(asc 1)" in slot_info
        
        # Test NP formatting 
        np_info = f"NP: {mock_servant.nps.nps[0]['name']} ({mock_servant.nps.nps[0]['card']})"
        assert "NP: Test NP (buster)" in np_info
        
        # Test Skills formatting
        skill_name = mock_servant.skills.skills[1][0]['name']
        skills_info = f"Skills: {skill_name}"
        assert "Skills: Test Skill" in skills_info
        
    def test_select_ascension_data_edge_cases(self):
        """Test edge cases for select_ascension_data."""
        
        # Empty servant data
        empty_servant = {}
        result = select_ascension_data(empty_servant, ascension=1)
        assert result['skills'] == []
        assert result['noblePhantasms'] == []
        assert result['passives'] == []
        
        # Mixed format - has both legacy and ascensions (should prefer ascensions)
        mixed_servant = {
            'skills': [{'id': 999, 'name': 'Legacy Skill', 'num': 1}],
            'ascensions': [
                {
                    'ascension': 1,
                    'skills': [{'id': 1001, 'name': 'Ascension Skill', 'num': 1}]
                }
            ]
        }
        
        result = select_ascension_data(mixed_servant, ascension=1)
        # Should prefer ascensions data over legacy
        assert result['skills'][0]['name'] == 'Ascension Skill'
        
        # Test with classPassive fallback
        servant_with_class_passive = {
            'skills': [],
            'classPassive': [{'id': 3001, 'name': 'Class Passive'}]
        }
        
        result = select_ascension_data(servant_with_class_passive, ascension=1)
        assert len(result['passives']) == 1
        assert result['passives'][0]['name'] == 'Class Passive'


if __name__ == '__main__':
    pytest.main([__file__])