# Task: Refactor tap utils.py to Python 3.12 typing

## Background

`restful_api_tap/utils.py` uses `Optional[...]` and possibly other old-style hints. This task converts them to `... | None` and keeps `Any`.

**Dependencies:** Task 01.

## This Task

- **File:** `taps/restful-api-tap/restful_api_tap/utils.py`
- Replace `Optional[...]` with `... | None`; replace any `Union`/`Dict`/`List` with built-ins and `|`.
- Keep `Any`; remove unused typing imports.
- Run from `taps/restful-api-tap/`: `uv run ruff check .`, `uv run mypy restful_api_tap`, `uv run pytest`.

**Acceptance criteria:** utils.py uses 3.12-style hints only; Ruff, mypy, and tests pass.

## Testing Needed

- `uv run pytest` from `taps/restful-api-tap/`.
- `uv run ruff check .` and `uv run mypy restful_api_tap`.
