# Task Plan: 06-refactor-tap-utils

## Overview

This task refactors `restful_api_tap/utils.py` to Python 3.12 typing conventions within the typing-312-standards feature. The module provides `flatten_json`, `unnest_dict`, and `get_start_date`. All `Optional[...]` annotations are replaced with `... | None`; `typing` imports are reduced to `Any` only. No behaviour or public API changes; Ruff (UP045) and mypy enforce style and type correctness after Task 01 configuration.

## Files to Create/Modify

| File | Action |
|------|--------|
| `taps/restful-api-tap/restful_api_tap/utils.py` | Modify |

**Changes in `utils.py`:**

- **Imports:** Replace `from typing import Any, Optional` with `from typing import Any`. Remove `Optional`.
- **`flatten_json`:** Change `except_keys: Optional[list] = None` to `except_keys: list | None = None`; change `store_raw_json_message: Optional[bool] = False` to `store_raw_json_message: bool | None = False`.
- **`get_start_date`:** Change parameter `context: Optional[dict]` to `context: dict | None`.
- **`unnest_dict`:** No type hints today; no change required (task converts existing hints only).
- No new files. No changes to other modules.

## Test Strategy

- **No new test files or test cases.** This is a refactor-only change; existing tests remain the behavioural specification.
- **TDD:** Not applicable for new behaviour; existing tests are run before and after edits to guard against regressions.
- **Order:** Run the tap test suite from `taps/restful-api-tap/` before making changes to establish a passing baseline; after edits, re-run pytest to confirm no regressions.
- **Static checks:** Ruff (with UP006, UP007, UP045 from Task 01) and mypy act as the typing-style and type-correctness gate. Fix any new violations introduced by the refactor (e.g. unused `Optional` import removed; annotations must remain valid).

## Implementation Order

1. From `taps/restful-api-tap/`, run `uv run pytest`, `uv run ruff check .`, and `uv run mypy restful_api_tap` to confirm a clean baseline (Task 01 must be complete so UP045 is enabled).
2. In `restful_api_tap/utils.py`:
   - Update the `typing` import: remove `Optional`; keep `Any`.
   - In `flatten_json`: replace `except_keys: Optional[list] = None` with `except_keys: list | None = None`; replace `store_raw_json_message: Optional[bool] = False` with `store_raw_json_message: bool | None = False`.
   - In `get_start_date`: replace `context: Optional[dict]` with `context: dict | None`.
3. Run `uv run ruff check .` and `uv run ruff format .` (if the project uses format); fix any issues.
4. Run `uv run mypy restful_api_tap`; fix any type errors.
5. Run `uv run pytest`; all tests must pass (no regressions).

## Validation Steps

1. **Ruff:** From `taps/restful-api-tap/`, `uv run ruff check .` exits 0 with no violations in `restful_api_tap/utils.py` (no `Optional`, no old-style generics).
2. **mypy:** From `taps/restful-api-tap/`, `uv run mypy restful_api_tap` exits 0 with no type errors.
3. **Tests:** From `taps/restful-api-tap/`, `uv run pytest` passes in full; no failing tests unless explicitly marked as expected failure.
4. **Inspection:** Open `utils.py` and confirm only `Any` is imported from `typing`, and all former `Optional[...]` usages are `... | None`.

## Documentation Updates

- **No doc or README changes** are required for this task. Type hints are internal to the module; public behaviour and config contracts are unchanged.
- If the project's AI context or conventions doc explicitly describe typing in `utils.py`, they can be updated in a later pass to state that the tap uses 3.12-style hints (`... | None`); this task does not mandate that change.
