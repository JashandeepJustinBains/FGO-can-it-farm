#!/usr/bin/env python3
"""Debug Mash skill candidates by costume."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from units.Servant import Servant

def debug_mash_candidates():
    """Show skill candidates for different Mash variants."""
    
    for costume_id, costume_name in [(None, "Base"), (800101, "Ortenaus"), (800102, "Paladin")]:
        print(f"=== {costume_name} (variant={costume_id or 800100}) ===")
        
        mash = Servant(1, ascension=1)
        if costume_id:
            mash.change_ascension(1, costume_svt_id=costume_id)
        
        # Look at slot 1 candidates in detail
        slot_list = mash.skills.skills.get(1, [])
        if slot_list and 'raw_candidates' in slot_list[0]:
            candidates = slot_list[0]['raw_candidates']
            print(f"Slot 1 has {len(candidates)} candidates:")
            
            # Filter candidates by svtId (this is what the selection logic does)
            variant_id = mash.variant_svt_id
            svt_matches = [s for s in candidates if s.get('svtId') == variant_id]
            print(f"  {len(svt_matches)} match current variant svtId {variant_id}")
            
            # Show the svt-filtered candidates with their names and release conditions
            for i, c in enumerate(svt_matches):
                cid = c.get('id')
                name = c.get('name', 'Unknown')
                priority = c.get('priority', 0)
                rc = c.get('releaseConditions', [])
                cond_summary = []
                for cond in rc:
                    ctype = cond.get('condType')
                    ctarget = cond.get('condTargetId')  
                    cnum = cond.get('condNum')
                    cond_summary.append(f"{ctype}:{ctarget}:{cnum}")
                print(f"    [{i}] id={cid} name={name} priority={priority} conds={cond_summary}")
            
            # Show which one gets selected
            selected = mash.skills.get_skill_by_num(1)
            print(f"  SELECTED: id={selected.get('id')} name={selected.get('name')}")
        
        print()

if __name__ == '__main__':
    debug_mash_candidates()