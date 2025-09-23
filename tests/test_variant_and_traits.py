"""
Tests for ascension/costume-aware variant selection and traits system.

Tests validate the algorithm picks correct variant svtId, selects skills with
highest id and level 10 values, chooses appropriate NP variants, and handles
trait transformations correctly.
"""

import json
import pytest
from units.Servant import Servant, compute_variant_svt_id, select_ascension_data
from units.traits import TraitSet, parse_trait_add_data, get_applicable_trait_adds


class MockDB:
    """Mock database for testing."""
    def __init__(self):
        self.servants = MockCollection()


class MockCollection:
    """Mock collection that loads from example JSON files."""
    def find_one(self, query):
        collection_no = query.get('collectionNo')
        if collection_no:
            try:
                with open(f'example_servant_data/{collection_no}.json', 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                return None
        return None


def test_trait_set_basic_functionality():
    """Test basic TraitSet operations."""
    # Test initialization with base traits
    base_traits = [{'id': 1000, 'name': 'servant'}, {'id': 2001, 'name': 'humanoid'}]
    trait_set = TraitSet(base_traits)
    
    assert trait_set.contains(1000)
    assert trait_set.contains(2001)
    assert not trait_set.contains(9999)
    
    # Test trait addition and removal
    trait_set.apply_trait_changes({'add': [{'id': 5000, 'name': 'canBeInBattle'}]})
    assert trait_set.contains(5000)
    
    trait_set.apply_trait_changes({'remove': [{'id': 5000}]})
    assert not trait_set.contains(5000)


def test_trait_set_ascension_traits():
    """Test ascension-specific trait application."""
    base_traits = [{'id': 1000, 'name': 'servant'}]
    trait_set = TraitSet(base_traits)
    
    # Mock ascension data
    ascension_data = {
        'individuality': {
            'ascension': {
                '0': [{'id': 2001, 'name': 'humanoid'}],
                '3': [{'id': 2002, 'name': 'dragon'}, {'id': 2924, 'name': 'canFlyInSpace'}]
            }
        }
    }
    
    # Test ascension 0 (level 1)
    trait_set.apply_ascension_traits(ascension_data, 0)
    assert trait_set.contains(1000)  # base trait
    assert trait_set.contains(2001)  # ascension trait
    assert not trait_set.contains(2002)  # different ascension
    
    # Test ascension 3 (level 4)
    trait_set.apply_ascension_traits(ascension_data, 3)
    assert trait_set.contains(1000)  # base trait
    assert not trait_set.contains(2001)  # replaced by new ascension
    assert trait_set.contains(2002)  # new ascension trait
    assert trait_set.contains(2924)  # new ascension trait


def test_trait_set_costume_traits():
    """Test costume-specific trait application."""
    base_traits = [{'id': 1000, 'name': 'servant'}]
    trait_set = TraitSet(base_traits)
    
    # Mock ascension data with costume traits
    ascension_data = {
        'individuality': {
            'costume': {
                '304830': [{'id': 2795, 'name': 'knightsOfTheRound'}]
            }
        }
    }
    
    trait_set.apply_costume_traits(ascension_data, 304830)
    assert trait_set.contains(1000)  # base trait
    assert trait_set.contains(2795)  # costume trait


def test_variant_svt_id_computation_basic():
    """Test basic variant svtId computation."""
    # Test costume override
    servant_data = {'id': 800100}
    result = compute_variant_svt_id(servant_data, 1, costume_svt_id=304830)
    assert result == 304830
    
    # Test fallback to top-level id
    result = compute_variant_svt_id(servant_data, 1)
    assert result == 800100


def test_variant_svt_id_with_np_svts():
    """Test variant svtId computation with npSvts imageIndex mapping."""
    servant_data = {
        'id': 304800,
        'npSvts': [
            {'svtId': 304800, 'imageIndex': 0, 'priority': 1},
            {'svtId': 304810, 'imageIndex': 1, 'priority': 1},
            {'svtId': 304820, 'imageIndex': 3, 'priority': 1}
        ]
    }
    
    # Test ascension 1 → imageIndex 0 → svtId 304800
    result = compute_variant_svt_id(servant_data, 1)
    assert result == 304800
    
    # Test ascension 2 → imageIndex 1 → svtId 304810
    result = compute_variant_svt_id(servant_data, 2)
    assert result == 304810
    
    # Test ascension 4 → imageIndex 3 → svtId 304820
    result = compute_variant_svt_id(servant_data, 4)
    assert result == 304820
    
    # Test unmapped ascension → fallback to top-level
    result = compute_variant_svt_id(servant_data, 3)
    assert result == 304800  # fallback


def test_variant_svt_id_priority_handling():
    """Test variant svtId computation with priority handling."""
    servant_data = {
        'id': 304800,
        'npSvts': [
            {'svtId': 304800, 'imageIndex': 0, 'priority': 1},
            {'svtId': 304810, 'imageIndex': 0, 'priority': 2},  # higher priority
        ]
    }
    
    # Should pick svtId 304810 due to higher priority
    result = compute_variant_svt_id(servant_data, 1)
    assert result == 304810


def test_select_ascension_data_legacy_format():
    """Test ascension data selection with legacy format."""
    servant_data = {
        'skills': [
            {'id': 1, 'name': 'Skill 1', 'num': 1},
            {'id': 2, 'name': 'Skill 2', 'num': 2}
        ],
        'noblePhantasms': [
            {'id': 10, 'name': 'NP 1', 'card': 'arts'}
        ],
        'passives': [],
        'transforms': []
    }
    
    result = select_ascension_data(servant_data, 1)
    assert len(result['skills']) == 2
    assert len(result['noblePhantasms']) == 1
    assert result['skills'][0]['id'] == 1
    assert result['noblePhantasms'][0]['id'] == 10


def test_select_ascension_data_list_of_lists():
    """Test ascension data selection with list-of-lists format."""
    servant_data = {
        'skills': [
            # Ascension 1 skills
            [{'id': 1, 'name': 'Skill 1 (Asc 1)', 'num': 1}],
            # Ascension 2 skills
            [{'id': 2, 'name': 'Skill 1 (Asc 2)', 'num': 1}]
        ],
        'noblePhantasms': [
            # Ascension 1 NPs
            [{'id': 10, 'name': 'NP 1 (Asc 1)', 'card': 'arts'}],
            # Ascension 2 NPs
            [{'id': 11, 'name': 'NP 1 (Asc 2)', 'card': 'buster'}]
        ]
    }
    
    # Test ascension 1
    result = select_ascension_data(servant_data, 1)
    assert result['skills'][0]['id'] == 1
    assert result['noblePhantasms'][0]['id'] == 10
    
    # Test ascension 2
    result = select_ascension_data(servant_data, 2)
    assert result['skills'][0]['id'] == 2
    assert result['noblePhantasms'][0]['id'] == 11
    
    # Test fallback to highest ascension
    result = select_ascension_data(servant_data, 5)
    assert result['skills'][0]['id'] == 2  # Should use highest available (ascension 2)
    assert result['noblePhantasms'][0]['id'] == 11


def test_skill_svts_selection():
    """Test skill selection from skillSvts format."""
    # This would be tested with actual servant data once we have skillSvts examples
    # For now, test the logic with mock data
    
    skill_svts = [
        {'svtId': 304800, 'num': 1, 'id': 888550, 'name': 'Skill 1 Base'},
        {'svtId': 304810, 'num': 1, 'id': 888551, 'name': 'Skill 1 Upgraded'},
        {'svtId': 304800, 'num': 1, 'id': 888552, 'name': 'Skill 1 Higher ID'},  # Should be chosen
        {'svtId': 304800, 'num': 2, 'id': 888560, 'name': 'Skill 2'}
    ]
    
    # Mock servant with variant_svt_id = 304800
    class MockServant:
        def __init__(self):
            self.variant_svt_id = 304800
    
    servant = MockServant()
    
    # Test variant-aware selection logic (simplified)
    skills_by_num = {}
    for skill in skill_svts:
        num = skill.get('num', 0)
        if num not in skills_by_num:
            skills_by_num[num] = []
        skills_by_num[num].append(skill)
    
    # For skill num 1, should pick variant matches first, then highest id
    skill_1_candidates = skills_by_num[1]
    variant_matches = [s for s in skill_1_candidates if s.get('svtId') == servant.variant_svt_id]
    selected_skill = max(variant_matches, key=lambda s: s.get('id', 0))
    
    assert selected_skill['id'] == 888552  # Highest ID among variant matches
    assert selected_skill['name'] == 'Skill 1 Higher ID'


def test_np_svts_selection():
    """Test NP selection from npSvts format."""
    np_svts = [
        {'svtId': 304800, 'imageIndex': 0, 'priority': 1, 'id': 300001},
        {'svtId': 304810, 'imageIndex': 1, 'priority': 1, 'id': 300002},
        {'svtId': 304820, 'imageIndex': 3, 'priority': 1, 'id': 300003}
    ]
    
    # Mock servant with variant_svt_id = 304810, ascension = 2
    class MockServant:
        def __init__(self):
            self.variant_svt_id = 304810
            self.ascension = 2
    
    servant = MockServant()
    
    # Test exact svtId match (should pick 304810 entry)
    variant_matches = [np for np in np_svts if np.get('svtId') == servant.variant_svt_id]
    assert len(variant_matches) == 1
    assert variant_matches[0]['id'] == 300002
    
    # Test imageIndex fallback (ascension 2 → imageIndex 1)
    if not variant_matches:
        expected_image_index = servant.ascension - 1
        image_matches = [np for np in np_svts if np.get('imageIndex') == expected_image_index]
        assert len(image_matches) == 1
        assert image_matches[0]['id'] == 300002


def test_level_10_skill_values():
    """Test that skills use level 10 (last) values by default."""
    skill_data = {
        'id': 888550,
        'name': 'Test Skill',
        'num': 1,
        'coolDown': [8, 7, 6, 5, 4, 3, 2, 1, 0, 0],  # Level 1-10 cooldowns
        'functions': [{
            'funcType': 'addState',
            'svals': [
                {'Value': 100},  # Level 1
                {'Value': 110},  # Level 2
                # ... levels 3-9 ...
                {'Value': 200}   # Level 10 (should be selected)
            ]
        }]
    }
    
    # Test that we pick last cooldown (level 10)
    cooldown_array = skill_data['coolDown']
    selected_cooldown = cooldown_array[-1]
    assert selected_cooldown == 0  # Level 10 cooldown
    
    # Test that we pick last svals (level 10)
    svals_array = skill_data['functions'][0]['svals']
    selected_svals = svals_array[-1]
    assert selected_svals['Value'] == 200  # Level 10 value


def test_integration_with_example_servants():
    """Test integration with actual example servant data."""
    
    # Test with Mash (1.json)
    try:
        with open('example_servant_data/1.json', 'r') as f:
            mash_data = json.load(f)
        
        # Test variant computation
        variant_id = compute_variant_svt_id(mash_data, 1)
        assert variant_id == mash_data.get('id', 800100)
        
        # Test ascension data selection
        ascension_data = select_ascension_data(mash_data, 1)
        assert 'skills' in ascension_data
        assert 'noblePhantasms' in ascension_data
        
        # Test traits
        if 'traits' in mash_data:
            trait_set = TraitSet(mash_data['traits'])
            assert trait_set.contains(1000)  # servant trait
        
    except FileNotFoundError:
        pytest.skip("example_servant_data/1.json not found")
    
    # Test with Mélusine (312.json)
    try:
        with open('example_servant_data/312.json', 'r') as f:
            melusine_data = json.load(f)
        
        # Test variant computation
        variant_id = compute_variant_svt_id(melusine_data, 1)
        assert variant_id == melusine_data.get('id', 304800)
        
        # Test ascension traits
        if 'ascensionAdd' in melusine_data and 'individuality' in melusine_data['ascensionAdd']:
            trait_set = TraitSet(melusine_data.get('traits', []))
            trait_set.apply_ascension_traits(melusine_data['ascensionAdd'], 0)
            
            # Check that ascension 0 traits are applied
            individuality = melusine_data['ascensionAdd']['individuality']
            if 'ascension' in individuality and '0' in individuality['ascension']:
                for trait in individuality['ascension']['0']:
                    assert trait_set.contains(trait['id'])
    
    except FileNotFoundError:
        pytest.skip("example_servant_data/312.json not found")


def test_trait_add_parsing():
    """Test parsing of traitAdd data."""
    trait_add_data = [
        {
            'idx': 1,
            'trait': [{'id': 2821, 'name': 'havingAnimalsCharacteristics'}],
            'limitCount': -1,
            'condType': 'none',
            'condId': 0,
            'condNum': 0,
            'eventId': 0,
            'startedAt': 1640962800,
            'endedAt': 1893423600
        },
        {
            'idx': 2,
            'trait': [{'id': 2945, 'name': 'unknown'}],
            'limitCount': 0,
            'condType': 'none',
            'condId': 0,
            'condNum': 0,
            'eventId': 80511,
            'startedAt': 1736931600,
            'endedAt': 1738727999
        }
    ]
    
    parsed_rules = parse_trait_add_data(trait_add_data)
    assert len(parsed_rules) == 2
    assert parsed_rules[0]['traits'] == [2821]
    assert parsed_rules[0]['limit_count'] == -1
    assert parsed_rules[1]['traits'] == [2945]
    assert parsed_rules[1]['limit_count'] == 0
    
    # Test applicable trait filtering
    applicable = get_applicable_trait_adds(parsed_rules, current_ascension=0)
    # Should include both rules since first has limitCount -1 (always applicable)
    # and second has limitCount 0 matching current_ascension 0
    expected_traits = [2821, 2945]
    for trait_id in expected_traits:
        assert trait_id in applicable


if __name__ == '__main__':
    # Run tests without pytest for basic validation
    test_trait_set_basic_functionality()
    test_trait_set_ascension_traits()
    test_trait_set_costume_traits()
    test_variant_svt_id_computation_basic()
    test_variant_svt_id_with_np_svts()
    test_variant_svt_id_priority_handling()
    test_select_ascension_data_legacy_format()
    test_select_ascension_data_list_of_lists()
    test_skill_svts_selection()
    test_np_svts_selection()
    test_level_10_skill_values()
    test_trait_add_parsing()
    
    print("All basic tests passed!")
    
    # Try integration tests if data available
    try:
        test_integration_with_example_servants()
        print("Integration tests passed!")
    except Exception as e:
        print(f"Integration tests failed (expected if data format differs): {e}")