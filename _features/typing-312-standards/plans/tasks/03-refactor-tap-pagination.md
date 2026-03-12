# Task Plan: 03-refactor-tap-pagination

## Overview

This task refactors `restful_api_tap/pagination.py` to Python 3.12 typing conventions within the typing-312-standards feature. It replaces `List[...]` and `Optional[...]` with built-in `list[...]` and pipe-union `... | None`, retains only `Any` and `cast` from `typing`, and removes unused imports. No behaviour or API changes; existing tests remain the regression gate.

**Scope:** Single file under `taps/restful-api-tap/restful_api_tap/pagination.py`.  
**Dependencies:** Task 01 (configure Ruff/mypy) must be done first. No dependency on task 02 (streams.py); may run in parallel with it.

---

## Files to Create/Modify

| Action | Path | Changes |
|--------|------|---------|
| **Modify** | `taps/restful-api-tap/restful_api_tap/pagination.py` | (1) Change import: `from typing import Any, List, Optional, cast` → `from typing import Any, cast`. (2) In `SimpleOffsetPaginator.has_more`: replace `extracted: List[Any] = cast(List[Any], ...)` with `extracted: list[Any] = cast(list[Any], ...)`. (3) In `RestAPIHeaderLinkPaginator.__init__`: replace `Optional[int]`, `Optional[bool]`, `Optional[str]` with `int | None`, `bool | None`, `str | None`. (4) In `RestAPIHeaderLinkPaginator.get_next_url`: replace return type `-> Optional[Any]` with `-> Any | None`. |

No new files. No other files in the tap are modified by this task.

---

## Test Strategy

- **No new test cases.** This is a refactor-only change; behaviour is unchanged.
- **TDD:** Not applicable (no new behaviour). Use existing tests as the specification: run the tap test suite before and after edits to confirm no regressions.
- **Static checks as gate:** After edits, run `uv run ruff check .` and `uv run mypy restful_api_tap` from `taps/restful-api-tap/`; any new violation must be fixed.
- **Black-box:** Existing tests continue to assert observable behaviour (returned values, pagination behaviour); no assertions on typing or internal call counts.

---

## Implementation Order

1. **Update imports**  
   In `pagination.py`, change `from typing import Any, List, Optional, cast` to `from typing import Any, cast`.

2. **Refactor `SimpleOffsetPaginator.has_more`**  
   Replace the annotated variable and `cast` usage:  
   `extracted: List[Any] = cast(List[Any], next(...))` →  
   `extracted: list[Any] = cast(list[Any], next(...))`.

3. **Refactor `RestAPIHeaderLinkPaginator.__init__`**  
   Replace parameter type hints:  
   `pagination_results_limit: Optional[int] = None` → `pagination_results_limit: int | None = None`,  
   `use_fake_since_parameter: Optional[bool] = False` → `use_fake_since_parameter: bool | None = False`,  
   `replication_key: Optional[str] = None` → `replication_key: str | None = None`.

4. **Refactor `RestAPIHeaderLinkPaginator.get_next_url`**  
   Replace return type: `-> Optional[Any]` → `-> Any | None`.

5. **Run quality checks**  
   From `taps/restful-api-tap/`: `uv run ruff check .`, `uv run mypy restful_api_tap`, `uv run pytest`. Resolve any failures before considering the task complete.

---

## Validation Steps

1. **Lint:** From `taps/restful-api-tap/`, run `uv run ruff check .` — no violations.
2. **Type check:** From `taps/restful-api-tap/`, run `uv run mypy restful_api_tap` — no errors.
3. **Tests:** From `taps/restful-api-tap/`, run `uv run pytest` — all tests pass (no regressions; no tests may be skipped or fail except those explicitly marked as expected failure).
4. **Regression gate:** Any failing test not marked with `@pytest.mark.xfail` or `@unittest.expectedFailure` must be fixed before task sign-off.

---

## Documentation Updates

- **No documentation updates required.** Module and docstrings in `pagination.py` describe behaviour only; no references to `List`/`Optional` in user-facing docs. If the project’s AI context or patterns doc references this file, no change is needed for this task (typing style is an implementation detail).
