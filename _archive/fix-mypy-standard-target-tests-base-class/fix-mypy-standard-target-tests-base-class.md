# fix-mypy-standard-target-tests-base-class

## The request

CI ran `uv run mypy .` from each plugin directory, so mypy type-checked the whole tree (source and `tests/`). In plugins using the SDK standard-target pattern (e.g. `loaders/target-gcs`), test code assigns `StandardTargetTests = get_target_test_class(...)` and uses it as a base class. Mypy treats that as a variable, not a type alias, and reported `[valid-type]` and `[misc]` (invalid base class) in `tests/test_core.py` at line 22. CI failed; pytest passed. Expected: mypy validates production source only, or test code is valid; CI mypy step should pass. Root cause: mypy scope—CI invoked mypy with `.` instead of restricting to the source package.

## Planned approach

**Chosen fix (Solution A):** In `.github/workflows/plugin-unit-tests.yml`, derive the mypy package name from `matrix.path` (last path component, hyphens → underscores, e.g. `loaders/target-gcs` → `target_gcs`) and run `uv run mypy <package>` instead of `uv run mypy .`. No plugin `pyproject.toml` or test changes. This aligns CI with `scripts/run_plugin_checks.sh` and each plugin’s `install.sh`, which already run mypy on the source package only. Alternatives (per-plugin exclude, per-plugin packages config, or type workarounds in tests) were rejected: either add per-plugin config, still require a workflow change, or conflict with “type-check production only.” Single task: update the Mypy step in the workflow to set `pkg` via a shell one-liner (e.g. `sed 's|.*/||;s/-/_/g'` on `matrix.path`) and invoke `uv run mypy "$pkg"`. Regression: existing CI (Plugin unit tests matrix) must pass for all jobs, including the Mypy step.

## What was implemented

The Mypy step in `.github/workflows/plugin-unit-tests.yml` was updated to derive the package name from `matrix.path` and run mypy on that package only. The step now runs:

```yaml
- name: Mypy
  run: |
    pkg=$(echo "${{ matrix.path }}" | sed 's|.*/||;s/-/_/g')
    uv run mypy "$pkg"
```

No plugin source, tests, or config were changed. CI passes for all matrix jobs (e.g. `loaders/target-gcs`, `taps/restful-api-tap`). The fix is recorded under **Fixed** in `CHANGELOG.md` with a link to this summary.
