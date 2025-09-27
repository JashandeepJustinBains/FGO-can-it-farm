
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from parse_servant_ascensions import create_structured_servant_data
from ascension_selector import select_ascension_data_enhanced

def validate_servant_444():
    print("=== Validating Servant 444 ===")
    with open('example_servant_data/444.json', 'r', encoding='utf-8') as f:
        servant_444 = json.load(f)
    structured = create_structured_servant_data(servant_444)
    if structured is None:
        print("ERROR: Failed to structure Servant 444")
        return
    print(f"Max Ascensions: {structured['maxAscensions']}")
    print(f"Structure Type: {structured['structureType']}")
    print(f"Skills: {len(structured['skills'])}")
    print(f"Noble Phantasms: {len(structured['noblePhantasms'])}")
    for asc in [1, 2, 3, 4]:
        asc_data = select_ascension_data_enhanced(structured, asc)
        print(f"\nAscension {asc}:")
        print(f"  Skills: {len(asc_data['skills'])}")
        print(f"  NPs: {len(asc_data['noblePhantasms'])}")
        print(f"  Traits: {len(asc_data['traits'])}")
        for skill in asc_data['skills']:
            print(f"    - {skill['name']}")

def validate_servant_312():
    print("\n=== Validating Servant 312 ===")
    with open('example_servant_data/312.json', 'r', encoding='utf-8') as f:
        servant_312 = json.load(f)
    structured = create_structured_servant_data(servant_312)
    if structured is None:
        print("ERROR: Failed to structure Servant 312")
        return
    print(f"Max Ascensions: {structured['maxAscensions']}")
    print(f"Structure Type: {structured['structureType']}")
    for asc in [1, 2, 3, 4]:
        asc_data = select_ascension_data_enhanced(structured, asc)
        print(f"\nAscension {asc}:")
        print(f"  Skills: {[s['name'] for s in asc_data['skills']]}")
        print(f"  NPs: {[np['name'] for np in asc_data['noblePhantasms']]}")

if __name__ == '__main__':
    validate_servant_444()
    validate_servant_312()
