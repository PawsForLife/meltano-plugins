# Task Plan: 04-refactor-tap-client

## Overview

This task refactors `restful_api_tap/client.py` to Python 3.12 typing conventions within the typing-312-standards feature. The file defines `RestApiStream` (base for REST API streams), `_request`, and `request_records`. All `Optional[...]` annotations are replaced with `... | None`; `typing` imports are reduced to `Any` and `Iterator` only. No behaviour or public API changes; Ruff (UP045) and mypy enforce style and type correctness after Task 01 configuration.

## Files to Create/Modify

| File | Action |
|------|--------|
| `taps/restful-api-tap/restful_api_tap/client.py` | Modify |

**Changes in `client.py`:**

- **Imports:** Replace `from typing import Any, Iterator, Optional` with `from typing import Any, Iterator`. Remove `Optional`.
- **`_request`:** Change parameter `context: Optional[dict]` to `context: dict | None`.
- **`request_records`:** Change parameter `context: Optional[dict]` to `context: dict | None`.
- No new files. No changes to other modules.

## Test Strategy

- **No new test files or test cases.** This is a refactor-only change; existing tests remain the behavioural specification.
- **TDD:** Not applicable for new behaviour; existing tests are run before and after edits to guard against regressions.
- **Order:** Run the tap test suite from `taps/restful-api-tap/` before making changes to establish a passing baseline; after edits, re-run pytest to confirm no regressions.
- **Static checks:** Ruff (with UP006, UP007, UP045 from Task 01) and mypy act as the typing-style and type-correctness gate. Fix any new violations introduced by the refactor (e.g. unused `Optional` import removed; annotations must remain valid).

## Implementation Order

1. From `taps/restful-api-tap/`, run `uv run pytest`, `uv run ruff check .`, and `uv run mypy restful_api_tap` to confirm a clean baseline (Task 01 must be complete so UP045 is enabled).
2. In `restful_api_tap/client.py`:
   - Update the `typing` import: remove `Optional`; keep `Any`, `Iterator`.
   - Replace `context: Optional[dict]` with `context: dict | None` in `_request(self, prepared_request, context)`.
   - Replace `context: Optional[dict]` with `context: dict | None` in `request_records(self, context)`.
3. Run `uv run ruff check .` and `uv run ruff format .` (if the project uses format); fix any issues.
4. Run `uv run mypy restful_api_tap`; fix any type errors.
5. Run `uv run pytest`; all tests must pass (no regressions).

## Validation Steps

1. **Ruff:** From `taps/restful-api-tap/`, `uv run ruff check .` exits 0 with no violations in `restful_api_tap/client.py` (no `Optional`, no old-style generics).
2. **mypy:** From `taps/restful-api-tap/`, `uv run mypy restful_api_tap` exits 0 with no type errors.
3. **Tests:** From `taps/restful-api-tap/`, `uv run pytest` passes in full; no failing tests unless explicitly marked as expected failure.
4. **Inspection:** Open `client.py` and confirm only `Any` and `Iterator` are imported from `typing`, and all former `Optional[dict]` usages are `dict | None`.

## Documentation Updates

- **No doc or README changes** are required for this task. Type hints are internal to the module; public behaviour and config contracts are unchanged.
- If the project’s AI context or conventions doc explicitly describe typing in `client.py`, they can be updated in a later pass to state that the tap uses 3.12-style hints (`dict | None`); this task does not mandate that change.
