# Task: Refactor target-gcs tests to Python 3.12 typing

## Background

target-gcs runtime code (`target.py`, `sinks.py`) requires no changes (plan: target.py uses only `singer_sdk.typing`; sinks.py uses `Any` and already uses `Callable[...] | None`). Only tests may still use old-style hints. This task updates `loaders/target-gcs/tests/` (e.g. `test_core.py` and any other files with `Optional`/`Union`/generics) to 3.12 style.

**Dependencies:** Task 01. Independent of tap tasks (02–07).

## This Task

- **Files:** `loaders/target-gcs/tests/*.py` (notably `test_core.py` and any others with old-style type hints).
- Replace `Optional`/`Union`/`Dict`/`List`/etc. with `X | None`, `X | Y`, and built-in `dict`/`list`/`set`/`tuple`.
- Keep `Any`, `cast` and other reserved typing symbols; remove unused typing imports.
- Run from `loaders/target-gcs/`: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check` (if used), `uv run mypy target_gcs`.

**Acceptance criteria:** All target-gcs tests use 3.12-style type hints; pytest, Ruff, and mypy pass.

## Testing Needed

- `uv run pytest` from `loaders/target-gcs/` — all tests must pass.
- `uv run ruff check .` and `uv run mypy target_gcs`.
