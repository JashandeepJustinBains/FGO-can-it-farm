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

Acceptance: POST endpoint accepts the example payload, validates and normalizes fields, and returns 200 with a run id or simulation result. The simulator receives structured input objects with `mode` passed through. Provide parsing unit tests.

Notes: validate types, accept empty placeholders for team slots (collectionNo empty string), and return helpful 4xx messages for invalid data.
Priority: 5

[not-started] (ID: 4) Add `mode` handling in `units/Servant.py`

Files: units/Servant.py, data loading helpers
Description: Support a `mode` attribute that selects servant data variant (skills/NP) based on ascension/variant. Backwards compatible when `mode` missing.

Acceptance: Creating a Servant with `mode` chooses the corresponding variant. Add unit tests using example servant JSON variants.

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
