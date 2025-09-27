import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PER_ASC_PATH = ROOT / 'outputs' / 'per_ascension'
MANUAL_PATH = ROOT / 'outputs' / 'manual_mappings'


def load_json(p: Path):
    with p.open('r', encoding='utf-8') as f:
        return json.load(f)


def save_json(p: Path, data):
    with p.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def apply_manual(mapping_file: Path):
    manual = load_json(mapping_file)
    collection_no = str(manual.get('collectionNo') or manual.get('id'))
    # find per_ascension file by collectionNo (filename is collectionNo.json)
    target_file = PER_ASC_PATH / f"{collection_no}.json"
    if not target_file.exists():
        # fallback to id key
        target_file = PER_ASC_PATH / f"{manual.get('id')}.json"
        if not target_file.exists():
            print(f"No per_ascension file found for manual mapping {mapping_file}")
            return

    per = load_json(target_file)

    overrides = manual.get('overrides', {}).get('forms', {})
    # normalize keys in overrides (allow both "costume:800130" and "800130")
    def norm_key(k):
        if k.startswith('form:'):
            return k[len('form:'):]
        return k

    for form in per.get('forms', []):
        fid = form.get('form_id')
        # check direct match
        if fid in overrides:
            o = overrides[fid]
        else:
            # try normalized matches
            short = fid
            if fid.startswith('form:'):
                short = fid[len('form:'):]
            if short in overrides:
                o = overrides[short]
            else:
                o = None

        if not o:
            continue

        # apply skills override
        if 'skills' in o:
            # replace skills array with mapped ids -> items with matched_forms set
            new_skills = []
            ids = set(o['skills'] or [])
            for s in form.get('skills', []):
                sid = s.get('skill', {}).get('id')
                if sid in ids:
                    s['matched_forms'] = [fid]
                new_skills.append(s)
            # add any skills that weren't present
            present_ids = {s.get('skill', {}).get('id') for s in new_skills}
            for sid in ids - present_ids:
                new_skills.append({
                    'skill': {'id': sid, 'name': ''},
                    'matched_forms': [fid]
                })
            form['skills'] = new_skills

        # apply noblePhantasms override
        if 'noblePhantasms' in o or 'noblePhantasms' in o:
            ids = set(o.get('noblePhantasms', []) or [])
            new_nps = []
            for np in form.get('np', []):
                nid = np.get('np', {}).get('id')
                if nid in ids:
                    np['matched_forms'] = [fid]
                new_nps.append(np)
            present_ids = {n.get('np', {}).get('id') for n in new_nps}
            for nid in ids - present_ids:
                new_nps.append({
                    'np': {'id': nid, 'name': ''},
                    'matched_forms': [fid]
                })
            form['np'] = new_nps

    save_json(target_file, per)
    print(f"Applied manual mapping {mapping_file} -> {target_file}")


if __name__ == '__main__':
    # apply all manual mappings in the manual_mappings folder
    for p in sorted(MANUAL_PATH.glob('*.json')):
        apply_manual(p)
