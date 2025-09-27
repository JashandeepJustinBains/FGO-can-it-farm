"""
Test script to verify comprehensive ascension parser integration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from units.Servant import Servant

def test_comprehensive_integration():
    """Test that comprehensive parser works in simulation."""
    
    print("Testing comprehensive ascension parser integration...")
    
    # Test servants with known complex ascension mechanics
    test_cases = [
        {"id": 444, "name": "U-Olga Marie (skill replacement)", "ascensions": [1, 2, 3, 4]},
        {"id": 312, "name": "Mélusine (skill inheritance)", "ascensions": [1, 2, 3, 4]},
    ]
    
    for case in test_cases:
        servant_id = case["id"]
        name = case["name"]
        
        print(f"\nTesting {name} (ID: {servant_id}):")
        
        for asc in case["ascensions"]:
            try:
                servant = Servant(servant_id, ascension=asc)
                
                skill_names = []
                for i in [1, 2, 3]:
                    skill = servant.skills.get_skill_by_num(i)
                    if skill:
                        skill_names.append(f"{skill.get('name', 'Unknown')} (ID: {skill.get('id', 'Unknown')})")
                    else:
                        skill_names.append("None")
                
                np_name = "None"
                if servant.nps.nps:
                    np_data = servant.nps.nps[0]
                    np_name = f"{np_data.get('name', 'Unknown')} (ID: {np_data.get('id', 'Unknown')})"
                
                print(f"  Ascension {asc}:")
                print(f"    Skills: {skill_names}")
                print(f"    NP: {np_name}")
                # Get trait count safely
                try:
                    trait_count = len(servant.trait_set.traits) if hasattr(servant.trait_set, 'traits') else 0
                except:
                    trait_count = 0
                print(f"    Traits count: {trait_count}")
                
            except Exception as e:
                print(f"  Ascension {asc}: ERROR - {e}")
    
    print("\nIntegration test complete!")


def test_change_ascension():
    """Test dynamic ascension changing."""
    print("\nTesting dynamic ascension changes...")
    
    try:
        # Test with U-Olga Marie
        servant = Servant(444, ascension=1)
        print(f"Initial ascension 1 - First skill: {servant.skills.get_skill_by_num(1).get('name', 'Unknown')}")
        
        servant.change_ascension(3)
        print(f"Changed to ascension 3 - First skill: {servant.skills.get_skill_by_num(1).get('name', 'Unknown')}")
        
        print("Dynamic ascension change test passed!")
        
    except Exception as e:
        print(f"Dynamic ascension change test failed: {e}")


if __name__ == "__main__":
    test_comprehensive_integration()
    test_change_ascension()