"""
Dump ascension -> variant -> selected full skill/NP JSON mappings to files under outputs/variant_mappings/
Usage:
  python tools\variant_map_dump.py 1 312 444

This will produce outputs/variant_mappings/1.json, 312.json, 444.json
"""
import sys
import os
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from units.Servant import compute_variant_svt_id, select_ascension_data
from units.skills import Skills
from units.np import NP

EXAMPLE_DIR = os.path.join(REPO_ROOT, 'example_servant_data')
OUT_DIR = os.path.join(REPO_ROOT, 'outputs', 'variant_mappings')

os.makedirs(OUT_DIR, exist_ok=True)


def load_servant_json(collection_no):
    path = os.path.join(EXAMPLE_DIR, f"{collection_no}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def mapping_for_servant(collection_no):
    data = load_servant_json(collection_no)
    result = {'collectionNo': collection_no, 'ascensions': {}}
    ascensions = [1,2,3,4]
    for asc in ascensions:
        variant = compute_variant_svt_id(data, asc)
        dummy = type('DummyServant', (), {'data': data, 'ascension': asc, 'variant_svt_id': variant})()
        asc_data = select_ascension_data(data, asc)
        skills_src = asc_data.get('skills', data.get('skills', []))
        skills_obj = Skills(skills_src, servant=dummy)
        skills_map = {}
        for slot in [1,2,3]:
            try:
                sk = skills_obj.get_skill_by_num(slot)
                skills_map[str(slot)] = sk
            except Exception as e:
                skills_map[str(slot)] = {'error': str(e)}
        nps_src = asc_data.get('noblePhantasms', data.get('noblePhantasms', []))
        np_obj = NP(nps_src, servant=dummy)
        nps_map = np_obj.nps
        result['ascensions'][str(asc)] = {
            'variant_svt_id': variant,
            'skills': skills_map,
            'noblePhantasms': nps_map
        }
    return result


if __name__ == '__main__':
    ids = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [1,312,444]
    for cid in ids:
        try:
            mapping = mapping_for_servant(cid)
            out_path = os.path.join(OUT_DIR, f"{cid}.json")
            with open(out_path, 'w', encoding='utf-8') as fh:
                json.dump(mapping, fh, indent=2, ensure_ascii=False)
            print(f'WROTE {out_path}')
        except Exception as e:
            print(f'ERROR for {cid}: {e}')
