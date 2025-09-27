"""
Apply manual mapping overrides into a servant JSON file by adding a non-breaking
field `variantSkillGroups` that maps human-friendly variant names to lists of
skills and noble phantasms. This script will NOT overwrite the original file
by default; it writes a new file with suffix `.with_variants.json`.

Usage:
  python scripts/apply_manual_mapping_to_servant.py example_servant_data/1.json

Assumptions made when mapping keys to variant names (change in code if needed):
- "form:asc:0" -> "default"
- "costume:800150" -> "ortenaus"
- "costume:800190" -> "paladin"

If a manual mapping key doesn't match these, it will be added under
`variantSkillGroups.customOverrides` using the raw form key.
"""
import json
import os
import sys


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 2:
        print('Usage: apply_manual_mapping_to_servant.py <servant_json_path>')
        sys.exit(2)

    servant_path = sys.argv[1]
    manual_path = os.path.join('outputs', 'manual_mappings', '1_manual_mapping.json')

    if not os.path.exists(servant_path):
        print('Servant file not found:', servant_path)
        sys.exit(1)
    if not os.path.exists(manual_path):
        print('Manual mapping not found:', manual_path)
        sys.exit(1)

    servant = load_json(servant_path)
    manual = load_json(manual_path)

    # Heuristic mapping of manual mapping form keys to friendly variant names.
    key_to_variant = {
        'form:asc:0': 'default',
        'costume:800150': 'ortenaus',
        'costume:800190': 'paladin'
    }

    variant_groups = {}
    custom_overrides = {}

    forms = manual.get('overrides', {}).get('forms', {})
    for form_key, mapping in forms.items():
        variant_name = key_to_variant.get(form_key)
        if variant_name is None:
            # strip common prefixes so the key is slightly nicer
            pretty = form_key.replace('form:', '').replace('costume:', '')
            custom_overrides[pretty] = mapping
            continue

        # normalize lists
        skills = mapping.get('skills', []) or []
        nps = mapping.get('noblePhantasms', []) or mapping.get('noblePhantasm', []) or []

        variant_groups[variant_name] = {
            'forms': [form_key],
            'skills': skills,
            'noblePhantasms': nps
        }

    if custom_overrides:
        variant_groups['customOverrides'] = custom_overrides

    # Attach the variant groups as a non-breaking field
    servant['variantSkillGroups'] = variant_groups

    out_path = servant_path.replace('.json', '.with_variants.json')
    write_json(out_path, servant)

    print('Wrote', out_path)


if __name__ == '__main__':
    main()
