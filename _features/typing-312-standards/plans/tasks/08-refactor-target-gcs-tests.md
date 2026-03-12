# Task Plan: 08-refactor-target-gcs-tests

## Overview

This task refactors the target-gcs test suite (`loaders/target-gcs/tests/`) to Python 3.12 typing conventions within the typing-312-standards feature. Runtime code (`target.py`, `sinks.py`) requires no changes per the master plan (target.py uses only `singer_sdk.typing`; sinks.py already uses `Callable[...] | None` and `Any`). Only test modules may still use old-style hints. The task audits all test files, replaces any `Optional`/`Union`/`Dict`/`List`/`Tuple`/`Set` with `X | None`, `X | Y`, and built-in `dict`/`list`/`set`/`tuple`, keeps `Any` and `cast` (and `Callable` from `collections.abc` where already used), and removes unused `typing` imports. No behaviour or test assertions change; Ruff (UP006, UP007, UP045 from Task 01) and mypy enforce style and type correctness.

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/tests/test_core.py` | Modify (audit; already uses `Any`, `cast`, `dict[str, Any]` — confirm no old-style hints; remove any unused typing imports) |
| `loaders/target-gcs/tests/test_sinks.py` | Modify (audit; already uses `Callable[[], datetime] \| None` — confirm no Optional/Union/Dict/List; ensure only `collections.abc.Callable` or typing as needed) |
| `loaders/target-gcs/tests/test_partition_key_generation.py` | Modify (audit; same as test_sinks — confirm 3.12 style throughout) |
| `loaders/target-gcs/tests/__init__.py` | No change (docstring only; no type hints) |

**Change rules (apply only where present):**

- Replace `Optional[X]` with `X | None`.
- Replace `Union[X, Y]` with `X | Y`.
- Replace `Dict[K, V]`, `List[T]`, `Tuple[...]`, `Set[T]` with `dict[K, V]`, `list[T]`, `tuple[...]`, `set[T]`.
- Keep `Any`, `cast` from `typing`; keep `Callable` from `collections.abc` (preferred) or `typing` as in existing code.
- Remove unused imports from `typing` (e.g. `Optional`, `Union`, `Dict`, `List`).
- Do not add `from __future__ import annotations` unless already present.

**Current state (for implementer):**

- `test_core.py`: Uses `from typing import Any, cast` and `SAMPLE_CONFIG: dict[str, Any]`; no Optional/Union/Dict/List found — verify and leave as-is or tidy imports only.
- `test_sinks.py`: Uses `Callable[[], datetime] | None` from `collections.abc`; no `typing` generics in annotations — verify and fix any remaining old-style hints if introduced later.
- `test_partition_key_generation.py`: Same pattern as test_sinks — verify and fix any old-style hints.

No new files. No changes to `target_gcs/` source (target.py, sinks.py).

## Test Strategy

- **No new test files or test cases.** This is a refactor of type hints only; existing tests remain the behavioural specification.
- **TDD:** Not applicable for new behaviour; existing tests are run before and after edits to guard against regressions.
- **Order:** Run the target-gcs test suite from `loaders/target-gcs/` before making changes to establish a passing baseline; after edits, re-run pytest to confirm no regressions.
- **Static checks:** Ruff (with UP006, UP007, UP045 from Task 01) and mypy act as the typing-style and type-correctness gate. Fix any violations (e.g. remaining old-style hints or unused imports).
- **Black-box:** Tests continue to assert observable behaviour (returned values, key names, client args, raised exceptions); no assertions on internal call counts or log output.

## Implementation Order

1. From `loaders/target-gcs/`, run `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check` (if used), and `uv run mypy target_gcs` to confirm a clean baseline (Task 01 must be complete so UP rules and mypy 3.12 are in effect).
2. Audit `tests/test_core.py`: ensure no `Optional`/`Union`/`Dict`/`List`/`Tuple`/`Set`; keep `Any`, `cast`; remove any unused typing imports.
3. Audit `tests/test_sinks.py`: ensure all annotations use 3.12 style (`Callable | None`, built-in generics); remove any unused typing imports.
4. Audit `tests/test_partition_key_generation.py`: same as step 3.
5. Apply replacements only where old-style hints exist; if none are found, confirm with ruff/mypy that the tests directory is compliant (e.g. mypy may need to see tests — confirm project’s mypy config for `target_gcs` and tests).
6. Run `uv run ruff check .` and `uv run ruff format .` (if the project uses format); fix any issues.
7. Run `uv run mypy target_gcs` (and tests if in scope per pyproject/mypy config); fix any type errors.
8. Run `uv run pytest`; all tests must pass (no regressions).

## Validation Steps

1. **Ruff:** From `loaders/target-gcs/`, `uv run ruff check .` exits 0 with no violations in `tests/` (no Optional, Union, or old-style generics).
2. **mypy:** From `loaders/target-gcs/`, `uv run mypy target_gcs` exits 0 with no type errors (include tests in check if configured).
3. **Tests:** From `loaders/target-gcs/`, `uv run pytest` passes in full; no failing tests unless explicitly marked as expected failure.
4. **Inspection:** Confirm each test file uses only 3.12-style hints (pipe unions, built-in generics) and only necessary imports from `typing` (e.g. `Any`, `cast`) or `collections.abc` (e.g. `Callable`).

## Documentation Updates

- **No doc or README changes** are required for this task. Changelog entries for the typing-312-standards feature are handled in Task 10 (update-changelogs).
- If `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` or patterns doc explicitly describe typing in target-gcs tests, they can be updated in a later pass to state that tests use 3.12-style hints; this task does not mandate that change.
