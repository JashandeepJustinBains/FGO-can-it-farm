"""discovery_catalog.py
Read-only discovery tool for FGOCombatSim servants collection.

This script streams every document from any database in the cluster
that contains a `servants` collection and produces a JSON catalog
report summarizing funcType usage, svals shapes, buff names, and
sample documents.

USAGE (recommended via GitHub Actions):
  - Put the read-only URI into the environment variable SERVANTS_READONLY_URI
  - Run: python discovery_catalog.py

Security: the script only reads; it does not write to the repo or DB.
Do NOT commit credentials. Provide them through GitHub Secrets.
"""

import os
import json
import sys
from collections import defaultdict, Counter
from pymongo import MongoClient
from bson import json_util


def find_servants_collections(client):
    dbs = []
    try:
        for dbname in client.list_database_names():
            try:
                cols = client[dbname].list_collection_names()
            except Exception:
                continue
            if "servants" in cols:
                dbs.append(dbname)
    except Exception as e:
        raise
    return dbs


def analyze_doc(doc, stats, sample_by_key, sample_limit=3):
    # Track top-level shapes
    for key in ("skills", "noblePhantasms", "passives", "transforms", "ascensions", "forms"):
        if key in doc:
            stats["top_level_keys"].add(key)

    # Walk skills/nps/passives if present
    for arr_key in ("skills", "noblePhantasms", "passives", "transforms"):
        arr = doc.get(arr_key)
        if not arr:
            continue
        # support nested list-of-lists and ascension objects
        items = []
        if isinstance(arr, list) and len(arr) > 0 and isinstance(arr[0], list):
            for sub in arr:
                items.extend(sub if isinstance(sub, list) else [sub])
        elif isinstance(arr, list):
            items = arr
        else:
            continue

        for item in items:
            for func in item.get("functions", []):
                ftype = func.get("funcType", "UNKNOWN")
                stats["funcType_counts"][ftype] += 1
                # sample documents
                if len(sample_by_key[("funcType", ftype)]) < sample_limit:
                    sample_by_key[("funcType", ftype)].append(func)
                # svals keys
                for k in func.keys():
                    if k.startswith('svals'):
                        stats["svals_keys"].add(k)
                # svals content shapes
                svals = func.get("svals")
                if isinstance(svals, list):
                    stats["svals_list_lengths"].add(len(svals))
                    if len(svals) > 0 and isinstance(svals[0], dict):
                        stats["svals_fieldnames"].update(svals[0].keys())
                elif isinstance(svals, dict):
                    stats["svals_fieldnames"].update(svals.keys())
                # buffs under function
                for buff in func.get("buffs", []):
                    bname = buff.get("name", "UNKNOWN_BUFF")
                    stats["buff_names"].add(bname)
                    if len(sample_by_key[("buff", bname)]) < sample_limit:
                        sample_by_key[("buff", bname)].append(buff)
                    bs = buff.get("svals")
                    if isinstance(bs, list):
                        stats["buff_svals_lengths"].add(len(bs))
                        if len(bs) > 0 and isinstance(bs[0], dict):
                            stats["buff_svals_fieldnames"].update(bs[0].keys())
                # functvals and tvals
                if func.get("functvals"):
                    stats["functvals_examples"].append(func.get("functvals"))
                if func.get("tvals"):
                    stats["tvals_examples"].append(func.get("tvals"))


def run_discovery(uri):
    client = MongoClient(uri, serverSelectionTimeoutMS=15000)
    dbs_with_servants = find_servants_collections(client)
    report = {
        "dbs_with_servants": dbs_with_servants,
        "per_db": {},
        "total_docs_processed": 0,
    }

    overall_stats = {
        "top_level_keys": set(),
        "funcType_counts": Counter(),
        "svals_keys": set(),
        "svals_list_lengths": set(),
        "svals_fieldnames": set(),
        "buff_names": set(),
        "buff_svals_lengths": set(),
        "buff_svals_fieldnames": set(),
        "functvals_examples": [],
        "tvals_examples": []
    }
    sample_by_key = defaultdict(list)

    if not dbs_with_servants:
        print(json.dumps({"error": "no db with 'servants' collection found"}, indent=2))
        return

    for dbname in dbs_with_servants:
        coll = client[dbname]["servants"]
        cursor = coll.find({}, no_cursor_timeout=True).batch_size(200)
        count = 0
        try:
            for doc in cursor:
                count += 1
                analyze_doc(doc, overall_stats, sample_by_key)
                if count % 1000 == 0:
                    print(json.dumps({"progress": f"processed {count} docs in {dbname}"}))
            report["per_db"][dbname] = {"docs_processed": count}
            report["total_docs_processed"] += count
        finally:
            cursor.close()

    # finalize sets -> lists for JSON
    finalized = {
        "top_level_keys": sorted(list(overall_stats["top_level_keys"])),
        "funcType_counts": dict(overall_stats["funcType_counts"]),
        "svals_keys": sorted(list(overall_stats["svals_keys"])),
        "svals_list_lengths": sorted(list(overall_stats["svals_list_lengths"])),
        "svals_fieldnames": sorted(list(overall_stats["svals_fieldnames"])),
        "buff_names": sorted(list(overall_stats["buff_names"])),
        "buff_svals_lengths": sorted(list(overall_stats["buff_svals_lengths"])),
        "buff_svals_fieldnames": sorted(list(overall_stats["buff_svals_fieldnames"])),
        "sample_by_key": { str(k): v for k, v in sample_by_key.items() },
        "functvals_examples_count": len(overall_stats["functvals_examples"]),
        "tvals_examples_count": len(overall_stats["tvals_examples"])
    }

    report["catalog"] = finalized
    print(json.dumps(report, default=json_util.default, indent=2))


if __name__ == "__main__":
    uri = os.environ.get('SERVANTS_READONLY_URI')
    if not uri:
        print("ERROR: please set SERVANTS_READONLY_URI env var and re-run.", file=sys.stderr)
        sys.exit(2)
    try:
        run_discovery(uri)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        raise
