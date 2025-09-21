TODOs
[not-started] (ID: 1) Fix duplicate quests

Files: GetUpdatesAndUpsert.py, scripts/dedupe_quests.py
Description: remove duplicates created for same quest id; keep highest recommendLv then newest.
Acceptance: run dedupe dry-run; run --commit to apply; verify count decreased and id unique.
Created: 2025-09-20
Priority: 7
[not-started] (ID: 2) Add /api/warmup endpoint

Files: main.py, db.py
Description: lightweight DB ping used by front-end warm request.
Acceptance: GET /api/warmup returns 200 quickly and db.client.admin.command('ping') executes.
Owner: you@example.com
Created: 2025-09-20
Priority: 6

Practical conventions for this repo

ID: use sequential integers so references are easy (1, 2, 3).
Status transitions: mark exactly one item in-progress when you start work; mark it completed immediately when finished (this matches our earlier process).
Link to artifacts: include commit SHA or PR link after you finish to make the history searchable.
Short-term vs long-term: prefix long-term/backlog items with [backlog] so they’re visually separate.

Example short checklist you can adopt now

[in-progress] (1) Fix DB-init syntax bug in GetUpdatesAndUpsert.py — Done (commit abc123)
[not-started] (2) Add --dry-run to updater scripts
[not-started] (3) Create scripts/dedupe_quests.py with dry-run + --commit
[not-started] (4) Add README section describing warmup endpoints — Done (commit def456)
[not-started] (5) Add unique index on quests.id after dedupe

---

High-priority additions (added 2025-09-21)

[in-progress] (ID: 3) Add JSON input endpoint

Files: api/main.py, api/read_helpers.py, sim_entry_points/traverse_api_input.py, Driver.py
Description: Accept and validate webapp JSON payload and wire it to the simulator. Payload contract:
- Team: array (up to 6) of unit objects. Each unit may have: collectionNo (string or int), np, initialCharge, attack, atkUp, artsUp, quickUp, busterUp, npUp, busterDamageUp, quickDamageUp, artsDamageUp, append_5 / append5 flags, mode (int).
- Mystic Code ID: integer
- Quest ID: integer
- Commands: string (sequence of commands and separators as used by the simulator)

Acceptance: POST endpoint accepts the example payload, validates and normalizes fields, and returns 200 with a run id or simulation result. The simulator receives structured input objects with `ascension` passed through. Provide parsing unit tests.

Notes: validate types, accept empty placeholders for team slots (collectionNo empty string), and return helpful 4xx messages for invalid data.
Priority: 5

[not-started] (ID: 4) Add `ascension` handling in `units/Servant.py`

Files: units/Servant.py, data loading helpers
Description: Support a `ascension` attribute that selects servant data variant (skills/NP) based on ascension/variant. Backwards compatible when `ascension` missing.

Acceptance: Creating a Servant with `ascension` chooses the corresponding variant. Add unit tests using example servant JSON variants.

Blocker: need sample servant JSON snippets showing multiple variants per servant.
Priority: 2

[not-started] (ID: 5) Fix NP-level vs OC-level calculation order

Files: units/np.py, units/Servant.py, damage calculation modules
Description: Investigate and correct reversed application of NP level and Overcharge (OC) modifications so NP-level sets base power then OC modifies damage/effect.

Acceptance: Unit tests demonstrate correct NP damage/OC numbers for sample cases. Add regression notes for affected sims.
Priority: 4

[not-started] (ID: 6) Generalize and fix transformation mechanics

Files: units/Servant.py, data model/schema, DB/JSON samples
Description: Replace hard-coded transformation logic with data-driven descriptors in servant JSON (e.g., `transforms` with rules). Support partial transforms (only NP or skills) and full replacements.

Acceptance: Transform behavior is driven by JSON fields; tests cover at least two transform patterns. Add sample servant JSONs demonstrating both styles.

Blocker: need example servant data showing differing transform behaviors.
Priority: 3

[not-started] (ID: 7) Remove FSM traces from `minimal` branch

Files: Driver.py, any modules referencing "Finite state machine" or "FSM"
Description: Remove or disable FSM code paths so the minimal runner executes user commands directly and deterministically.

Acceptance: Running the minimal runner with the example `Commands` string executes the commands directly; no FSM code remains in runtime path.
Priority: 9

[not-started] (ID: 8) Create Copilot-friendly TODO hints & sample data

Files to add: TODO-hints/TODO-3-hint.md .. TODO-9-hint.md, samples/servants/*.json, CONTRIBUTING-TODOS.md
Description: Create surgical prompt hint files for each high-priority task with goal, input/output contract, example JSONs, and required acceptance tests so a secondary agent can continue implementation.

Acceptance: Repo contains TODO-hint files and sample JSONs sufficient for an external agent to continue work with minimal context switching.
Priority: 1

[not-started] (ID: 9) Repo hygiene & low-risk improvements

Files: api/README.md, tests/, linting config (optional)
Description: Add small improvements: API payload README, parsing tests, and quick search for TODO/FIXME to create follow-up issues.

Acceptance: `api/README.md` added and a basic test skeleton for API parsing present.
Priority: 8

[not-started] (ID: 10) Finish `db.py` (work-in-progress)

Files: db.py
Description: `db.py` is currently a work-in-progress file used for database connection bootstrapping. Finish implementing environment-based configuration, connection pooling, and secure read-only clients for simulation consumers. Ensure it supports local dev (env var), Atlas (MONGO_URI), and a mocked in-memory store for tests.
Acceptance: `db.py` exposes `get_db()` and `get_client()` helpers and is covered by a basic unit test that can swap in a fake client. Add clear docs in `api/README.md`.
Priority: 5

[not-started] (ID: 11) Minimal successful-run logging (Cloudflare D1)

Files: utils/results_store.py, api/main.py, sim_entry_points/traverse_api_input.py
Description: When a simulation run clears all waves (successful run), write a compact summary record suitable for limited storage (Cloudflare D1). The minimal record should include: a compact team descriptor (collectionNos + ascensions), mystic code id, quest id, short command string, result hash, timestamp, and short per-wave summary (damage dealt / remaining HP as % or flags). Use a configurable backend (D1 via HTTP endpoint or SQLite fallback) to write records.
Acceptance: Implement `utils/results_store.py` with a simple interface `save_minimal_run(summary: dict) -> id`. Wire the FastAPI endpoint to call this after detect-success. Provide a script to export local SQLite to a small JSON file to seed D1 during migrations.
Priority: 3
