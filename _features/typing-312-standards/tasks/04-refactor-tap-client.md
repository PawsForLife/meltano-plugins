# Task: Refactor tap client.py to Python 3.12 typing

## Background

`restful_api_tap/client.py` uses `Optional[...]` and possibly other old-style hints. This task converts them to `... | None` and keeps `Any`, `Iterator` from `typing`.

**Dependencies:** Task 01.

## This Task

- **File:** `taps/restful-api-tap/restful_api_tap/client.py`
- Replace `Optional[...]` with `... | None`; replace any `Union`/`Dict`/`List` with `|` and built-in generics.
- Keep `Any`, `Iterator`; remove unused typing imports.
- Run from `taps/restful-api-tap/`: `uv run ruff check .`, `uv run mypy restful_api_tap`, `uv run pytest`.

**Acceptance criteria:** client.py uses 3.12-style hints only; Ruff, mypy, and tests pass.

## Testing Needed

- `uv run pytest` from `taps/restful-api-tap/`.
- `uv run ruff check .` and `uv run mypy restful_api_tap`.
