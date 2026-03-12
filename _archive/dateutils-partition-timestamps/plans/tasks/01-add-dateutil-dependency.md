# Task Plan: 01-add-dateutil-dependency

## Overview

This task adds the **python-dateutil** dependency to the target-gcs package so that later tasks can use `dateutil.parser.parse` and `dateutil.parser.ParserError` in partition path resolution. It is the prerequisite for all dateutil implementation work; it has no dependencies on other tasks and introduces no interface or model changes.

**Scope:** Dependency declaration and environment verification only. No production code or test cases are added in this task.

---

## Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `loaders/target-gcs/pyproject.toml` | Modify | Add one dependency to `[project].dependencies`. |

**Specific change in `loaders/target-gcs/pyproject.toml`:**

- In the `dependencies` list (under `[project]`), add: `python-dateutil>=2.8.1`.
- Optional, per project version policy: use `python-dateutil>=2.8.1,<3` if the project constrains major versions. Version 2.8.1+ provides `ParserError` and `UnknownTimezoneWarning` reliably (see `plans/master/dependencies.md`).
- Preserve existing dependency order and formatting (e.g. one entry per line, trailing comma if present).

No new files are created. No other files are modified.

---

## Test Strategy

- **No new test file or test case** is required for this task.
- Verification is environment-based: after adding the dependency and running the install script, the implementer confirms that:
  1. `from dateutil import parser` succeeds in the target-gcs environment.
  2. `from dateutil.parser import ParserError` succeeds.
  3. The existing test suite runs successfully (e.g. `uv run pytest` from `loaders/target-gcs/`), ensuring the new dependency does not break current tests.

Later tasks (e.g. 02–05) will add or adjust tests that use dateutil; those tests will implicitly validate that the dependency is correctly declared and installed.

---

## Implementation Order

1. **Edit `loaders/target-gcs/pyproject.toml`**
   - Open the `dependencies` list under `[project]`.
   - Add `"python-dateutil>=2.8.1"` (or `"python-dateutil>=2.8.1,<3"` if the project uses an upper bound). Place it in a consistent position (e.g. alphabetical or after existing runtime deps); the master plan does not prescribe order.

2. **Run the project install script**
   - From the repository root or from `loaders/target-gcs/`, run the plugin’s install script (e.g. `./install.sh` inside `loaders/target-gcs/`). This ensures the lockfile (e.g. `uv.lock`) and the virtual environment are updated with the new dependency. Use the project’s preferred method (see `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md`: target-gcs uses `uv sync`; `install.sh` runs venv creation, sync, lint, typecheck, and tests).

3. **Verify imports and tests**
   - With the target-gcs venv active (e.g. `source loaders/target-gcs/.venv/bin/activate`), run:
     - `python -c "from dateutil import parser; from dateutil.parser import ParserError; print('OK')"`
     - `uv run pytest` (or the project’s test command) from `loaders/target-gcs/`.
   - Both must succeed.

---

## Validation Steps

- [ ] `loaders/target-gcs/pyproject.toml` contains `python-dateutil>=2.8.1` (or with `,<3`) in `[project].dependencies`.
- [ ] `./install.sh` (in `loaders/target-gcs/`) completes without error.
- [ ] In the target-gcs environment, `from dateutil import parser` and `from dateutil.parser import ParserError` execute without error.
- [ ] The full target-gcs test suite passes (`uv run pytest` from `loaders/target-gcs/`).
- [ ] Linters and type checker (e.g. `ruff check .`, `ruff format --check`, `mypy target_gcs`) still pass per project rules; no code changes in this task, so no new lint/type issues are expected.

---

## Documentation Updates

- **None required for this task.** No user-facing behaviour or public API changes.
- Optional (not required by this task): a later documentation task (e.g. task 08) may update `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` or dependency lists to mention python-dateutil; that is out of scope for 01-add-dateutil-dependency.

---

## References

- Task doc: `_features/dateutils-partition-timestamps/tasks/01-add-dateutil-dependency.md`
- Master plan: `_features/dateutils-partition-timestamps/plans/master/overview.md`, `implementation.md` (Step 1), `dependencies.md`
- Environment: `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md` (target-gcs commands, uv, install.sh)
