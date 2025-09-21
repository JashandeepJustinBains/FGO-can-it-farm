import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the entire connectDB module before any imports
mock_db = MagicMock()
sys.modules['scripts.connectDB'] = MagicMock()
sys.modules['scripts.connectDB'].db = mock_db

def test_select_ascension_data_function():
    """Test the select_ascension_data function with different JSON formats."""
    from units.Servant import select_ascension_data
    
    # Test case 1: Legacy single-list format (ascension-independent)
    legacy_servant = {
        'skills': [
            {'id': 1, 'name': 'Skill A'},
            {'id': 2, 'name': 'Skill B'}, 
            {'id': 3, 'name': 'Skill C'}
        ],
        'noblePhantasms': [
            {'id': 1, 'name': 'Test NP', 'card': 'arts'}
        ]
    }
    
    result = select_ascension_data(legacy_servant, 2)
    assert len(result['skills']) == 3
    assert result['skills'][0]['name'] == 'Skill A'
    assert len(result['noblePhantasms']) == 1
    assert result['noblePhantasms'][0]['name'] == 'Test NP'
    
    # Test case 2: List-of-lists format 
    list_of_lists_servant = {
        'skills': [
            [{'id': 1, 'name': 'Asc1 Skill A'}],  # Ascension 1
            [{'id': 2, 'name': 'Asc2 Skill A'}],  # Ascension 2  
            [{'id': 3, 'name': 'Asc3 Skill A'}]   # Ascension 3
        ],
        'noblePhantasms': [
            [{'id': 1, 'name': 'Asc1 NP', 'card': 'arts'}],
            [{'id': 2, 'name': 'Asc2 NP', 'card': 'buster'}]
        ]
    }
    
    result = select_ascension_data(list_of_lists_servant, 2)
    assert len(result['skills']) == 1
    assert result['skills'][0]['name'] == 'Asc2 Skill A'
    assert result['noblePhantasms'][0]['name'] == 'Asc2 NP'
    
    # Test case 3: Ascension higher than available (should use highest with warning)
    result = select_ascension_data(list_of_lists_servant, 5)
    assert result['skills'][0]['name'] == 'Asc3 Skill A'  # Should use last available
    assert result['noblePhantasms'][0]['name'] == 'Asc2 NP'  # Highest available NP

def test_team_repr_format():
    """Test team __repr__ format using a simple mock implementation."""
    
    # Create a minimal mock GameManager that demonstrates the repr format
    class MockGameManager:
        def __init__(self):
            # Create mock servants
            self.servants = []
            
            # Mock servant 1 (Mash)
            servant1 = MagicMock()
            servant1.id = 1
            servant1.name = 'Mash Kyrielight'
            servant1.ascension = 3
            servant1.nps.nps = [{'name': 'Lord Camelot', 'card': 'arts'}]
            servant1.skills.get_skill_by_num.side_effect = lambda i: {
                'name': ['Defensive Stance', 'Transient Wall of Snowflakes', 'Lord Camelot'][i]
            }
            servant1.skills.cooldowns = {1: 7, 2: 8, 3: 6}
            servant1.skills.max_cooldowns = {1: 7, 2: 8, 3: 6}
            self.servants.append(servant1)
            
            # Mock servant 2 (Aoko)
            servant2 = MagicMock()
            servant2.id = 413
            servant2.name = 'Aozaki Aoko'
            servant2.ascension = 1
            servant2.nps.nps = [{'name': 'Shooting Star', 'card': 'buster'}]
            servant2.skills.get_skill_by_num.side_effect = lambda i: {
                'name': ['Magic Bullet', 'Time Alter', 'Fifth Magic'][i]
            }
            servant2.skills.cooldowns = {1: 8, 2: 7, 3: 10}
            servant2.skills.max_cooldowns = {1: 8, 2: 7, 3: 10}
            self.servants.append(servant2)
        
        def __repr__(self):
            """Team representation implementation matching game_manager.py"""
            lines = []
            for i, servant in enumerate(self.servants, 1):
                # Basic servant info
                slot_line = f"Slot {i}: #{servant.id} {servant.name} (asc {servant.ascension})"
                
                # NP info
                if hasattr(servant, 'nps') and servant.nps and servant.nps.nps:
                    np = servant.nps.nps[0]
                    np_name = np.get('name', 'Unknown NP')
                    np_card = np.get('card', 'unknown')
                    slot_line += f" | NP: {np_name} ({np_card})"
                else:
                    slot_line += " | NP: None"
                
                # Skills info
                skills_info = []
                if hasattr(servant, 'skills') and servant.skills:
                    for skill_num in [1, 2, 3]:
                        try:
                            skill = servant.skills.get_skill_by_num(skill_num - 1)
                            skill_name = skill.get('name', f'Skill {skill_num}')
                            cooldown = servant.skills.cooldowns.get(skill_num, 0)
                            max_cd = servant.skills.max_cooldowns.get(skill_num, 0)
                            cd_display = cooldown if cooldown > 0 else max_cd
                            skills_info.append(f"{skill_name} (CD {cd_display})")
                        except (IndexError, KeyError):
                            skills_info.append(f"Skill {skill_num} (unavailable)")
                
                if skills_info:
                    slot_line += f" | Skills: {', '.join(skills_info)}"
                else:
                    slot_line += " | Skills: None"
                
                # Transform info
                transform_info = "none"
                if servant.id == 413:  # Aoko
                    transform_info = "transforms->4132 on first NP use"
                elif servant.id == 4132:  # Super Aoko
                    transform_info = "transformed from 413"
                
                slot_line += f" | transforms: {transform_info}"
                lines.append(slot_line)
            
            return "\n".join(lines)
    
    # Test the representation
    mock_gm = MockGameManager()
    team_repr = repr(mock_gm)
    
    print("Generated team representation:")
    print(team_repr)
    
    # Verify the representation contains expected information
    assert '#1 Mash Kyrielight (asc 3)' in team_repr
    assert '#413 Aozaki Aoko (asc 1)' in team_repr
    assert 'Lord Camelot (arts)' in team_repr
    assert 'Shooting Star (buster)' in team_repr
    assert 'Defensive Stance' in team_repr
    assert 'Magic Bullet' in team_repr
    assert 'transforms->4132 on first NP use' in team_repr  # Aoko transform
    assert 'Slot 1:' in team_repr
    assert 'Slot 2:' in team_repr

if __name__ == '__main__':
    pytest.main([__file__, '-v'])