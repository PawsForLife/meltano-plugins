# Pipeline Scratchpad

## Bug: mypy-standard-target-tests-base-class

**Pipeline State**: Phase 1 Complete, Phase 2 Complete, Phase 3 Complete

### Investigation
- **Directory**: `_bugs/mypy-standard-target-tests-base-class/investigation/`
- **Root cause hypothesis**: MyPy treats `StandardTargetTests` (assigned from `get_target_test_class(...)`) as a variable, not a type alias; using it as a base class is rejected (valid-type, invalid base class).
- **Affected components**: `loaders/target-gcs/tests/test_core.py`; CI runs `mypy .`, local/install.sh runs `mypy gcs_target` (tests not checked).

### Research (Phase 2 Complete)
- **Findings**: MyPy rejects variables as base classes; annotating as `Any` is a standard workaround. Chosen solution: `StandardTargetTests: Any = get_target_test_class(...)`.

### Plan (Phase 3 Complete)
- **Location**: `_bugs/mypy-standard-target-tests-base-class/plans/master/`
- **Fix**: Add type annotation `StandardTargetTests: Any = get_target_test_class(...)` in `loaders/target-gcs/tests/test_core.py`. No new tests; validate with `uv run mypy .` and `uv run pytest`.
