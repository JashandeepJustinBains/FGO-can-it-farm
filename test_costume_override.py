#!/usr/bin/env python3
"""Test costume override functionality for Mash."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from units.Servant import Servant

def test_mash_costume_override():
    """Test Mash with different costume overrides."""
    
    print("=== Testing Mash Base (no costume) ===")
    mash = Servant(1, ascension=1)
    print(f"Ascension: {mash.ascension}, Variant: {mash.variant_svt_id}")
    for i in range(1, 4):
        skill = mash.skills.get_skill_by_num(i)
        print(f"  Slot {i}: id={skill.get('id')} name={skill.get('name')}")
    
    print("\n=== Testing Mash with Ortenaus Costume (800101) ===")
    mash.change_ascension(1, costume_svt_id=800101)
    print(f"Ascension: {mash.ascension}, Variant: {mash.variant_svt_id}")
    for i in range(1, 4):
        skill = mash.skills.get_skill_by_num(i)
        print(f"  Slot {i}: id={skill.get('id')} name={skill.get('name')}")
    
    print("\n=== Testing Mash with Paladin Costume (800102) ===")
    mash.change_ascension(1, costume_svt_id=800102)
    print(f"Ascension: {mash.ascension}, Variant: {mash.variant_svt_id}")
    for i in range(1, 4):
        skill = mash.skills.get_skill_by_num(i)
        print(f"  Slot {i}: id={skill.get('id')} name={skill.get('name')}")
    
    print("\n=== Testing Mash Base Higher Ascensions ===")
    for asc in [2, 3, 4]:
        mash.change_ascension(asc)
        print(f"Ascension {asc}, Variant: {mash.variant_svt_id}")
        for i in range(1, 4):
            skill = mash.skills.get_skill_by_num(i)
            print(f"  Slot {i}: id={skill.get('id')} name={skill.get('name')}")
        print()

if __name__ == '__main__':
    test_mash_costume_override()