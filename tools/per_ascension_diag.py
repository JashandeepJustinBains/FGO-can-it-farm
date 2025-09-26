"""Per-ascension diagnostic: print raw skill candidates and NP choices for a servant.

Usage: run this script with the workspace Python. It prints, for each ascension,
- Servant variant id used
- For each skill slot: raw candidates (svtId, id, priority, condTargetId/condNum groups) and which candidate was selected by the runtime logic
- NP entries parsed and their imageIndex/priority/releaseConditions

This helps validate ascension-aware selection behavior.
"""

import json
import sys
from pprint import pprint

from units.Servant import Servant


def extract_cond_summary(cond):
    return {
        'condType': cond.get('condType'),
        'condTargetId': cond.get('condTargetId'),
        'condNum': cond.get('condNum'),
        'condGroup': cond.get('condGroup')
    }


def diag_servant(collection_no, asc_min=1, asc_max=4):
    for asc in range(asc_min, asc_max + 1):
        print('=' * 80)
        print(f"CollectionNo={collection_no}  Ascension={asc}")
        try:
            sv = Servant(collection_no, ascension=asc)
        except Exception as e:
            print(f"  ERROR constructing Servant: {e}")
            continue

        print(f"  Computed variant_svt_id: {sv.variant_svt_id}\n")

        # Skills
        print('  Skills:')
        skills_obj = sv.skills
        for slot in (1, 2, 3):
            print(f"    Slot {slot}:")
            slot_list = getattr(skills_obj, 'skills', {}).get(slot, [])
            if not slot_list:
                print('      (no skills)')
                continue

            first = slot_list[0]
            if isinstance(first, dict) and 'raw_candidates' in first:
                raw_candidates = first['raw_candidates']
                print(f"      raw_candidates: {len(raw_candidates)} candidates")
                for i, c in enumerate(raw_candidates):
                    svt = c.get('svtId')
                    cid = c.get('id') or c.get('new_id') or c.get('id')
                    pr = c.get('priority')
                    rc = c.get('releaseConditions', [])
                    conds = [extract_cond_summary(x) for x in rc]
                    # imageIndex for some skill entries may be present
                    img = c.get('imageIndex', None)
                    print(f"        [{i}] svtId={svt} id={cid} priority={pr} imageIndex={img} conds={conds}")

                # Which candidate was selected by current runtime selection?
                selected = skills_obj.get_skill_by_num(slot)
                if selected:
                    sid = selected.get('id')
                    sname = selected.get('name')
                    scool = selected.get('cooldown')
                    print(f"      Selected -> id={sid} name={sname} cooldown={scool}")
                    # Try to locate the matching raw candidate
                    matched = None
                    for c in raw_candidates:
                        if c.get('id') == sid or c.get('new_id') == sid:
                            matched = c
                            break
                    if matched:
                        print('      Matched candidate details:')
                        pprint({k: matched.get(k) for k in ['svtId','id','priority','releaseConditions','imageIndex']}, indent=8)
                    else:
                        print('      Selected parsed entry not found among raw candidates (parsed/legacy).')
                else:
                    print('      No candidate was selected (selection returned None)')

            else:
                # Legacy parsed skills
                print('      legacy parsed entries:')
                for idx, p in enumerate(slot_list):
                    print(f"        [{idx}] id={p.get('id')} name={p.get('name')} cooldown={p.get('cooldown')}")

        print('')

        # Noble Phantasms
        print('  NoblePhantasms (parsed order):')
        try:
            for i, np_entry in enumerate(sv.nps.nps):
                nid = np_entry.get('id')
                name = np_entry.get('name')
                pr = np_entry.get('priority')
                svtid = np_entry.get('svtId')
                # try to surface imageIndex from npSvts if present
                img = None
                raw_np_svts = np_entry.get('npSvts') or []
                if raw_np_svts and isinstance(raw_np_svts, list):
                    img = raw_np_svts[0].get('imageIndex')
                print(f"    [{i}] id={nid} svtId={svtid} priority={pr} imageIndex={img} name={name}")
        except Exception as e:
            print(f"    ERROR listing NPs: {e}")

        # Also print top-level skillSvts section from the servant JSON if present (helps debugging)
        print('\n  Top-level skillSvts (summary from data):')
        top_skill_svts = sv.data.get('skillSvts', [])
        if top_skill_svts:
            grouped = {}
            for e in top_skill_svts:
                num = e.get('num')
                grouped.setdefault(num, []).append(e)
            for num, entries in grouped.items():
                print(f"    slot {num}: {len(entries)} top-level entries")
                for j, ent in enumerate(entries[:8]):
                    conds = [extract_cond_summary(x) for x in ent.get('releaseConditions', [])]
                    print(f"      [{j}] svtId={ent.get('svtId')} id={ent.get('id')} priority={ent.get('priority')} conds={conds}")
        else:
            print('    (no top-level skillSvts in data)')

        print('\n')


