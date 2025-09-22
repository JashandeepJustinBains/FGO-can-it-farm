#!/usr/bin/env python3
"""Download servant JSON files from a public R2 root and produce a discovery_report.json.

The script will try a manifest/index if present, otherwise it will probe numeric filenames 1..N and stop after consecutive misses.
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict
from urllib.parse import urljoin

try:
    import requests
except Exception:
    print(json.dumps({'error': 'missing_dependency', 'message': 'requests required'}))
    sys.exit(2)


def fetch_url(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)


def find_functions(obj):
    """Recursively yield dicts that look like function/effect objects (contain 'funcType')."""
    if isinstance(obj, dict):
        if 'funcType' in obj:
            yield obj
        for v in obj.values():
            yield from find_functions(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_functions(item)


def safe_load_json(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--r2-root', required=True, help='Public R2 root URL (must end with /)')
    parser.add_argument('--out', default='discovery_report.json')
    parser.add_argument('--outdir', default='downloaded_servants')
    parser.add_argument('--max-id', type=int, default=5000)
    parser.add_argument('--stop-after-misses', type=int, default=200)
    args = parser.parse_args()

    r2 = args.r2_root
    if not r2.endswith('/'):
        r2 += '/'

    os.makedirs(args.outdir, exist_ok=True)

    docs = []
    # Try common manifest names first
    manifest_names = ['index.json', 'manifest.json', 'files.json']
    found_manifest = None
    for name in manifest_names:
        status, text = fetch_url(urljoin(r2, name))
        if status == 200:
            data = safe_load_json(text)
            if isinstance(data, list):
                found_manifest = [f for f in data]
            elif isinstance(data, dict) and 'files' in data and isinstance(data['files'], list):
                found_manifest = data['files']
            break

    if found_manifest:
        file_urls = []
        for entry in found_manifest:
            if isinstance(entry, str):
                file_urls.append(urljoin(r2, entry))
            elif isinstance(entry, dict) and 'path' in entry:
                file_urls.append(urljoin(r2, entry['path']))
    else:
        # Probe numeric filenames
        file_urls = []
        misses = 0
        for i in range(1, args.max_id + 1):
            candidate = urljoin(r2, f"{i}.json")
            status, text = fetch_url(candidate, timeout=5)
            if status == 200:
                file_urls.append(candidate)
                misses = 0
            else:
                misses += 1
                if misses >= args.stop_after_misses:
                    break

    # Download files
    for u in file_urls:
        status, text = fetch_url(u)
        if status == 200:
            data = safe_load_json(text)
            if data is None:
                # skip non-json
                continue
            docs.append({'url': u, 'doc': data})
            # write a local copy
            name = os.path.basename(u) or f"{len(docs)}.json"
            try:
                with open(os.path.join(args.outdir, name), 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
            except Exception:
                pass

    # Build discovery report
    report = {
        'generated_at': time.time(),
        'total_documents': len(docs),
        'sample_document_urls': [d['url'] for d in docs[:50]],
        'per_db_counts': {},
        'funcType_counts': {},
        'funcType_samples': {},
        'svals_keys': {},
        'buff_names': {},
    }

    for entry in docs:
        doc = entry['doc']
        # per-db heuristics
        dbname = doc.get('db') or doc.get('database') or doc.get('source_db') or 'unknown'
        report['per_db_counts'][dbname] = report['per_db_counts'].get(dbname, 0) + 1

        for func in find_functions(doc):
            ft = func.get('funcType')
            if not ft:
                continue
            report['funcType_counts'][ft] = report['funcType_counts'].get(ft, 0) + 1
            samples = report['funcType_samples'].setdefault(ft, [])
            if len(samples) < 5:
                samples.append(func)

            # svals keys
            svals = func.get('svals') or {}
            if isinstance(svals, dict):
                for k in svals.keys():
                    report['svals_keys'].setdefault(k, 0)
                    report['svals_keys'][k] += 1

            # buffs
            buffs = func.get('buffs') or []
            if isinstance(buffs, list):
                for b in buffs:
                    if isinstance(b, dict):
                        name = b.get('name') or b.get('buff') or 'unknown'
                        report['buff_names'][name] = report['buff_names'].get(name, 0) + 1

    # Convert defaultdict-like to normal
    # Keep samples limited and serializable
    for k, v in list(report['funcType_samples'].items()):
        report['funcType_samples'][k] = v[:5]

    # sort funcType_counts into list
    report['funcType_counts_sorted'] = sorted(report['funcType_counts'].items(), key=lambda x: -x[1])

    try:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(json.dumps({'error': 'write_failed', 'message': str(e)}))
        sys.exit(3)

    print(json.dumps({'status': 'ok', 'total_documents': report['total_documents']}))


if __name__ == '__main__':
    main()
