"""
Utility to print ascension -> variant -> selected skills/NPs mapping for example servants.
Run as: python tools\variant_map.py 1 312 444

This tool WILL NOT attempt DB access. It only reads files from example_servant_data/.
"""
import sys
import os
import json

# Ensure repo root is on sys.path so local packages (units, managers, etc.) can be imported
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from units.Servant import compute_variant_svt_id
from units.skills import Skills
from units.np import NP

EXAMPLE_DIR = os.path.join(REPO_ROOT, 'example_servant_data')


def load_servant_json(collection_no):
    path = os.path.join(EXAMPLE_DIR, f"{collection_no}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def print_mapping(collection_no):
    print('='*60)
    print(f'Servant {collection_no}')
    try:
        data = load_servant_json(collection_no)
    except FileNotFoundError:
        print('  No example JSON available')
        return

    # Determine ascension levels to examine
    ascensions = [1, 2, 3, 4]

    for asc in ascensions:
        variant = compute_variant_svt_id(data, asc)
        print(f'Ascension {asc} -> variant svtId: {variant}')

        # Ascension-specific selection for skills and NPs
        # Build a temporary servant-like container to use Skills/NP parser without DB
        class DummyServant:
            def __init__(self, data, asc, variant):
                self.data = data
                self.ascension = asc
                self.variant_svt_id = variant

        dummy = DummyServant(data, asc, variant)

        # Select ascension-aware blocks if present
        from units.Servant import select_ascension_data
        asc_data = select_ascension_data(data, asc)

        # Determine skills selection
        skills_src = asc_data.get('skills', data.get('skills', []))
        skills_obj = Skills(skills_src, servant=dummy)
        print('  Skills mapping:')
        for slot in [1,2,3]:
            try:
                # Determine provenance for this slot
                provenance = 'legacy'
                selected_svt = None

                # 1) Ascension block explicit skill
                asc_skills_list = asc_data.get('skills', []) or []
                asc_skill_obj = None
                for s in asc_skills_list:
                    if int(s.get('num', 0)) == slot:
                        asc_skill_obj = s
                        break

                if asc_skill_obj is not None:
                    if 'skillSvts' in asc_skill_obj and asc_skill_obj.get('skillSvts'):
                        # nested skillSvts candidate
                        provenance = 'nested skillSvts (ascension block)'
                        # build combined candidates
                        raw_candidates = []
                        for svt in asc_skill_obj.get('skillSvts', []):
                            cand = dict(asc_skill_obj)
                            cand.update(svt)
                            cand['num'] = asc_skill_obj.get('num')
                            raw_candidates.append(cand)
                        # use Skills helper to select
                        helper = Skills([], servant=dummy)
                        selected = helper._select_skill_from_candidates(raw_candidates, dummy.variant_svt_id)
                        if selected:
                            selected_svt = selected.get('svtId') or selected.get('svtId')
                else:
                    # 2) top-level skillSvts in servant data
                    top_skill_svts = data.get('skillSvts', []) or []
                    if top_skill_svts:
                        # group by num
                        candidates = [e for e in top_skill_svts if int(e.get('num', 0)) == slot]
                        if candidates:
                            provenance = 'top-level skillSvts'
                            helper = Skills([], servant=dummy)
                            selected = helper._select_skill_from_candidates(candidates, dummy.variant_svt_id)
                            if selected:
                                selected_svt = selected.get('svtId')
                    else:
                        # 3) legacy (ascension block without skillSvts or top-level skills)
                        provenance = 'ascension skills / legacy'

                sk = skills_obj.get_skill_by_num(slot)
                svt_display = f', svtId={selected_svt}' if selected_svt is not None else ''
                print(f'    Slot {slot}: source={provenance}{svt_display}')
                try:
                    print(json.dumps(sk, indent=2, ensure_ascii=False))
                except Exception:
                    print(repr(sk))
            except Exception as e:
                print(f'    Slot {slot}: ERROR - {e}')

        # Determine NP selection
        nps_src = asc_data.get('noblePhantasms', data.get('noblePhantasms', []))
        np_obj = NP(nps_src, servant=dummy)
        print('  NPs mapping:')
        for np_entry in np_obj.nps:
            print(f'    NP new_id={np_entry.get("new_id")}, svtId={np_entry.get("svtId")}, id={np_entry.get("id")}, card={np_entry.get("card")}, imageIndex={np_entry.get("imageIndex")}, priority={np_entry.get("priority")}')
            try:
                print(json.dumps(np_entry, indent=2, ensure_ascii=False))
            except Exception:
                print(repr(np_entry))

    print('\n')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        ids = [int(x) for x in sys.argv[1:]]
    else:
        ids = [1, 312, 444]
    for cid in ids:
        print_mapping(cid)
