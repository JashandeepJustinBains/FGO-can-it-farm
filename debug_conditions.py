#!/usr/bin/env python3
"""Debug the costume condition logic in detail."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from units.Servant import Servant

def debug_costume_conditions():
    """Debug condition checking for costume overrides."""
    
    print("=== Debug Ortenaus Condition Checking ===")
    mash = Servant(1, ascension=1)
    print(f"Before costume change: variant={mash.variant_svt_id}")
    mash.change_ascension(1, costume_svt_id=800101)
    print(f"After costume change: variant={mash.variant_svt_id}")
    
    # Get candidates for slot 1 FROM THE NEW SKILLS OBJECT
    slot_list = mash.skills.skills.get(1, [])
    if slot_list and 'raw_candidates' in slot_list[0]:
        candidates = slot_list[0]['raw_candidates']
        
        # Filter by svtId first (what current logic does after release conditions)
        variant_id = mash.variant_svt_id
        print(f"Current variant: {variant_id}")
        
        # Check release conditions for key skills
        key_skills = {
            744450: "Black Barrel B",
            2476450: "誉れ高き雪花の盾 B",
            236000: "Honorable Wall of Snowflakes"
        }
        
        for candidate in candidates:
            skill_id = candidate.get('id')
            if skill_id in key_skills:
                print(f"\nSkill: {key_skills[skill_id]} (id={skill_id})")
                print(f"  svtId: {candidate.get('svtId')}")
                print(f"  priority: {candidate.get('priority')}")
                
                # Check release conditions manually
                conditions = candidate.get('releaseConditions', [])
                if not conditions:
                    print(f"  No release conditions -> AVAILABLE")
                else:
                    for i, cond in enumerate(conditions):
                        ctype = cond.get('condType')
                        ctarget = cond.get('condTargetId')
                        cnum = cond.get('condNum')
                        print(f"  Condition {i}: {ctype} target={ctarget} num={cnum}")
                        
                        # Check this condition manually using the NEW skills object
                        result = mash.skills._check_skill_release_condition(cond)
                        print(f"    -> {result}")
                    
                    # Check if ALL conditions in group 0 pass using the NEW skills object
                    group_0_conds = [c for c in conditions if c.get('condGroup', 0) == 0]
                    all_pass = all(mash.skills._check_skill_release_condition(c) for c in group_0_conds)
                    print(f"  Overall group 0 result: {all_pass}")

if __name__ == '__main__':
    debug_costume_conditions()