# Task Plan: 02-refactor-tap-streams

## Overview

This task refactors `restful_api_tap/streams.py` to Python 3.12 typing conventions only in that file. It replaces `typing.Dict`, `typing.List`, `typing.Optional`, and `typing.Union` with built-in generics (`dict`, `list`) and pipe-union syntax (`X | None`, `X | Y`), and trims the `typing` import to the symbols that have no built-in equivalent. Behaviour is unchanged; the change is type-hint and import hygiene. It depends on task 01 (Ruff/mypy configuration) so the linter enforces the new style.

**In scope:** `taps/restful-api-tap/restful_api_tap/streams.py` only.  
**Out of scope:** Other tap modules (pagination, client, tap, utils), tap tests, and `singer_sdk.typing` usage (e.g. schema definitions).

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `taps/restful-api-tap/restful_api_tap/streams.py` | Modify: update type hints and imports only |

### Specific changes in `streams.py`

1. **Import (line 11)**  
   - From: `from typing import Any, Dict, Generator, Iterable, Optional, Union, cast`  
   - To: `from typing import Any, Generator, Iterable, cast`  
   - Remove: `Dict`, `Optional`, `Union`.

2. **`DynamicStream.__init__` (lines 52–86)**  
   - Replace every `Optional[<type>]` parameter with `<type> | None` (e.g. `Optional[dict]` → `dict | None`, `Optional[list]` → `list | None`, `Optional[str]` → `str | None`, `Optional[int]` → `int | None`, `Optional[bool]` → `bool | None`, `Optional[object]` → `object | None`, `Optional[datetime]` → `datetime | None`).  
   - Leave parameter names and default values unchanged.

3. **Instance attribute (line 191)**  
   - `self.pagination_page_size: Optional[int]` → `self.pagination_page_size: int | None`.

4. **`backoff_wait_generator` (line 265)**  
   - Return type: `Generator[Union[int, float], None, None]` → `Generator[int | float, None, None]`.

5. **`_get_url_params_page_style` (lines 371–372)**  
   - Parameters: `context: Optional[dict]`, `next_page_token: Optional[Any]` → `context: dict | None`, `next_page_token: Any | None`.  
   - Return: `Dict[str, Any]` → `dict[str, Any]`.

6. **`_get_url_params_offset_style` (lines 314–315)**  
   - Parameters: `context: Optional[dict]`, `next_page_token: Optional[Any]` → `context: dict | None`, `next_page_token: Any | None`.  
   - Return: `Dict[str, Any]` → `dict[str, Any]`.

7. **`_get_url_params_header_link` (lines 361–363)**  
   - Parameters: `context: Optional[Dict]`, `next_page_token: Optional[Any]` → `context: dict | None`, `next_page_token: Any | None`.  
   - Return: `Dict[str, Any]` → `dict[str, Any]`.

8. **`_get_url_params_hateoas_body` (lines 418–419)**  
   - Parameters: `context: Optional[dict]`, `next_page_token: Optional[Any]` → `context: dict | None`, `next_page_token: Any | None`.  
   - Return: `Dict[str, Any]` → `dict[str, Any]`.

9. **`post_process` (lines 381–384)**  
   - Parameter: `context: Optional[types.Context] = None` → `context: types.Context | None = None`.  
   - Return: `Optional[dict]` → `dict | None`.  
   - Leave `cast(Optional[dict], row)` → `cast(dict | None, row)` (or equivalent) so the return type matches.

**Do not change:**  
- Any `singer_sdk` or `singer_sdk.helpers.types` usage (e.g. `types.Record`, `types.Context`).  
- Logic, defaults, or docstrings except where a type name appears in a docstring and should stay consistent (optional).

---

## Test Strategy

- **No new tests.** This is a refactor-only task; behaviour must remain identical.
- **Regression:** Run the existing tap test suite from `taps/restful-api-tap/`: `uv run pytest`. All tests must pass.
- **Style and types:** From `taps/restful-api-tap/` run `uv run ruff check .` and `uv run mypy restful_api_tap`. Both must pass (task 01 must be done so UP006/UP007/UP045 and mypy 3.12 are active).
- **Black-box:** Tests continue to assert observable behaviour only; no assertions on typing or imports.

---

## Implementation Order

1. **Prerequisite:** Confirm task 01 is complete (Ruff UP006, UP007, UP045 and mypy `python_version = "3.12"` for the tap).
2. Update the `typing` import in `streams.py`: keep only `Any`, `Generator`, `Iterable`, `cast`.
3. Replace all `Optional[...]` with `... | None` in parameters, return types, and the single attribute annotation.
4. Replace all `Union[X, Y]` with `X | Y` (e.g. `Generator[Union[int, float], ...]` → `Generator[int | float, ...]`).
5. Replace all `Dict[...]` and `List[...]` with `dict[...]` and `list[...]` in annotations (parameters and return types).
6. Run `uv run ruff check .` and fix any remaining style issues.
7. Run `uv run mypy restful_api_tap` and fix any type errors.
8. Run `uv run pytest` and fix any regressions.

---

## Validation Steps

1. From `taps/restful-api-tap/`: `uv run ruff check .` — exit code 0.
2. From `taps/restful-api-tap/`: `uv run mypy restful_api_tap` — exit code 0.
3. From `taps/restful-api-tap/`: `uv run pytest` — all tests pass (no new failures except explicitly marked xfail).
4. Grep (or visual check) `streams.py` for `Optional`, `Union`, `Dict`, `List` from `typing`: no matches in type positions.

---

## Documentation Updates

- **None required.** No public API, config, or behaviour change. Optional: if the repo has a contributing or style guide that references typing, ensure it allows or recommends 3.12-style hints; that is covered by the feature-level documentation plan, not this task.
