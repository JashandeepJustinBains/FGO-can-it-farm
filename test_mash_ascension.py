#!/usr/bin/env python3
"""Test Mash skills across ascension levels to understand condNum decoding."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from units.Servant import Servant

def test_mash_ascension_progression():
    """Test Mash skills at different ascension levels."""
    
    print("=== Mash Base Form Ascension Progression ===")
    
    for asc in range(1, 10):
        mash = Servant(1, ascension=asc)
        skill1 = mash.skills.get_skill_by_num(1)
        print(f"Asc {asc}: Slot 1 = id={skill1.get('id')} name={skill1.get('name')}")

if __name__ == '__main__':
    test_mash_ascension_progression()