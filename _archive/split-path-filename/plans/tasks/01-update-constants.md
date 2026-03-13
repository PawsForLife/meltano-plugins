# Task Plan: 01 — Update Constants

## Overview

This task establishes the path and filename constants that replace config-driven `key_naming_convention`. It adds `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, and `FILENAME_TEMPLATE` to `constants.py`, removes `DEFAULT_KEY_NAMING_CONVENTION` and `DEFAULT_KEY_NAMING_CONVENTION_HIVE`, and updates `paths/__init__.py` exports. No task dependencies. This is the foundation for all path patterns (tasks 04–07).

**Scope boundary:** Only `constants.py` and `paths/__init__.py` are modified. Path modules (`simple.py`, `dated.py`, `partitioned.py`) and tests (`test_base.py`, `test_sinks.py`) that import the removed constants will have import errors until tasks 04–08 migrate them. Per the task document, those imports are fixed in subsequent tasks.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/target_gcs/constants.py` | Modify: add new constants, remove old constants |
| `loaders/target-gcs/target_gcs/paths/__init__.py` | Modify: remove exports of removed constants, add exports for new ones |

### constants.py — Specific Changes

| Change | Detail |
|--------|--------|
| Add | `PATH_SIMPLE = "{stream}/{date}"` |
| Add | `PATH_DATED = "{stream}/{hive_path}"` |
| Add | `PATH_PARTITIONED = "{stream}/{hive_path}"` |
| Add | `FILENAME_TEMPLATE = "{timestamp}.jsonl"` |
| Remove | `DEFAULT_KEY_NAMING_CONVENTION` |
| Remove | `DEFAULT_KEY_NAMING_CONVENTION_HIVE` |
| Keep | `DEFAULT_PARTITION_DATE_FORMAT = "year=%Y/month=%m/day=%d"` (unchanged) |

### paths/__init__.py — Specific Changes

| Change | Detail |
|--------|--------|
| Remove | Imports and `__all__` entries for `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE` |
| Add | Imports and `__all__` entries for `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE` (for convenience; path modules may import from `constants` directly) |

---

## Test Strategy

Per the task document: **No new unit tests for constants.** Values are used by path patterns; pattern tests (tasks 05–07) validate usage. Constants are simple string literals; black-box validation happens via path pattern behaviour.

**Existing tests that will fail after this task** (fixed in subsequent tasks):

- `tests/unit/paths/test_base.py` — imports removed constants; fixed in task 04 when `_MinimalPattern` is updated
- `tests/unit/test_sinks.py` — imports removed constants; fixed in task 08 when sinks config is updated
- `tests/unit/paths/test_simple.py`, `test_dated.py`, `test_partitioned.py` — path modules import removed constants; fixed in tasks 05–07

---

## Implementation Order

1. **Edit `constants.py`** — Add the four new constants above `DEFAULT_PARTITION_DATE_FORMAT`; remove `DEFAULT_KEY_NAMING_CONVENTION` and `DEFAULT_KEY_NAMING_CONVENTION_HIVE`.
2. **Edit `paths/__init__.py`** — Replace imports: remove `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`; add `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`. Update `__all__` accordingly.
3. **Validate modified files** — Run `ruff check target_gcs/constants.py target_gcs/paths/__init__.py` and `mypy target_gcs.constants` from `loaders/target-gcs/` (full `mypy target_gcs` will fail until path modules are migrated).

---

## Validation Steps

1. **Constants exist** — `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE` have exact values per spec.
2. **Old constants removed** — No references to `DEFAULT_KEY_NAMING_CONVENTION` or `DEFAULT_KEY_NAMING_CONVENTION_HIVE` in `constants.py` or `paths/__init__.py`.
3. **Ruff** — `uv run ruff check target_gcs/constants.py target_gcs/paths/__init__.py` passes.
4. **MyPy** — `uv run mypy target_gcs.constants` passes (isolated module check).
5. **Full project** — Run `uv run pytest` from `loaders/target-gcs/`; expect failures in path and sink tests. Acceptable until tasks 04–08 complete.

---

## Documentation Updates

- **None** for this task. `AI_CONTEXT_target-gcs.md` and README will be updated in task 10 (documentation).

---

## Post-Task State

- New constants are available for tasks 04–07.
- Path modules and tests will have import errors until tasks 04–08 migrate them.
- Implementer may proceed to task 02 (fix date_as_partition) immediately; the branch will be broken until task 05 at minimum.
