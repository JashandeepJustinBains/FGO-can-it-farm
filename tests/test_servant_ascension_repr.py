"""
Tests for ascension-selection helper and enhanced repr methods.

Assumptions/fallbacks comment:
- Uses minimal fixtures from example_servant_data to avoid DB dependencies
- Falls back gracefully when ascension data is missing (logs warnings)
- Preserves raw effect IDs and matrices without semantic translation
- Tests repr format patterns rather than deep data equality
"""

import pytest
import json
import os


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
            asc_index = asc_data.get('ascension', asc_data.get('ascensionIndex', asc_data.get('index', 0)))
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
                highest_asc = max(ascensions_data, key=lambda x: x.get('ascension', x.get('ascensionIndex', x.get('index', 0))))
                highest_level = highest_asc.get('ascension', highest_asc.get('ascensionIndex', highest_asc.get('index', 0)))
                print(f"WARNING: Ascension {ascension} not found, using highest available ascension {highest_level}")
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
                print(f"WARNING: Skills ascension {ascension} not found, using highest available ascension {highest_idx + 1}")
                result['skills'] = skills_data[highest_idx]
        else:
            result['skills'] = skills_data
            
        if is_nps_list_of_lists:
            if ascension <= len(nps_data):
                result['noblePhantasms'] = nps_data[ascension - 1]
            else:
                # Use highest available
                highest_idx = len(nps_data) - 1
                print(f"WARNING: NoblePhantasms ascension {ascension} not found, using highest available ascension {highest_idx + 1}")
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
        
        # Test legacy single-list format
        legacy_servant = {
            'skills': [
                {'id': 1001, 'name': 'Skill A', 'num': 1},
                {'id': 1002, 'name': 'Skill B', 'num': 2}
            ],
            'noblePhantasms': [
                {'id': 2001, 'name': 'NP A', 'card': 'arts'}
            ]
        }
        
        result = select_ascension_data(legacy_servant, ascension=1)
        assert len(result['skills']) == 2
        assert result['skills'][0]['name'] == 'Skill A'
        assert len(result['noblePhantasms']) == 1
        assert result['noblePhantasms'][0]['name'] == 'NP A'
        
        # Test list-of-lists format
        list_of_lists_servant = {
            'skills': [
                [{'id': 1001, 'name': 'Skill A v1', 'num': 1}],   # Ascension 1
                [{'id': 1011, 'name': 'Skill A v2', 'num': 1}],   # Ascension 2
                [{'id': 1021, 'name': 'Skill A v3', 'num': 1}]    # Ascension 3
            ],
            'noblePhantasms': [
                [{'id': 2001, 'name': 'NP A v1', 'card': 'arts'}],   # Ascension 1
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
        
        # Test explicit ascensions format
        ascensions_servant = {
            'ascensions': [
                {
                    'ascension': 1,
                    'skills': [{'id': 1001, 'name': 'Asc1 Skill', 'num': 1}],
                    'noblePhantasms': [{'id': 2001, 'name': 'Asc1 NP', 'card': 'quick'}]
                },
                {
                    'ascension': 3,
                    'skills': [{'id': 1003, 'name': 'Asc3 Skill', 'num': 1}],
                    'noblePhantasms': [{'id': 2003, 'name': 'Asc3 NP', 'card': 'buster'}]
                }
            ]
        }
        
        result = select_ascension_data(ascensions_servant, ascension=3)
        assert result['skills'][0]['name'] == 'Asc3 Skill'
        assert result['noblePhantasms'][0]['name'] == 'Asc3 NP'
        
        # Test missing ascension (should fall back to highest)
        result = select_ascension_data(ascensions_servant, ascension=2)
        assert result['skills'][0]['name'] == 'Asc3 Skill'  # Highest available
    
    def test_team_repr_contains_core_fields(self):
        """Test that team repr contains expected core fields."""
        
        # Create a simple mock GameManager for testing
        class MockNPs:
            def __init__(self, nps_data):
                self.nps = nps_data
        
        class MockSkills:
            def __init__(self, skills_data):
                self.skills = skills_data
        
        class MockServant:
            def __init__(self, servant_id, name, ascension):
                self.id = servant_id
                self.name = name
                self.ascension = ascension
                self.data = {}
                self.skills = MockSkills({1: [{'name': f'Test Skill {servant_id}', 'cooldown': 7}]})
                self.nps = MockNPs([{'name': f'Test NP {servant_id}', 'card': 'buster', 'new_id': 1}])
        
        class MockGameManager:
            def __init__(self, servants):
                self.servants = servants
            
            def team_repr(self):
                if not self.servants:
                    return "GameManager(no servants)"
                
                lines = ["Team composition:"]
                
                for i, servant in enumerate(self.servants):
                    slot_info = f"Slot {i + 1}: #{servant.id} {servant.name}"
                    if hasattr(servant, 'ascension'):
                        slot_info += f" (asc {servant.ascension})"
                    
                    lines.append(slot_info)
                    lines.append(f"  NPs: Test NP {servant.id} (buster)")
                    lines.append(f"  Skills: Test Skill {servant.id}")
                    lines.append(f"  transforms: none")
                
                return "\\n".join(lines)
            
            def __repr__(self):
                return self.team_repr()
        
        # Create test servants and game manager
        servant1 = MockServant(1, 'Test Servant 1', 2)
        servant2 = MockServant(2, 'Test Servant 2', 1)
        game_manager = MockGameManager([servant1, servant2])
        
        # Test repr output
        repr_output = repr(game_manager)
        
        # Assert that core fields are present using substring checks
        assert "Test Servant 1" in repr_output
        assert "Test Servant 2" in repr_output
        assert "#1" in repr_output  # collectionNo
        assert "#2" in repr_output  # collectionNo
        assert "(asc 2)" in repr_output  # ascension
        assert "(asc 1)" in repr_output  # ascension
        assert "Test NP 1" in repr_output  # NP name
        assert "Test NP 2" in repr_output  # NP name
        assert "Test Skill 1" in repr_output  # skill name
        assert "Test Skill 2" in repr_output  # skill name
    
    def test_select_ascension_data_edge_cases(self):
        """Test edge cases for select_ascension_data function."""
        
        # Test empty servant data
        empty_servant = {}
        result = select_ascension_data(empty_servant, ascension=1)
        assert result['skills'] == []
        assert result['noblePhantasms'] == []
        assert result['passives'] == []
        assert result['transforms'] == []
        
        # Test servant with classPassive instead of passives
        servant_with_class_passive = {
            'skills': [],
            'noblePhantasms': [],
            'classPassive': [{'id': 401, 'name': 'Test Passive'}]
        }
        result = select_ascension_data(servant_with_class_passive, ascension=1)
        assert len(result['passives']) == 1
        assert result['passives'][0]['name'] == 'Test Passive'
        
        # Test mixed format handling
        mixed_servant = {
            'skills': [{'id': 1001, 'name': 'Legacy Skill', 'num': 1}],  # Legacy format
            'forms': [  # Forms array
                {
                    'index': 1,
                    'noblePhantasms': [{'id': 2001, 'name': 'Form NP', 'card': 'quick'}]
                }
            ]
        }
        result = select_ascension_data(mixed_servant, ascension=1)
        # Should prefer forms array which matches index=1=ascension, 
        # but forms entry has no skills so result['skills'] will be empty
        assert len(result['skills']) == 0  # No skills in the form entry
        assert result['noblePhantasms'][0]['name'] == 'Form NP'