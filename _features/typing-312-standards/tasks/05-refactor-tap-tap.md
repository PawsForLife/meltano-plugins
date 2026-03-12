# Task: Refactor tap tap.py to Python 3.12 typing

## Background

`restful_api_tap/tap.py` uses `List[...]` and `Optional[...]`. This task converts them to `list[...]` and `... | None` and keeps `Any`; leave `singer_sdk.typing as th` unchanged.

**Dependencies:** Task 01.

## This Task

- **File:** `taps/restful-api-tap/restful_api_tap/tap.py`
- Replace `List[...]`, `Optional[...]` with `list[...]`, `... | None`.
- Keep `Any`; do not change `th` (schema/config) usage.
- Remove unused typing imports.
- Run from `taps/restful-api-tap/`: `uv run ruff check .`, `uv run mypy restful_api_tap`, `uv run pytest`.

**Acceptance criteria:** tap.py uses 3.12-style hints; Ruff, mypy, and tests pass.

## Testing Needed

- `uv run pytest` from `taps/restful-api-tap/`.
- `uv run ruff check .` and `uv run mypy restful_api_tap`.
