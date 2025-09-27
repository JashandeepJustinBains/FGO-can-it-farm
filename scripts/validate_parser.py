"""
Complete validation script for the corrected ascension parser.
"""

import json
from scripts.parse_servant_ascensions_corrected import (
    create_structured_servant_data,
    select_ascension_data_enhanced
)

def test_servant_444():
    """Test servant 444 (U-Olga Marie) - priority replacement pattern."""
    print("=== Validating Servant 444 ===")
    
    with open('example_servant_data/444.json', 'r', encoding='utf-8') as f:
        servant_444 = json.load(f)
    
    structured_444 = create_structured_servant_data(servant_444)
    
    print(f"Max Ascensions: {structured_444['maxAscensions']}")
    print(f"Structure Type: priority-based")
    print(f"Skills by priority: {list(structured_444['skillsByPriority'].keys())}")
    print(f"NPs by priority: {list(structured_444['npsByPriority'].keys())}")
    
    # Test ascension selection
    for asc in [1, 2, 3, 4]:
        asc_data = select_ascension_data_enhanced(structured_444, asc)
        print(f"\nAscension {asc}:")
        print(f"  Skills: {len(asc_data['skills'])}")
        print(f"  NPs: {len(asc_data['noblePhantasms'])}")
        print(f"  Traits: {len(asc_data['traits'])}")
        
        for skill in asc_data['skills']:
            skill_name = skill.get('name', f"[Unicode - ID {skill.get('id')}]")
            try:
                print(f"    - {skill_name}")
            except UnicodeEncodeError:
                print(f"    - [Unicode Skill - ID {skill.get('id')}]")

def test_servant_312():
    """Test servant 312 (Mélusine) - skill inheritance with slot replacement."""
    print("\n=== Validating Servant 312 ===")
    
    with open('example_servant_data/312.json', 'r', encoding='utf-8') as f:
        servant_312 = json.load(f)
    
    structured_312 = create_structured_servant_data(servant_312)
    
    print(f"Max Ascensions: {structured_312['maxAscensions']}")
    print(f"Structure Type: priority-based")
    print(f"Skills by priority: {list(structured_312['skillsByPriority'].keys())}")
    print(f"NPs by priority: {list(structured_312['npsByPriority'].keys())}")
    
    # Test ascension selection
    for asc in [1, 2, 3, 4]:
        asc_data = select_ascension_data_enhanced(structured_312, asc)
        print(f"\nAscension {asc}:")
        
        skill_names = []
        for skill in asc_data['skills']:
            skill_names.append(skill.get('name', f"[ID {skill.get('id')}]"))
        print(f"  Skills: {skill_names}")
        
        np_names = []
        for np in asc_data['noblePhantasms']:
            np_names.append(np.get('name', f"[ID {np.get('id')}]"))
        print(f"  NPs: {np_names}")

def validate_parsing():
    """Run validation tests."""
    test_servant_444()
    test_servant_312()
    print("\n=== Validation Complete ===")

if __name__ == '__main__':
    validate_parsing()