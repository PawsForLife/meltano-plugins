# Pipeline Scratchpad

## Feature: normalise-plugin-source-folders

**Pipeline State**: Phase 1 Complete, Phase 2 Complete, Phase 3 Complete, Phase 4 Complete, Phase 5–6 Not started  
**Task Completion Status**: Task 01-rename-source-directory completed (validation complete; pytest/mypy in target-gcs expected to fail until task 03). Task 02-update-plugin-config completed. Task 03-update-python-imports-and-tests completed.  
**Execution Order**: 01-rename-source-directory.md, 02-update-plugin-config.md, 03-update-python-imports-and-tests.md, 04-update-repository-tooling.md, 05-update-documentation.md.

Task 01-rename-source-directory completed, validation complete.

Task 02-update-plugin-config completed.

Task 03-update-python-imports-and-tests completed.

Task plan created: 05-update-documentation at plans/tasks/05-update-documentation.md

Task plan created: 04-update-repository-tooling at plans/tasks/04-update-repository-tooling.md  
Task plan created: 03-update-python-imports-and-tests at plans/tasks/03-update-python-imports-and-tests.md

Task plan created: 02-update-plugin-config at plans/tasks/02-update-plugin-config.md

Task plan created: 01-rename-source-directory at plans/tasks/01-rename-source-directory.md

**Phase 1 Research summary**  
- **Feature**: Normalise plugin source folder names.  
- **Output**: `_features/normalise-plugin-source-folders/planning/` (impacted-systems.md, new-systems.md, possible-solutions.md, selected-solution.md).  
- **Key findings**: Only loaders/target-gcs violates the rule (source `gcs_target` → `target_gcs`). Impact: plugin dir rename; pyproject.toml, meltano.yml, install.sh; all Python imports and test patches; scripts/run_plugin_checks.sh and CI mypy derivation; AI context and root docs. No new systems; tooling can use a single rule (plugin dir name with `-` → `_`) and drop the target-gcs exception.  
- **Selected solution**: Internal rename of `gcs_target/` to `target_gcs/` plus reference updates everywhere and simplification of package-name derivation in run_plugin_checks.sh and CI.

**Phase 2 Plan summary**  
- **Plan location**: `_features/normalise-plugin-source-folders/plans/master/` (overview.md, architecture.md, interfaces.md, implementation.md, testing.md, dependencies.md, documentation.md).  
- **Key decisions**: Single task (rename + reference updates; no separate config/tests tasks). Order: (1) rename directory, (2) plugin config (pyproject.toml, meltano.yml, install.sh), (3) Python imports and test patches, (4) scripts/run_plugin_checks.sh and CI workflow, (5) docs. Established rule: `source_pkg = plugin_dir_name.replace("-", "_")`; tooling uses one derivation rule, no target-gcs or target-* exceptions.

---

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
