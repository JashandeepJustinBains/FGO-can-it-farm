"""
Unit tests for servant_parser module.

Tests the ascension-aware servant parser with different data shapes and scenarios.
"""

import pytest
import json
import os
from unittest.mock import patch, mock_open
from utils.servant_parser import (
    select_ascension_data,
    extract_skill_summary,
    extract_np_summary,
    _detect_transforms,
    _unwrap_mongo_data,
    generate_markdown_summary,
    process_servant_file
)


@pytest.fixture
def sample_mash_data():
    """Load Mash data for testing."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(current_dir)
    mash_file = os.path.join(repo_root, 'example_servant_data', '1-MashKyrielight.json')
    
    if os.path.exists(mash_file):
        with open(mash_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Fallback mock data if file not found
        return {
            "collectionNo": {"$numberInt": "1"},
            "name": "Mash Kyrielight",
            "className": "shielder",
            "classId": {"$numberInt": "8"},
            "rarity": {"$numberInt": "4"},
            "attribute": "earth",
            "skills": [
                {
                    "id": {"$numberInt": "1000"},
                    "name": "Test Skill",
                    "coolDown": [10, 10, 9, 9, 8, 8, 7, 7, 6, 5],
                    "strengthStatus": {"$numberInt": "1"},
                    "functions": [{"funcType": "addState"}]
                }
            ],
            "noblePhantasms": [
                {
                    "name": "Test NP",
                    "card": "arts",
                    "npDistribution": [100],
                    "functions": [{"funcTargetType": "ptAll"}]
                }
            ],
            "classPassive": [
                {
                    "id": {"$numberInt": "12345"},
                    "name": "Test Passive",
                    "detail": "Test passive description"
                }
            ],
            "traits": [
                {"id": {"$numberInt": "2"}, "name": "genderFemale"}
            ]
        }


@pytest.fixture
def sample_aoko_data():
    """Load Aoko data for testing transforms."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(current_dir)
    aoko_file = os.path.join(repo_root, 'example_servant_data', '413-Aozaki Aoko.json')
    
    if os.path.exists(aoko_file):
        with open(aoko_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Fallback mock data
        return {
            "collectionNo": {"$numberInt": "413"},
            "name": "Aozaki Aoko",
            "className": "foreigner",
            "classId": {"$numberInt": "25"},
            "rarity": {"$numberInt": "5"},
            "attribute": "human",
            "skills": [],
            "noblePhantasms": [],
            "classPassive": [],
            "traits": []
        }


def test_unwrap_mongo_data():
    """Test MongoDB format unwrapping."""
    input_data = {
        "number": {"$numberInt": "123"},
        "nested": {
            "inner": {"$numberInt": "456"},
            "regular": "text"
        },
        "list": [{"$numberInt": "789"}, "normal"]
    }
    
    result = _unwrap_mongo_data(input_data)
    
    assert result["number"] == 123
    assert result["nested"]["inner"] == 456
    assert result["nested"]["regular"] == "text"
    assert result["list"][0] == 789
    assert result["list"][1] == "normal"


def test_legacy_single_list_selection(sample_mash_data):
    """Test legacy single-list selection (Mash example)."""
    result = select_ascension_data(sample_mash_data, 3)
    
    # Check meta data
    assert result['meta']['collectionNo'] == 1
    assert result['meta']['name'] == 'Mash Kyrielight'
    assert result['meta']['className'] == 'shielder'
    
    # Check ascension data
    ascension_data = result['ascensions'][0]
    assert ascension_data['ascension_index'] == 3
    assert len(ascension_data['skills']) <= 3  # Should have skills
    assert 'noblePhantasms' in ascension_data
    assert 'passives' in ascension_data
    
    # Check raw_keys indicate legacy format
    assert result['raw_keys']['source_format'] == 'legacy_single_list'


def test_extract_skill_summary():
    """Test skill summary extraction."""
    skill_data = {
        "id": {"$numberInt": "12345"},
        "name": "Test Skill A",
        "coolDown": [10, 10, 9, 9, 8, 8, 7, 7, 6, 5],  # Max level at index 9
        "strengthStatus": {"$numberInt": "1"},  # Upgraded
        "functions": [
            {"funcType": "addState", "funcTargetType": "self"},
            {"funcType": "gainNp", "funcTargetType": "self"}
        ]
    }
    
    unwrapped = _unwrap_mongo_data(skill_data)
    result = extract_skill_summary(unwrapped)
    
    assert result['id'] == 12345
    assert result['display_name'] == 'Test Skill A'
    assert result['cooldown'] == 5  # Should use index 9 (max level)
    assert result['upgraded'] == True
    assert len(result['raw_effects']) == 2


def test_extract_skill_summary_non_upgraded():
    """Test skill summary for non-upgraded skill."""
    skill_data = {
        "id": {"$numberInt": "67890"},
        "name": "Basic Skill",
        "coolDown": [8, 8, 7, 7, 6, 6, 5, 5, 4, 4],
        "strengthStatus": {"$numberInt": "0"},  # Not upgraded
        "functions": [{"funcType": "healHp"}]
    }
    
    unwrapped = _unwrap_mongo_data(skill_data)
    result = extract_skill_summary(unwrapped)
    
    assert result['upgraded'] == False
    assert result['cooldown'] == 4


def test_extract_np_summary():
    """Test noble phantasm summary extraction."""
    np_data = {
        "name": "Excalibur",
        "card": "buster",
        "npDistribution": [16, 33, 51],
        "functions": [
            {
                "funcTargetType": "enemy",
                "svals": [{"Value": 600}],
                "svals2": [{"Value": 800}],
                "svals3": [{"Value": 1000}]
            }
        ]
    }
    
    result = extract_np_summary(np_data)
    
    assert result['name'] == 'Excalibur'
    assert result['card_type'] == 'buster'
    assert result['hits'] == [16, 33, 51]
    assert result['scope'] == 'enemy'
    assert 'oc_matrix' in result  # Should detect overcharge scaling


def test_detect_transforms_aoko():
    """Test transform detection for Aoko."""
    transforms = _detect_transforms(413, {})
    
    assert len(transforms) == 1
    transform = transforms[0]
    assert transform['trigger'] == 'first_np_use'
    assert transform['type'] == 'full_transform'
    assert transform['target_collection_no'] == 4132
    assert transform['preserve_cooldowns'] == True


def test_detect_transforms_no_transform():
    """Test no transforms for regular servant."""
    transforms = _detect_transforms(1, {})  # Mash
    
    assert len(transforms) == 0


def test_transforms_detection_in_select_ascension_data(sample_aoko_data):
    """Test that transforms are properly included in ascension data."""
    result = select_ascension_data(sample_aoko_data, 1)
    
    # Should have transforms section
    assert 'transforms' in result
    if result['transforms']:  # Only check if Aoko data is available
        assert len(result['transforms']) == 1
        assert result['transforms'][0]['target_collection_no'] == 4132


def test_generate_markdown_summary():
    """Test markdown summary generation."""
    canonical_data = {
        'meta': {
            'collectionNo': 1,
            'name': 'Test Servant',
            'className': 'saber',
            'classId': 1,
            'rarity': 5,
            'attribute': 'heaven'
        },
        'ascensions': [{
            'ascension_index': 3,
            'skills': [{
                'display_name': 'Test Skill',
                'cooldown': 5,
                'id': 12345,
                'upgraded': True,
                'raw_effects': [{}]
            }],
            'noblePhantasms': [{
                'name': 'Test NP',
                'card_type': 'buster',
                'hits': [100],
                'scope': 'enemy',
                'effects': [{}]
            }],
            'passives': [{
                'name': 'Test Passive',
                'id': 67890
            }]
        }],
        'transforms': [{
            'trigger': 'first_np_use',
            'type': 'full_transform',
            'target_collection_no': 9999,
            'preserve_cooldowns': True
        }]
    }
    
    markdown = generate_markdown_summary(canonical_data, 3)
    
    # Check key sections are present
    assert '# Test Servant (Collection No. 1) - Ascension 3' in markdown
    assert '**Class:** saber (ID: 1)' in markdown
    assert '**Rarity:** 5★' in markdown
    assert '### Skill 1: Test Skill (upgraded)' in markdown
    assert '### NP 1: Test NP' in markdown
    assert '## Transforms' in markdown
    assert '## Class Passives' in markdown


def test_process_servant_file_integration(tmp_path):
    """Test complete file processing integration."""
    # Create a test input file
    test_data = {
        "collectionNo": {"$numberInt": "999"},
        "name": "Test Integration Servant",
        "className": "archer",
        "classId": {"$numberInt": "2"},
        "rarity": {"$numberInt": "4"},
        "attribute": "earth",
        "skills": [{
            "id": {"$numberInt": "99999"},
            "name": "Integration Test Skill",
            "coolDown": [8, 8, 7, 7, 6, 6, 5, 5, 4, 3],
            "strengthStatus": {"$numberInt": "0"},
            "functions": [{"funcType": "healHp"}]
        }],
        "noblePhantasms": [{
            "name": "Integration Test NP",
            "card": "arts",
            "npDistribution": [100],
            "functions": [{"funcTargetType": "self"}]
        }],
        "classPassive": [],
        "traits": []
    }
    
    input_file = tmp_path / "test_servant.json"
    output_dir = tmp_path / "parsed"
    
    with open(input_file, 'w') as f:
        json.dump(test_data, f)
    
    # Process the file
    process_servant_file(str(input_file), str(output_dir))
    
    # Check outputs were created
    assert (output_dir / "999-asc1.json").exists()
    assert (output_dir / "999-asc1.md").exists()
    
    # Check JSON content
    with open(output_dir / "999-asc1.json") as f:
        result = json.load(f)
    
    assert result['meta']['collectionNo'] == 999
    assert result['meta']['name'] == 'Test Integration Servant'
    assert len(result['ascensions'][0]['skills']) == 1
    
    # Check markdown content
    with open(output_dir / "999-asc1.md") as f:
        markdown = f.read()
    
    assert 'Test Integration Servant' in markdown
    assert 'Integration Test Skill' in markdown


def test_ascension_fallback_behavior():
    """Test that requesting high ascension falls back gracefully."""
    test_data = {
        "collectionNo": {"$numberInt": "888"},
        "name": "Test Fallback",
        "className": "caster",
        "classId": {"$numberInt": "3"},
        "rarity": {"$numberInt": "3"},
        "attribute": "human",
        "skills": [],
        "noblePhantasms": [],
        "classPassive": [],
        "traits": []
    }
    
    # Should not crash when requesting ascension 10
    result = select_ascension_data(test_data, 10)
    
    # Should still return valid data structure
    assert result['meta']['collectionNo'] == 888
    assert result['ascensions'][0]['ascension_index'] == 10
    assert 'skills' in result['ascensions'][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])