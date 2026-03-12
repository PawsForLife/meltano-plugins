# Task: Refactor tap tests to Python 3.12 typing

## Background

Tap test files (`taps/restful-api-tap/tests/`) may use `Optional`, `Union`, `Dict`, `List` in type annotations. This task applies the same replacement rules so the tap test suite is fully 3.12-style and Ruff/mypy pass.

**Dependencies:** Tasks 01–06 (tap source and config updated).

## This Task

- **Files:** `taps/restful-api-tap/tests/*.py` (e.g. `test_streams.py`, `test_is_sorted.py`, and any others with old-style hints).
- In test modules, replace `Optional`/`Union`/`Dict`/`List`/`Set`/`Tuple` with `X | None`, `X | Y`, and built-in `dict`/`list`/`set`/`tuple`.
- Keep `Any`, `cast`, and other reserved typing symbols as per the feature; remove unused imports.
- Run from `taps/restful-api-tap/`: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check` (if used), `uv run mypy restful_api_tap` (note: tap mypy may exclude tests; if so, run ruff on tests).

**Acceptance criteria:** All tap tests use 3.12-style type hints; full test suite and lint/type checks pass.

## Testing Needed

- `uv run pytest` from `taps/restful-api-tap/` — all tests must pass (no behaviour change).
- `uv run ruff check .` (and format if applicable); mypy as configured for the tap.
