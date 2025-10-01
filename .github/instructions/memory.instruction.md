---
applyTo: '**'
---

# User Memory

## User Preferences
- Programming languages: Python
- Code style preferences: follow existing project style
- Development environment: VS Code on Windows, PowerShell
- Communication style: concise, technical

## Project Context
- Current project type: simulation for FGO mechanics
- Tech stack: Python 3, modular managers (np_manager, skill_manager, turn_manager, game_manager), unit classes
- Key requirements: separate compact (INFO) and verbose (DEBUG) logs; preserve existing behavior; write JSONL step traces

## Coding Patterns
- Use module-level logger = logging.getLogger(__name__)
- Central logging configured in `Driver.py` to write outputs/output.log (INFO), outputs/verbose.log (DEBUG), outputs/compact.log (human-friendly)

## Context7 Research History
- None yet

## Conversation History
- Task: make logging less noisy; compact logs should include tokens, skill/NP usage, total damage, NP usage; verbose logs should include per-hit damage, buff/effect lists, NP gain per hit, etc.
- Central `Driver.py` already configures logging and writes JSONL step traces.
- Search found ~150 `logging.info` occurrences across managers and units; need to demote noisy INFO to DEBUG and remove module-level basicConfig calls.

## Notes
- Edits must be incremental and compile-checked to avoid indentation/syntax errors.
- Memory updated after each major change.
