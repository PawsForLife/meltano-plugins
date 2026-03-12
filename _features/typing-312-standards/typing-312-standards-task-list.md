# Task List: typing-312-standards

Tasks are listed in execution order. Each task document lives in `_features/typing-312-standards/tasks/`.

| Order | Task file | Description |
|------|-----------|-------------|
| 1 | 01-configure-ruff-mypy.md | Configure Ruff (UP006, UP007, UP045) and mypy (python_version 3.12) for tap, target-gcs, and root/scripts if applicable. |
| 2 | 02-refactor-tap-streams.md | Refactor `restful_api_tap/streams.py` to 3.12 typing (dict/list, X \| Y, X \| None). |
| 3 | 03-refactor-tap-pagination.md | Refactor `restful_api_tap/pagination.py` to 3.12 typing. |
| 4 | 04-refactor-tap-client.md | Refactor `restful_api_tap/client.py` to 3.12 typing. |
| 5 | 05-refactor-tap-tap.md | Refactor `restful_api_tap/tap.py` to 3.12 typing. |
| 6 | 06-refactor-tap-utils.md | Refactor `restful_api_tap/utils.py` to 3.12 typing. |
| 7 | 07-refactor-tap-tests.md | Refactor tap tests (`taps/restful-api-tap/tests/*.py`) to 3.12 typing. |
| 8 | 08-refactor-target-gcs-tests.md | Refactor target-gcs tests to 3.12 typing (runtime code unchanged). |
| 9 | 09-refactor-scripts.md | Refactor `scripts/list_packages.py` and `scripts/tests/test_list_packages.py` to 3.12 typing. |
| 10 | 10-update-changelogs.md | Add changelog entries (root and optionally tap/target) for the refactor. |

**Execution order:** 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10. Task 01 is prerequisite for 02–09; 10 is last (after all code/config work). Tap tasks 02–07 can be reordered among themselves if desired; target (08) and scripts (09) are independent of tap.

**Verification:** After each task, run the relevant test suite and Ruff/mypy as specified in the task document. All existing tests must pass (no behaviour change).
