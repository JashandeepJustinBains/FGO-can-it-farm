import json
import sys
from pathlib import Path


def find_skill_like_nodes(obj):
    """Recursively find dict nodes that look like skills (have id and name and type)."""
    out = []
    if isinstance(obj, dict):
        if 'id' in obj and 'name' in obj and 'type' in obj:
            out.append(obj)
        for v in obj.values():
            out.extend(find_skill_like_nodes(v))
    elif isinstance(obj, list):
        for item in obj:
            out.extend(find_skill_like_nodes(item))
    return out


def main(src_path, out_dir):
    src = Path(src_path)
    j = json.loads(src.read_text(encoding='utf-8'))

    # Determine ascension keys
    asc_keys = []
    try:
        asc_map_source = j.get('extraAssets', {})
        # prefer charaGraph.ascension if present
        if 'charaGraph' in asc_map_source and 'ascension' in asc_map_source['charaGraph']:
            asc_keys = list(asc_map_source['charaGraph']['ascension'].keys())
        else:
            # fallback: spriteModel.ascension
            sm = asc_map_source.get('spriteModel', {}).get('ascension', {})
            asc_keys = list(sm.keys())
    except Exception:
        asc_keys = []

    if not asc_keys:
        # conservative default
        asc_keys = ["1", "2", "3", "4"]

    asc_keys = sorted(set(str(k) for k in asc_keys), key=lambda x: int(x))

    compact = {
        'id': j.get('id'),
        'collectionNo': j.get('collectionNo'),
        'name': j.get('name'),
        # ascensions will be deduplicated into a list; ascensionIndex maps asc key -> index in that list
        'ascensions': {},
        'ascensionIndex': {},
        'ascensionKeys': ' '.join(asc_keys),
        'metadata': {
            'asc_keys_used': asc_keys,
            'warnings': []
        }
    }

    # Traits: copy top-level traits into all ascensions
    traits = j.get('traits', [])
    trait_ids = [t['id'] for t in traits if isinstance(t, dict) and 'id' in t]
    # start with per-key containers
    for k in asc_keys:
        compact['ascensions'][k] = {'skills': [], 'noblePhantasms': [], 'traits': trait_ids.copy()}

    # Find skills and try to map them to ascensions
    skill_nodes = find_skill_like_nodes(j)
    # We will dedupe by id
    seen_skills = set()
    for s in skill_nodes:
        sid = s.get('id')
        if not sid or sid in seen_skills:
            continue
        seen_skills.add(sid)
        # heuristics: check skillSvts nums, releaseConditions in skill or skillSvts
        mapped = False
        svts = s.get('skillSvts') or []
        nums = set()
        for entry in svts:
            if isinstance(entry, dict) and 'num' in entry:
                nums.add(str(entry['num']))
            # also check releaseConditions
            for rc in entry.get('releaseConditions', []) if isinstance(entry, dict) else []:
                if rc.get('condType') == 'equipWithTargetCostume' and 'condNum' in rc:
                    nums.add(str(rc['condNum']))
        # Check releaseConditions on the skill itself
        for rc in s.get('releaseConditions', []) if isinstance(s.get('releaseConditions'), list) else []:
            if rc.get('condType') == 'equipWithTargetCostume' and 'condNum' in rc:
                nums.add(str(rc['condNum']))
        # Some skills use 'condLimitCount' to indicate ascension
        if not nums and isinstance(s.get('condLimitCount'), int) and s.get('condLimitCount')>0:
            nums.add(str(s.get('condLimitCount')))

        if nums:
            for n in nums:
                if n in compact['ascensions']:
                    compact['ascensions'][n]['skills'].append(sid)
                    mapped = True
                else:
                    # sometimes num refers to the svt.num (0-based?) try normalized
                    if n.isdigit():
                        nn = str(int(n))
                        if nn in compact['ascensions']:
                            compact['ascensions'][nn]['skills'].append(sid)
                            mapped = True
        if not mapped:
            # default: available in all ascensions
            for k in asc_keys:
                compact['ascensions'][k]['skills'].append(sid)

    # Noble Phantasms
    nps = j.get('noblePhantasms', [])
    seen_nps = set()
    for np in nps:
        npid = np.get('id')
        if not npid or npid in seen_nps:
            continue
        seen_nps.add(npid)
        nums = set()
        for entry in np.get('npSvts', []) if isinstance(np.get('npSvts'), list) else []:
            if isinstance(entry, dict) and 'num' in entry:
                nums.add(str(entry['num']))
            for rc in entry.get('releaseConditions', []) if isinstance(entry, dict) else []:
                if rc.get('condType') == 'equipWithTargetCostume' and 'condNum' in rc:
                    nums.add(str(rc['condNum']))
        for rc in np.get('releaseConditions', []) if isinstance(np.get('releaseConditions'), list) else []:
            if rc.get('condType') == 'equipWithTargetCostume' and 'condNum' in rc:
                nums.add(str(rc['condNum']))
        if nums:
            for n in nums:
                if n in compact['ascensions']:
                    compact['ascensions'][n]['noblePhantasms'].append(npid)
                else:
                    if n.isdigit():
                        nn = str(int(n))
                        if nn in compact['ascensions']:
                            compact['ascensions'][nn]['noblePhantasms'].append(npid)
        else:
            # default: all ascensions
            for k in asc_keys:
                compact['ascensions'][k]['noblePhantasms'].append(npid)

    # Deduplicate lists
    for k in asc_keys:
        for kind in ('skills','noblePhantasms','traits'):
            compact['ascensions'][k][kind] = sorted(set(compact['ascensions'][k][kind]))

    # Build deduplicated ascensions list and index map
    unique_list = []
    index_map = {}
    for k in asc_keys:
        entry = compact['ascensions'][k]
        # use tuple of tuples for hashing: (('skills', (..)), ('noblePhantasms', (...)), ('traits', (...)))
        key = (
            tuple(entry['skills']),
            tuple(entry['noblePhantasms']),
            tuple(entry['traits'])
        )
        if key in index_map:
            compact['ascensionIndex'][k] = index_map[key]
        else:
            idx = len(unique_list)
            unique_list.append(entry)
            index_map[key] = idx
            compact['ascensionIndex'][k] = idx

    # replace ascensions dict with the compact list
    compact['ascensions'] = unique_list

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    dest = out_path / f"{j.get('collectionNo', j.get('id'))}.json"
    dest.write_text(json.dumps(compact, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Wrote {dest}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: make_compact_servant.py <source_servant_json> [out_dir]')
        sys.exit(1)
    src = sys.argv[1]
    outd = sys.argv[2] if len(sys.argv) > 2 else 'servants'
    main(src, outd)
