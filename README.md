NOTICE: I sincerely apologize for revealing this forbidden knowledge.

This project helps evaluate which servants can clear high-level farming nodes automatically. It fetches servant and quest data from Atlas Academy, stores them in MongoDB, and exposes a small API and simulation endpoints used by the frontend.

## High-level components
- `scripts/`: data collection and upsert utilities
  - `GetUpdatesAndUpsert.py` — download servant and quest JSON from Atlas Academy and upsert into MongoDB. Uses deterministic `sourceHash` + `replace_one(..., upsert=True)` so changed documents replace previous documents and identical documents are skipped.
  - `GetNiceFormatQuests.py` (legacy) — helper for quest scraping
- `api/`: FastAPI backend that serves servant, mysticcode, quest data and runs simulations.
- `units/`, `managers/`: core simulation logic and models used by both CLI and API.
- `outputs/`: generated search trees, logs, and other outputs.

## Backend evolution (recent updates)
- **Warmup support**: frontend now sends a fire-and-forget warmup request on app mount. To support that the backend provides:
  - `GET /api/servants?warm=true` — quick DB ping that returns immediately (no heavy work).
  - `GET /api/warmup` — dedicated warmup endpoint that pings MongoDB and returns `{"status":"ok"}` (best-effort).
  Purpose: warm DB connections / connection pools so the first real user request isn't slowed by cold DB startups.

- **Upsert semantics**: `GetUpdatesAndUpsert.py` now computes a canonical `sourceHash` (stable JSON dump -> SHA256) and uses `replace_one(query, new_data, upsert=True)` to truly replace documents when they change. If the hash matches, the script skips the write to avoid unnecessary I/O.

- **Servant auto-discovery**: The script can discover the latest servants by scanning ids up to a safety cap and skipping hardcoded non-playable ids. Heuristic checks for playable servants include the presence of `collectionNo` and at least one of `mstSkill`, `skills`, or `cards`.

- **Retry and politeness**: requests use a shared `requests.Session`, configurable `RATE_LIMIT_SECONDS`, and a jittered exponential backoff that honors HTTP 429 `Retry-After`.

## Data hygiene & deduplication guidance
If duplicate quests were accidentally inserted, options:
1. **Drop and rebuild (fast)**: back up the `quests` collection, drop it, and re-run `GetUpdatesAndUpsert.py -q` to repopulate.
2. **Selective dedupe**: archive duplicated documents into `quests_duplicates_archive` and remove extras while keeping the preferred document (e.g., highest recommend level or newest). The repo includes a dedupe script pattern in `scripts/` for this workflow.

## Deployment & packaging notes
- The FastAPI app imports `sim_entry_points.traverse_api_input`. That module currently lives at the top level — this works as long as your runtime includes the repository root in `PYTHONPATH`. Alternatives:
  - Keep `sim_entry_points` at repo root and run the API with the repo root on `PYTHONPATH` or install the package in editable mode (`pip install -e .`).
  - Move `sim_entry_points` under `api/` and update imports to use relative imports. This centralizes server code but requires updating any scripts that import it from the old location.

## Environment variables used by scripts & API
- `MONGO_URI` (required) — MongoDB connection string for reads/writes.
- `RATE_LIMIT_SECONDS` — seconds between Atlas Academy requests (default 1.0).
- `CONSECUTIVE_MISS_LIMIT` — how many consecutive non-playable/missing servant IDs to see before stopping discovery (default 5).
- `MAX_ID_LIMIT` — safety cap for auto-discovery scanning (default 500).
- `NON_PLAYABLE_IDS` — comma-separated ids to skip during servant discovery.
- `MAX_RETRIES`, `BACKOFF_BASE`, `MAX_BACKOFF` — controls for retry/backoff behavior.
- `LOG_LEVEL` — logging level for scripts (e.g., INFO, DEBUG).

## Quick operational commands
Activate venv and run quests-only updater:
```powershell
& .\env\Scripts\Activate.ps1
python .\scripts\GetUpdatesAndUpsert.py -q
```

Drop and rebuild quests (backup recommended):
```powershell
& .\env\Scripts\Activate.ps1
python - <<'PY'
from pymongo import MongoClient
import os
client = MongoClient(os.environ['MONGO_URI'])
db = client['FGOCanItFarmDatabase']
db['quests'].drop()
print('Dropped quests collection')
PY
python .\scripts\GetUpdatesAndUpsert.py -q
```

Create unique index on quests `id` after cleanup:
```powershell
& .\env\Scripts\Activate.ps1
python - <<'PY'
from pymongo import MongoClient
import os
client = MongoClient(os.environ['MONGO_URI'])
db = client['FGOCanItFarmDatabase']
db['quests'].create_index([('id', 1)], unique=True, name='unique_quest_id')
print('Created unique index on id')
PY
```

## If you'd like
- I can add a `--dry-run` option to `GetUpdatesAndUpsert.py` to simulate writes.
- I can add a dedicated `scripts/dedupe_quests.py` in the repo (dry-run first, `--commit` to apply) if you want a surgical dedupe path.
- I can move `sim_entry_points` into `api/` and update imports if you prefer that packaging.

Thank you — let me know which cleanup path you'd like (drop+rebuild vs. safe dedupe) and I will prepare the exact commands/scripts and run the dry-run locally for you.
        