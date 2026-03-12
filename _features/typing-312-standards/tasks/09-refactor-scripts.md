# Task: Refactor repo-root scripts to Python 3.12 typing

## Background

`scripts/list_packages.py` and `scripts/tests/test_list_packages.py` may use `typing.Dict`/`List`/`Optional`/`Union`. The script already uses `from __future__ import annotations`; this task converts any remaining old-style generics to built-ins and `|` for consistency with the rest of the feature.

**Dependencies:** Task 01. Independent of tap and target-gcs refactors.

## This Task

- **Files:** `scripts/list_packages.py`, `scripts/tests/test_list_packages.py`
- Replace `typing.Dict`/`List`/`Optional`/`Union`/`Set`/`Tuple` with built-in `dict`/`list`/`set`/`tuple` and `X | None`, `X | Y`.
- Keep `from __future__ import annotations` if already present; keep `Any`, `cast`, etc. as per feature rules.
- Run script tests as defined at repo root (e.g. `pytest scripts/tests -v` or per `.github/workflows/script-tests.yml`).

**Acceptance criteria:** Scripts and their tests use 3.12-style type hints; script test suite passes. If the repo adds ruff/mypy for scripts in a later change, this refactor leaves scripts ready.

## Testing Needed

- Run script tests from repo root: `pytest scripts/tests -v` (or equivalent per project docs/CI).
- No new tests required; refactor-only. If a ruff config is added for scripts in task 01, run `ruff check scripts/` and fix any violations.
