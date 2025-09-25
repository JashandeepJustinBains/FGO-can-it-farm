#!/usr/bin/env python3
"""Examine all Mash skill candidates to understand costume logic."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from units.Servant import Servant

def examine_all_candidates():
    """Show all skill candidates for Mash with detailed conditions."""
    
    mash = Servant(1, ascension=1)
    
    slot_list = mash.skills.skills.get(1, [])
    if slot_list and 'raw_candidates' in slot_list[0]:
        candidates = slot_list[0]['raw_candidates']
        print(f"All {len(candidates)} candidates for Mash slot 1:\n")
        
        for i, c in enumerate(candidates):
            svt_id = c.get('svtId')
            cid = c.get('id')
            name = c.get('name', 'Unknown')
            priority = c.get('priority', 0)
            rc = c.get('releaseConditions', [])
            
            print(f"[{i:2d}] id={cid} svtId={svt_id} priority={priority}")
            print(f"     name: {name}")
            
            if rc:
                print(f"     conditions:")
                for j, cond in enumerate(rc):
                    ctype = cond.get('condType')
                    ctarget = cond.get('condTargetId')  
                    cnum = cond.get('condNum')
                    cgroup = cond.get('condGroup', 0)
                    print(f"       [{j}] {ctype} target={ctarget} num={cnum} group={cgroup}")
            else:
                print(f"     conditions: none")
            print()

if __name__ == '__main__':
    examine_all_candidates()