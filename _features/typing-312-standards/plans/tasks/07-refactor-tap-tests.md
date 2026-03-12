# Task Plan: 07-refactor-tap-tests

## Overview

This task refactors tap test modules under `taps/restful-api-tap/tests/` to Python 3.12 typing conventions as part of the typing-312-standards feature. Test code may use parameters defaulting to `None` with non-optional type hints (e.g. `extras: dict = None`) or any remaining `Optional`/`Union`/`Dict`/`List`/`Set`/`Tuple` from `typing`. The task applies the same replacement rules as the tap source: use `X | None` for optional types, built-in `dict`/`list`/`set`/`tuple` for generics, and retain only `Any`, `cast`, and other reserved typing symbols. No test behaviour or assertions change; the full tap test suite and Ruff/mypy must pass after the refactor.

**Dependencies:** Tasks 01–06 (Ruff/mypy config and tap source refactors) must be complete so that UP006, UP007, UP045 are enabled and tap code already uses 3.12-style hints.

## Files to Create/Modify

| File | Action |
|------|--------|
| `taps/restful-api-tap/tests/test_streams.py` | Modify |
| `taps/restful-api-tap/tests/test_is_sorted.py` | Modify only if old-style hints exist |
| `taps/restful-api-tap/tests/test_tap.py` | Modify only if old-style hints exist |
| `taps/restful-api-tap/tests/test_utils.py` | Modify only if old-style hints exist |
| `taps/restful-api-tap/tests/test_core.py` | Modify only if old-style hints exist |
| `taps/restful-api-tap/tests/test_404_end_of_stream.py` | Modify only if old-style hints exist |

**No new files.** Other test modules (`__init__.py`) are unchanged unless they contain type hints to convert.

### Changes in `test_streams.py`

- **`config(extras: dict = None)`** → `config(extras: dict | None = None) -> dict`
- **`json_resp(extras: dict = None)`** → `json_resp(extras: dict | None = None) -> dict`
- **`setup_api(..., json_extras: dict = None, headers_extras: dict = None, matcher: Any = None)`** → use `json_extras: dict | None = None`, `headers_extras: dict | None = None`, `matcher: Any | None = None`
- **Imports:** Keep `from typing import Any`; add no new typing symbols (no `Optional` used; use `| None` only).
- If any `Optional`/`Union`/`Dict`/`List`/`Set`/`Tuple` are present, replace with `X | None`, `X | Y`, and built-in generics; remove unused typing imports.

### Other test files

- **test_is_sorted.py:** Currently only `from typing import Any` and `requests_mock: Any`. No `Optional`/`Union`/generics found; no change required unless a later scan finds old-style hints.
- **test_tap.py, test_utils.py, test_core.py, test_404_end_of_stream.py:** No typing generics or Optional/Union in current code; only adjust if grep reveals any.

Implementer should run `ruff check .` from the tap directory after Tasks 01–06; any file under `tests/` reported by Ruff for UP006/UP007/UP045 (or equivalent) must be updated. The plan assumes primary edits in `test_streams.py`; other files are “modify only if needed.”

## Test Strategy

- **No new test cases.** This is a refactor-only task; existing tests remain the behavioural specification.
- **TDD:** Not applicable for new behaviour. Run the full tap test suite before and after edits to guard against regressions.
- **Order:**
  1. From `taps/restful-api-tap/`, run `uv run pytest` to establish a passing baseline.
  2. Run `uv run ruff check .` (and `uv run ruff format --check` if used). After Tasks 01–06, Ruff may already flag `tests/` for UP045 (e.g. `dict = None` → `dict | None = None`). Fix all reported files.
  3. Run `uv run mypy restful_api_tap` (and, if the tap’s config includes `tests/`, run mypy on tests). Resolve any new type errors from the refactor.
  4. Re-run `uv run pytest`; all tests must pass (no behaviour change).
- **Black-box:** Tests continue to assert observable behaviour only; no assertions on typing style or internal call counts.

## Implementation Order

1. **Baseline:** From `taps/restful-api-tap/`, run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check` (if applicable), and `uv run mypy restful_api_tap`. Confirm Tasks 01–06 are complete and tap source is clean. Note any Ruff violations in `tests/`.
2. **Scan:** Run `uv run ruff check .` and note every `tests/*.py` file with UP006, UP007, or UP045 violations. Optionally grep for `Optional`, `Union`, `Dict`, `List`, `Set`, `Tuple` in `taps/restful-api-tap/tests/` to catch unannotated optional params (e.g. `dict = None`).
3. **Refactor test_streams.py:**
   - In `config(extras: dict = None)`, change to `extras: dict | None = None`.
   - In `json_resp(extras: dict = None)`, change to `extras: dict | None = None`.
   - In `setup_api(..., json_extras: dict = None, headers_extras: dict = None, matcher: Any = None)`, change to `json_extras: dict | None = None`, `headers_extras: dict | None = None`, `matcher: Any | None = None`.
   - Replace any remaining `Optional`/`Union`/`Dict`/`List`/`Set`/`Tuple` with 3.12 style; keep `Any`; remove unused `typing` imports.
4. **Refactor other test files:** For each file under `tests/` that Ruff or mypy flags (or that contains old-style hints), apply the same rules: `Optional[X]` → `X | None`, `Union[X, Y]` → `X | Y`, `Dict`/`List`/`Set`/`Tuple` → `dict`/`list`/`set`/`tuple`, params defaulting to `None` with a non-optional type → `X | None = None`. Keep `Any`, `cast`; remove unused imports.
5. **Lint and format:** Run `uv run ruff check .` and `uv run ruff format .` (if used); fix any issues.
6. **Type check:** Run `uv run mypy restful_api_tap` (and tests if in scope); fix any type errors.
7. **Regression:** Run `uv run pytest`; all tests must pass. No test logic or assertions are changed.

## Validation Steps

1. **Ruff:** From `taps/restful-api-tap/`, `uv run ruff check .` exits 0 with no violations in `tests/` (no UP006/UP007/UP045 or other enabled rules).
2. **Format:** If the project uses Ruff format, `uv run ruff format --check` exits 0.
3. **mypy:** From `taps/restful-api-tap/`, `uv run mypy restful_api_tap` (and tests if configured) exits 0.
4. **Tests:** From `taps/restful-api-tap/`, `uv run pytest` passes in full; no failing tests unless explicitly marked as expected failure.
5. **Inspection:** In `test_streams.py`, confirm optional parameters use `dict | None = None` or `Any | None = None`; no `Optional`/`Union`/typing generics remain in any tap test file.

## Documentation Updates

- No doc or README changes are required for this task. Type hints in tests are internal to the test suite; public behaviour and tap contracts are unchanged.
- If the project’s AI context or conventions explicitly describe typing in tap tests, they may be updated in a later pass to state that tests use 3.12-style hints; this task does not mandate that change.
