Quick review help (copy into the Copilot conversation)

Short: I want a code review focusing on runtime skill selection parity with NP selection. Use only example_servant_data/*.json; do NOT attempt DB access.

Commands to run locally (PowerShell):
```powershell
# checkout branch (already committed locally)
git checkout feature/skills-runtime-selection

# run dynamic NP/skill tests
env\Scripts\pytest -q tests/test_np_dynamic_selection.py

# run a few related tests
env\Scripts\pytest -q tests/test_TraverseApiInput_1.py tests/test_variant_api_input.py
```

Files to inspect:
- `units/skills.py`
- `units/np.py`
- `units/Servant.py`

Key question to answer:
- Do skills follow the same releaseCondition filtering and variant preference rules as NPs? If not, propose a small patch.

If suggesting tests: include the test name, a one-line description and a small fixture (e.g., create a synthetic `skillSvts` candidate list with two groups of releaseConditions).