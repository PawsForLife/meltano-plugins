# Task: Refactor tap pagination.py to Python 3.12 typing

## Background

`restful_api_tap/pagination.py` uses `List[...]` and `Optional[...]`. This task converts those to `list[...]` and `... | None` and keeps only `Any` and `cast` from `typing`.

**Dependencies:** Task 01. Can be done after or in parallel with task 02 (no dependency on streams.py).

## This Task

- **File:** `taps/restful-api-tap/restful_api_tap/pagination.py`
- Replace `List[...]`, `Optional[...]` with `list[...]`, `... | None`.
- Keep `Any`, `cast` from `typing`; remove unused typing imports.
- Run from `taps/restful-api-tap/`: `uv run ruff check .`, `uv run mypy restful_api_tap`, `uv run pytest`.

**Acceptance criteria:** pagination.py uses only 3.12-style hints; Ruff and mypy pass; existing tests pass.

## Testing Needed

- `uv run pytest` from `taps/restful-api-tap/` (no behaviour change).
- `uv run ruff check .` and `uv run mypy restful_api_tap`.
