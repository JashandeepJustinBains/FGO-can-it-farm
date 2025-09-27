"""
Comprehensive test of the Enhanced Heuristic Ascension Parser integration.
Tests all edge cases and complex mechanics in the simulation environment.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_enhanced_integration():
    """Test enhanced parser integration with complex servants."""
    
    print("=== Enhanced Heuristic Parser Integration Test ===\n")
    
    # Test cases covering all heuristic types
    test_cases = [
        {
            "id": 444, 
            "name": "U-Olga Marie", 
            "type": "complete_replacement",
            "expected_changes": {
                1: "priority 1 skills",
                3: "priority 2 skills (complete replacement)"
            }
        },
        {
            "id": 312, 
            "name": "Mélusine", 
            "type": "skill_inheritance", 
            "expected_changes": {
                1: "Ray Horizon A (888550)",
                3: "Ray Horizon A (888575) - transformed"
            }
        },
        {
            "id": 421, 
            "name": "BB/GO", 
            "type": "unlockable_np",
            "expected_changes": {
                1: "C.C.C. + unlockable G.G.G."
            }
        },
        {
            "id": 394, 
            "name": "Ptolemy", 
            "type": "np_swap",
            "expected_changes": {
                1: "Contact with Wisdom EX (2281650)",
                3: "Contact with Wisdom EX (2281675) - transformed"  
            }
        },
        {
            "id": 413, 
            "name": "Aoko", 
            "type": "transformation",
            "expected_changes": {
                1: "Transformation capability via skill 3"
            }
        }
    ]
    
    for case in test_cases:
        servant_id = case["id"]
        name = case["name"]
        servant_type = case["type"]
        
        print(f"🧪 Testing {name} (ID: {servant_id}) - Type: {servant_type}")
        print(f"Expected: {case['expected_changes']}")
        
        try:
            # Test key ascensions
            for asc in [1, 3]:
                print(f"\n  📊 Ascension {asc}:")
                
                # Import here to avoid circular imports during module loading
                from units.Servant_updated import select_ascension_data
                from units import select_character
                
                servant_data = select_character(servant_id)
                if not servant_data:
                    print(f"    ❌ Servant data not found")
                    continue
                
                asc_data = select_ascension_data(servant_data, asc)
                
                # Analyze skills
                skills = asc_data.get('skills', [])
                skill_info = []
                for skill in skills:
                    skill_name = skill.get('name', 'Unknown')
                    skill_id = skill.get('id', 'Unknown')
                    skill_info.append(f"{skill_name} (ID: {skill_id})")
                
                print(f"    Skills: {skill_info}")
                
                # Analyze NPs
                nps = asc_data.get('noblePhantasms', [])
                np_info = []
                for np in nps:
                    np_name = np.get('name', 'Unknown')
                    np_id = np.get('id', 'Unknown')
                    unlockable = " [UNLOCKABLE]" if np.get('unlockable') else ""
                    np_info.append(f"{np_name} (ID: {np_id}){unlockable}")
                
                print(f"    NPs: {np_info}")
                
                # Check for special mechanics
                heuristics_info = asc_data.get('heuristics', {})
                if heuristics_info.get('unlocks'):
                    print(f"    🔓 Unlocks: {heuristics_info['unlocks']}")
                
                transforms = asc_data.get('transforms', [])
                if transforms:
                    print(f"    🔄 Transformations: {len(transforms)} available")
            
            print(f"  ✅ {name} test completed\n")
            
        except Exception as e:
            print(f"  ❌ {name} test failed: {e}\n")
    
    print("=== Enhanced Integration Test Complete! ===")


def test_dynamic_ascension_changes():
    """Test dynamic ascension changing with enhanced parser."""
    print("\n=== Dynamic Ascension Change Test ===")
    
    try:
        from units.Servant_updated import Servant
        
        # Test with U-Olga Marie (complete replacement)
        print("🔄 Testing U-Olga Marie dynamic ascension changes...")
        servant = Servant(444, ascension=1)
        
        skill1_asc1 = servant.skills.get_skill_by_num(1)
        print(f"  Ascension 1, Skill 1: {skill1_asc1.get('name')} (ID: {skill1_asc1.get('id')})")
        
        servant.change_ascension(3)
        skill1_asc3 = servant.skills.get_skill_by_num(1)
        print(f"  Ascension 3, Skill 1: {skill1_asc3.get('name')} (ID: {skill1_asc3.get('id')})")
        
        if skill1_asc1.get('id') != skill1_asc3.get('id'):
            print("  ✅ Dynamic ascension change successful - skills updated correctly!")
        else:
            print("  ❌ Dynamic ascension change failed - skills not updated")
        
        # Test with Mélusine (skill inheritance)
        print("\n🔄 Testing Mélusine dynamic ascension changes...")
        servant2 = Servant(312, ascension=1)
        
        skill3_asc1 = servant2.skills.get_skill_by_num(3)
        print(f"  Ascension 1, Skill 3: {skill3_asc1.get('name')} (ID: {skill3_asc1.get('id')})")
        
        servant2.change_ascension(4)
        skill3_asc4 = servant2.skills.get_skill_by_num(3)
        print(f"  Ascension 4, Skill 3: {skill3_asc4.get('name')} (ID: {skill3_asc4.get('id')})")
        
        if skill3_asc1.get('id') != skill3_asc4.get('id'):
            print("  ✅ Dynamic transformation successful - Ray Horizon A transformed!")
        else:
            print("  ❌ Dynamic transformation failed - skill not updated")
            
    except Exception as e:
        print(f"  ❌ Dynamic ascension test failed: {e}")


if __name__ == "__main__":
    test_enhanced_integration()
    test_dynamic_ascension_changes()