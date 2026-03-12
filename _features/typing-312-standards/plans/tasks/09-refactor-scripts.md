# Task Plan: 09-refactor-scripts

## Overview

This task refactors repo-root scripts and their tests to Python 3.12 typing conventions as part of the typing-312-standards feature. The scope is `scripts/list_packages.py` and `scripts/tests/test_list_packages.py`. Both files already use `from __future__ import annotations` and may already use built-in generics and pipe unions; the task is to audit for any remaining `typing.Dict`/`List`/`Optional`/`Union`/`Set`/`Tuple`, replace them with built-ins and `X | None` / `X | Y`, and retain only `Any`, `cast`, and other reserved typing symbols per the feature rules. No behaviour or test assertions change. Script tests are run from repo root to confirm no regressions. Task 01 does not add Ruff/mypy for scripts at repo root; this refactor leaves scripts ready if the repo adds script linting later.

**Dependencies:** Task 01 (Ruff/mypy config). Scripts are independent of tap and target-gcs refactors (tasks 02–08).

## Files to Create/Modify

| File | Action |
|------|--------|
| `scripts/list_packages.py` | Audit; replace any `Optional`/`Union`/`Dict`/`List`/`Set`/`Tuple` with `X \| None`, `X \| Y`, and built-in `dict`/`list`/`set`/`tuple`. Keep `from __future__ import annotations`. Keep only `Any`, `cast`, etc. from `typing` if used. |
| `scripts/tests/test_list_packages.py` | Same replacement rules for type hints. Keep `from __future__ import annotations`. No new tests. |

**No new files.** No other script files are in scope unless the repo adds scripts under `scripts/` that contain type hints; then apply the same rules.

### Change rules (apply only where present)

- Replace `Optional[X]` with `X | None`.
- Replace `Union[X, Y]` with `X | Y`.
- Replace `Dict[K, V]`, `List[T]`, `Tuple[...]`, `Set[T]` with `dict[K, V]`, `list[T]`, `tuple[...]`, `set[T]`.
- Keep `Any`, `cast` from `typing` if already used; do not introduce them unless needed.
- Remove unused imports from `typing` (e.g. `Optional`, `Union`, `Dict`, `List`).
- Keep `from __future__ import annotations` in both files (already present).

**Current state (for implementer):** As of the plan, `list_packages.py` uses `list[Path]`, `Path | None`; `test_list_packages.py` uses `tuple[str, int]`. No `typing.Dict`/`List`/`Optional`/`Union` were found under `scripts/`. The implementer should still audit both files and any other script modules for old-style hints and apply the rules; if none are found, validation is limited to running the script test suite to confirm no regressions.

## Test Strategy

- **No new test cases.** Refactor-only; existing tests in `scripts/tests/` remain the behavioural specification.
- **TDD:** Not applicable for new behaviour. Run the script test suite before and after edits to guard against regressions.
- **Execution:** From repo root, run script tests as defined by the project (e.g. `pytest scripts/tests -v` or per `.github/workflows/script-tests.yml`). Ensure the venv is active and pytest is available.
- **Static checks:** Task 01 does not add Ruff/mypy for `scripts/` at repo root. If a later change adds Ruff/mypy for scripts, this refactor leaves scripts compliant with 3.12 style so no follow-up is required.

## Implementation Order

1. From repo root (with venv active), run `pytest scripts/tests -v` to establish a passing baseline.
2. Audit `scripts/list_packages.py`: search for `Optional`, `Union`, `Dict`, `List`, `Set`, `Tuple` from `typing` or `typing.`; replace with `X | None`, `X | Y`, and built-in generics; remove unused `typing` imports; keep `from __future__ import annotations`.
3. Audit `scripts/tests/test_list_packages.py`: same replacement rules; remove unused typing imports.
4. Re-run `pytest scripts/tests -v`; all tests must pass (no regressions).
5. If the project documents or uses a different command for script tests (e.g. a Make target or CI path), run that instead and confirm pass.

## Validation Steps

1. **Script tests:** From repo root, `pytest scripts/tests -v` (or project-equivalent) exits 0; no failing tests unless explicitly marked as expected failure.
2. **Inspection:** Both `scripts/list_packages.py` and `scripts/tests/test_list_packages.py` use only 3.12-style type hints (pipe unions, built-in generics) and only necessary imports from `typing` (e.g. `Any`, `cast`), with no remaining `Optional`/`Union`/`Dict`/`List`/`Set`/`Tuple` from `typing`.

## Documentation Updates

- None required for this task. Changelog entries for the typing-312-standards feature are handled in Task 10 (update-changelogs).
- If `docs/` or README describes script usage or typing, no change is mandated; the refactor does not alter script behaviour or CLI.