def enhanced_diag_servant(collection_no, start_ascension=1, end_ascension=4, output_json=True, output_dir="outputs/per_ascension"):
    """
    Enhanced diagnostic that outputs both human-readable and machine-readable formats.
    
    Args:
        collection_no: Servant collection number
        start_ascension: Starting ascension to test (default 1)
        end_ascension: Ending ascension to test (default 4)
        output_json: Whether to output machine-readable JSON (default True)
        output_dir: Output directory for JSON files (default "outputs/per_ascension")
    
    Returns:
        Dictionary with diagnostic results for each ascension
    """
    import os
    import json
    from datetime import datetime
    
    # Ensure output directory exists
    if output_json:
        os.makedirs(output_dir, exist_ok=True)
    
    results = {
        "collection_no": collection_no,
        "timestamp": datetime.now().isoformat(),
        "ascensions": {}
    }
    
    print(f"=== Enhanced Diagnostic for Servant {collection_no} ===")
    
    for asc in range(start_ascension, end_ascension + 1):
        print(f"\n--- Ascension {asc} ---")
        
        try:
            # Create servant instance
            servant = Servant(collection_no, ascension=asc)
            
            asc_result = {
                "ascension": asc,
                "variant_svt_id": getattr(servant, 'variant_svt_id', None),
                "original_base_svt_id": getattr(servant, 'original_base_svt_id', None),
                "skills": {},
                "noble_phantasms": [],
                "error": None
            }
            
            # Analyze skills for each slot
            if hasattr(servant, 'skills') and servant.skills:
                for slot in [1, 2, 3]:
                    try:
                        selected_skill = servant.skills.get_skill_by_num(slot)
                        
                        asc_result["skills"][slot] = {
                            "selected_id": selected_skill.get('id') if selected_skill else None,
                            "selected_name": selected_skill.get('name') if selected_skill else None,
                            "cooldown": selected_skill.get('cooldown') if selected_skill else None
                        }
                        
                        if selected_skill:
                            print(f"  Slot {slot}: {selected_skill.get('name', 'Unknown')} (id={selected_skill.get('id')}, cooldown={selected_skill.get('cooldown')})")
                        else:
                            print(f"  Slot {slot}: No skill selected")
                        
                    except Exception as e:
                        asc_result["skills"][slot] = {"error": str(e)}
                        print(f"  Slot {slot}: ERROR - {e}")
            
            # Analyze NPs
            if hasattr(servant, 'nps') and servant.nps:
                for np in servant.nps.nps:
                    np_info = {
                        "id": np.get('id'),
                        "name": np.get('name'),
                        "new_id": np.get('new_id'),
                        "priority": np.get('priority'),
                        "svt_id": np.get('svtId')
                    }
                    asc_result["noble_phantasms"].append(np_info)
                    print(f"  NP: {np.get('name', 'Unknown')} (id={np.get('id')}, new_id={np.get('new_id')})")
            
            results["ascensions"][asc] = asc_result
            print(f"  Status: OK")
            
        except Exception as e:
            error_msg = str(e)
            results["ascensions"][asc] = {
                "ascension": asc,
                "error": error_msg
            }
            print(f"  Status: ERROR - {error_msg}")
    
    # Save JSON output
    if output_json:
        output_file = os.path.join(output_dir, f"{collection_no}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nMachine-readable output saved to: {output_file}")
    
    return results

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: per_ascension_diag.py <collectionNo> [asc_min] [asc_max]')
        sys.exit(1)
    col = int(sys.argv[1])
    amin = int(sys.argv[2]) if len(sys.argv) >= 3 else 1
    amax = int(sys.argv[3]) if len(sys.argv) >= 4 else 4
    diag_servant(col, amin, amax)
