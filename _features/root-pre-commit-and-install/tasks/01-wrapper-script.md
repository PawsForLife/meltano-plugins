# Task 01: Wrapper script `scripts/run_plugin_checks.sh`

## Background

Root pre-commit must run ruff and mypy (and optionally pytest) per plugin using each plugin's `.venv`. Pre-commit does not natively run per-subdirectory with that directory's venv. The plan therefore uses a single local hook that invokes a wrapper script. This script discovers plugin directories via `scripts/list_packages.py` (same source of truth as CI and root install), then for each path runs that plugin's venv binaries with correct working directory and mypy package name. This task has no dependencies on other feature tasks; it is the first deliverable in the implementation order.

## This Task

- **Create** `scripts/run_plugin_checks.sh`.
- **Shebang**: `#!/usr/bin/env bash`.
- **Repo root**: Resolve from script location (e.g. `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`, `ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"`).
- **Discovery**: Run `python "$ROOT/scripts/list_packages.py" "$ROOT"` (line output); iterate each line as the relative plugin path.
- **Per plugin**: For each path, `cd "$ROOT/$path"` (or handle paths as output by `list_packages.py`); if `.venv` is missing, exit non-zero with a clear message; run `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`, `.venv/bin/mypy <package>`; optionally run `.venv/bin/pytest` if env var (e.g. `RUN_PYTEST=1`) is set (default off).
- **Package name for mypy**: Derive from last component of path: replace `-` with `_`; for `target-*`, use `*_target` (e.g. `target-gcs` → `gcs_target`). Implement a small fallback map for exceptions (e.g. `restful-api-tap` → `restful_api_tap`, `target-gcs` → `gcs_target`). Default rule: `target-<name>` → `<name>_target` with `-`→`_`; else replace `-` with `_` in the last path component.
- **Exit behaviour**: On first failure (non-zero from any of ruff check, ruff format --check, mypy, or pytest), exit with that non-zero code; otherwise exit 0.
- **Top-of-file comment**: State purpose: run ruff and mypy per plugin using each plugin's venv; discovery via `list_packages.py`; optional pytest.
- **Make executable**: `chmod +x scripts/run_plugin_checks.sh`.

## Testing Needed

- No new application unit tests. Validation is behavioural: from repo root, after all plugin venvs exist, run `./scripts/run_plugin_checks.sh` and expect exit 0 when all checks pass; expect non-zero when a plugin has no `.venv` or when a check fails (e.g. mypy error in a plugin). Optional black-box script test: assert exit code of wrapper when run from root (all venvs present, all pass → 0; missing .venv or failing check → non-zero). Do not assert call counts or internal invocations.
