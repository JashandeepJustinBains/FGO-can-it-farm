Title: Make skill selection runtime-aware; honor variant overrides; add file fallback

Summary:
Make skill selection runtime-aware so the simulator selects the correct skill at time-of-use according to the servant's current variant/ascension (mirrors existing NP selection behavior). Also honor explicit costume/variant overrides and add a file fallback for environments without DB.

Files changed (high level):
- units/skills.py — store deferred `raw_candidates` for `skillSvts`, dynamic selection via `_select_skill_from_candidates`, `get_skill_by_num`, safe `initialize_max_cooldowns`.
- units/Servant.py — `compute_variant_svt_id` honors explicit `costume_svt_id`; `select_character` now attempts DB lookup if available, then falls back to reading `example_servant_data/<id>.json` with UTF-8.

Why this change:
- Some servants switch NPs/skills depending on ascension/costume or via skill effects mid-combat. NP selection was already fixed to be runtime-aware; skills needed the same behavior to avoid incorrect ability usage when ascension changes during a run.

How I validated locally:
- Ran `env\Scripts\pytest -q tests/test_np_dynamic_selection.py` — all tests passed locally.
- Ran broader subsets; some external tests fail because the test suite expects DB-backed example data for other collection numbers not included in `example_servant_data/`. The review should NOT attempt to connect to any DB; use only `example_servant_data/` files.

What I want feedback on:
- Correctness of releaseCondition grouping logic for skills (OR groups / AND within group parity with NP selection).
- Any missing edge-cases where deferred selection may behave incorrectly or produce side effects.
- Additional targeted tests to cover releaseCondition grouping and costume override behavior.

How to reproduce (local):
1. Checkout branch: `feature/skills-runtime-selection`
2. Run dynamic tests: `env\Scripts\pytest -q tests/test_np_dynamic_selection.py`
3. Optional broader test: `env\Scripts\pytest -q tests/test_TraverseApiInput_1.py tests/test_variant_api_input.py`

Notes for reviewer:
- DO NOT connect to the project DB or request DB credentials. Use only the sample JSON files in `example_servant_data/` (I intentionally cherry-picked servants that exercise variant/NP swap behavior: 1.json, 312.json, 444.json).
- If you suggest code changes, please provide a minimal patch for me to apply.