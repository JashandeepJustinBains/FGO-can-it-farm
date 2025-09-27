#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from units.Servant import Servant

def test_servant_ascensions(servant_id, servant_name):
    """Test a servant across all ascensions"""
    print(f"\nTesting {servant_name} (ID: {servant_id}):")
    
    for asc in range(1, 5):
        try:
            servant = Servant(servant_id, ascension=asc)
            skills = servant.skills.get_skill_names() if hasattr(servant.skills, 'get_skill_names') else []
            np_name = servant.nps.nps[0]['name'] if servant.nps.nps else "No NP"
            traits_count = len(servant.traits.trait_list) if hasattr(servant.traits, 'trait_list') else 0
            
            print(f"  Ascension {asc}:")
            print(f"    Skills: {skills}")
            print(f"    NP: {np_name}")
            print(f"    Traits count: {traits_count}")
            
        except Exception as e:
            print(f"  Ascension {asc}: Error - {e}")

def main():
    print("Testing additional servants with complex mechanics...")
    
    # Test Ptolemaîos (394) - Should have NP swap mechanics
    test_servant_ascensions(394, "Ptolemaîos")
    
    # Test Jade Rabbit (448) - Should have NP/skill swap mechanics  
    test_servant_ascensions(448, "Jade Rabbit")
    
    # Test dynamic ascension changes for these servants
    print("\n" + "="*50)
    print("Testing dynamic ascension changes...")
    
    # Test Ptolemaîos dynamic changes
    try:
        print("\nPtolemaîos dynamic test:")
        servant = Servant(394, ascension=1)
        initial_np = servant.nps.nps[0]['name'] if servant.nps.nps else "No NP"
        print(f"Initial ascension 1 - NP: {initial_np}")
        
        servant.change_ascension(3)
        changed_np = servant.nps.nps[0]['name'] if servant.nps.nps else "No NP"
        print(f"Changed to ascension 3 - NP: {changed_np}")
        
        if initial_np != changed_np:
            print("✅ Ptolemaîos NP change detected!")
        else:
            print("⚠️ Ptolemaîos NP remained the same")
            
    except Exception as e:
        print(f"Ptolemaîos dynamic test failed: {e}")
    
    # Test Jade Rabbit dynamic changes
    try:
        print("\nJade Rabbit dynamic test:")
        servant = Servant(448, ascension=1)
        initial_skill = servant.skills.get_skill_names()[0] if servant.skills.get_skill_names() else "No skill"
        initial_np = servant.nps.nps[0]['name'] if servant.nps.nps else "No NP"
        print(f"Initial ascension 1 - First skill: {initial_skill}, NP: {initial_np}")
        
        servant.change_ascension(3)
        changed_skill = servant.skills.get_skill_names()[0] if servant.skills.get_skill_names() else "No skill"
        changed_np = servant.nps.nps[0]['name'] if servant.nps.nps else "No NP"
        print(f"Changed to ascension 3 - First skill: {changed_skill}, NP: {changed_np}")
        
        if initial_skill != changed_skill or initial_np != changed_np:
            print("✅ Jade Rabbit changes detected!")
        else:
            print("⚠️ Jade Rabbit remained the same")
            
    except Exception as e:
        print(f"Jade Rabbit dynamic test failed: {e}")
    
    print("\nAdditional servant testing complete!")

if __name__ == "__main__":
    main()