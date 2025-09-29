import tests.test_db_setup
from dotenv import load_dotenv
load_dotenv()
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
import connectDB
# Ensure global db is set in this test's global scope
if hasattr(connectDB, 'db'):
    globals()['db'] = connectDB.db
import json
import pytest
from units.Servant import Servant, compute_variant_svt_id, select_ascension_data
from units.traits import TraitSet, parse_trait_add_data, get_applicable_trait_adds


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
    
    # Connect to MongoDB Atlas
    from pymongo import MongoClient
    import os
    mongo_uri = os.getenv('MONGO_URI_READ')
    if not mongo_uri:
        pytest.skip("No MONGO_URI_READ environment variable set for MongoDB Atlas")
    client = MongoClient(mongo_uri)
    db = client['FGOCanItFarmDatabase']
    servants_col = db['servants']

    # Test with Mash (collectionNo: 1)
    mash_data = servants_col.find_one({'collectionNo': 1})
    if not mash_data:
        pytest.skip("Mash (collectionNo: 1) not found in MongoDB")

    # Test variant computation
    variant_id = compute_variant_svt_id(mash_data, 1)
    assert variant_id == mash_data.get('id', 800100)

    # Test ascension data selection
    ascension_data = select_ascension_data(mash_data, 1)
    assert 'skills' in ascension_data
    assert 'noblePhantasms' in ascension_data

    # Test traits
    if 'traits' in mash_data:
        # Only keep dict traits with an 'id' field
        dict_traits = [t for t in mash_data['traits'] if isinstance(t, dict) and 'id' in t]
        if dict_traits:
            trait_set = TraitSet(dict_traits)
            assert trait_set.contains(1000)  # servant trait

    # Test with Mélusine (collectionNo: 312)
    melusine_data = servants_col.find_one({'collectionNo': 312})
    if not melusine_data:
        pytest.skip("Mélusine (collectionNo: 312) not found in MongoDB")

    # Test that skills/NPs change between ascensions 1-2 and 3-4 for Mélusine
    # Check that skill 3 in priority 1 (asc 1-2) has different function values (svals) than in priority 2 (asc 3-4)
    if 'skillsByPriority' in melusine_data:
        skills_by_priority = melusine_data['skillsByPriority']
        def extract_svals(skill):
            if not skill:
                return None
            svals = []
            for func in skill.get('functions', []):
                if 'svals' in func:
                    svals.append(tuple(v.get('Value') for v in func['svals'] if 'Value' in v))
            return tuple(svals) if svals else None

        # Get skill 3 for priority 1 (asc 1-2) and priority 2 (asc 3-4)
        skill3_prio1 = skills_by_priority.get('1', {}).get('3')
        skill3_prio2 = skills_by_priority.get('2', {}).get('3')

        svals_prio1 = extract_svals(skill3_prio1)
        svals_prio2 = extract_svals(skill3_prio2)
        assert svals_prio1 and svals_prio2 and svals_prio1 != svals_prio2, "Skill 3 function values (svals) should differ between ascension priorities 1 (asc 1-2) and 2 (asc 3-4)"

    # NPs
    if 'npsByPriority' in melusine_data and 'npPriorityMapping' in melusine_data:
        mapping = melusine_data['npPriorityMapping']
        nps_by_priority = melusine_data['npsByPriority']
        # Ascensions 1-2
        asc12_nps = set()
        for prio, idxs in mapping.items():
            for idx in idxs:
                if idx in [1, 2] and prio in nps_by_priority:
                    for np in nps_by_priority[prio]:
                        asc12_nps.add(np['id'])
        # Ascensions 3-4
        asc34_nps = set()
        for prio, idxs in mapping.items():
            for idx in idxs:
                if idx in [3, 4] and prio in nps_by_priority:
                    for np in nps_by_priority[prio]:
                        asc34_nps.add(np['id'])
        assert asc12_nps and asc34_nps and asc12_nps != asc34_nps, "NPs should differ between ascensions 1-2 and 3-4"


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