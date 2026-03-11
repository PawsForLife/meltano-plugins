# Task Plan: 01 — Wrapper script `scripts/run_plugin_checks.sh`

## Overview

This task delivers the wrapper script that root pre-commit will invoke. The script discovers plugin directories via `scripts/list_packages.py` (same source of truth as CI and root install), then for each plugin runs ruff (check + format) and mypy using that plugin's `.venv`, with optional pytest when `RUN_PYTEST=1`. It is the first deliverable in the feature; it has no dependencies on other feature tasks. Success is defined by: script is executable, resolves repo root from its own location, runs discovery, derives mypy package names (including fallback map), runs per-plugin checks in order and exits on first failure with a clear message when `.venv` is missing.

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `scripts/run_plugin_checks.sh` | **Create** | New Bash script. See Implementation Order for full contents and behaviour. |
| (none) | — | No existing files are modified by this task. |

**Script contract (create only):**

- **Path**: `scripts/run_plugin_checks.sh`
- **Shebang**: `#!/usr/bin/env bash`
- **Top-of-file comment**: State purpose: run ruff and mypy per plugin using each plugin's venv; discovery via `list_packages.py`; optional pytest via `RUN_PYTEST=1`.
- **Repo root**: Resolve from script location: `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`, then `ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"`.
- **Discovery**: Run `python "$ROOT/scripts/list_packages.py" "$ROOT"` (no `--json`). Output is one relative path per line (e.g. `taps/restful-api-tap`, `loaders/target-gcs`). Iterate each line as the plugin path.
- **Per plugin**: For each path:
  - `cd "$ROOT/$path"` (or equivalent so CWD is the plugin directory).
  - If `.venv` is missing: print a clear message to stderr (e.g. "Missing .venv in $path; run root install.sh first.") and exit non-zero (e.g. 1).
  - Run in order: `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`, `.venv/bin/mypy <package>` where `<package>` is the derived mypy package name (see below). If `RUN_PYTEST=1` (default unset/off): run `.venv/bin/pytest`. On first non-zero exit from any of these, exit immediately with that exit code.
- **Package name for mypy**: Derive from the last path component of the relative path (e.g. `taps/restful-api-tap` → `restful-api-tap`). Apply fallback map first; if no map entry, apply default rule.
  - **Fallback map**: `restful-api-tap` → `restful_api_tap`; `target-gcs` → `gcs_target`. Implement via Bash associative array or case statement.
  - **Default rule**: If the last component matches `target-*`, use `*_target` with `-` replaced by `_` (e.g. `target-gcs` → `gcs_target`). Otherwise replace `-` with `_` in the last component (e.g. `some-tap` → `some_tap`).
- **Exit behaviour**: On first failure (non-zero from ruff check, ruff format --check, mypy, or pytest), exit with that non-zero code. If all plugins and all checks pass, exit 0.
- **Permissions**: Script must be executable (`chmod +x scripts/run_plugin_checks.sh`).

## Test Strategy

- **No new application unit tests** (per master testing.md). This task does not add or change Python application code.
- **Validation is behavioural**: From repo root, after all plugin venvs exist (e.g. after each plugin's `./install.sh` has been run), executing `./scripts/run_plugin_checks.sh` must exit 0 when all checks pass. When a plugin has no `.venv` or a check fails (e.g. mypy error in a plugin), the script must exit non-zero and (for missing .venv) emit a clear message.
- **Optional black-box script test** (implementer may add): Assert exit code only — e.g. from repo root with all venvs present and passing checks, exit 0; with a missing `.venv` in one plugin or a failing check, exit non-zero. Do not assert call counts, log lines, or internal invocations (per development_practices.mdc).
- **TDD**: If optional script tests are added, write the test first (e.g. "wrapper exits 0 when all plugins have venv and pass") then implement to satisfy it. If no script tests are added, implement then validate manually.

## Implementation Order

1. **Create script file**  
   Create `scripts/run_plugin_checks.sh` with shebang and top-of-file comment describing purpose, discovery via `list_packages.py`, and optional pytest.

2. **Resolve repo root**  
   Set `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` and `ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"`. Use `$ROOT` for all subsequent paths.

3. **Run discovery**  
   Run `python "$ROOT/scripts/list_packages.py" "$ROOT"` and capture line output. Ensure script is invoked with one argument (root directory); see `scripts/list_packages.py` (optional first positional `root`). Iterate over each line (strip whitespace; skip empty lines if any).

4. **Implement mypy package name derivation**  
   - Extract last path component from each relative path (e.g. `taps/restful-api-tap` → `restful-api-tap`).
   - Implement fallback map: `restful-api-tap` → `restful_api_tap`, `target-gcs` → `gcs_target` (Bash: associative array with `declare -A` or case statement).
   - Default: if component matches `target-*`, output `*_target` with `-`→`_` in the middle part; else replace all `-` with `_` in the component.
   - Expose as a function or inline logic so each plugin path maps to a single package name string.

5. **Per-plugin loop**  
   For each discovered path:
   - `cd "$ROOT/$path"` (in a subshell or restore CWD after if not using subshell to avoid affecting subsequent iterations).
   - If `[ ! -d .venv ]`: print clear error to stderr, exit 1 (or non-zero).
   - Run `.venv/bin/ruff check .`; on non-zero exit, exit with that code.
   - Run `.venv/bin/ruff format --check .`; on non-zero exit, exit with that code.
   - Run `.venv/bin/mypy <package>` with the derived package name; on non-zero exit, exit with that code.
   - If `RUN_PYTEST=1` (or equivalent check): run `.venv/bin/pytest`; on non-zero exit, exit with that code.
   - If using subshell per plugin, ensure exit code from the subshell is propagated (e.g. `(cd ... && ...) || exit $?`).

6. **Exit 0**  
   After all plugins are processed successfully, exit 0.

7. **Make executable**  
   Run `chmod +x scripts/run_plugin_checks.sh` (or document that the implementer must do so).

## Validation Steps

1. **From repo root**, ensure each plugin has a valid `.venv` (e.g. run each plugin's `./install.sh` from its directory).
2. Run `./scripts/run_plugin_checks.sh` from repo root; **expect exit code 0** and ruff/mypy output indicating all plugins were checked.
3. **Negative: missing .venv** — Temporarily rename or remove one plugin's `.venv`, run the script from repo root; **expect non-zero exit** and a clear message that `.venv` is missing (e.g. in stderr). Restore `.venv` afterward.
4. **Negative: failing check** — Introduce a mypy error in one plugin (or a ruff violation), run the script; **expect non-zero exit** with the failing tool's output. Revert the test change.
5. **Optional**: With `RUN_PYTEST=1`, run the script; **expect** pytest to run per plugin and exit 0 when all tests pass; or non-zero when a test fails.
6. **Regression**: Existing plugin test suites and CI remain unchanged; no new application tests required. If optional script tests were added, run them and ensure they pass.

## Documentation Updates

- **None for this task.** Root README, docs/monorepo, and AI_CONTEXT_QUICK_REFERENCE are updated in task 04 (documentation-updates). The only documentation for this task is the script's own top-of-file comment (part of implementation).

## Dependencies

- **list_packages.py**: Must be callable as `python "$ROOT/scripts/list_packages.py" "$ROOT"`; outputs one relative path per line (no `--json`). Existing script; no changes in this task.
- **Plugin layout**: Each discovered path must contain `.venv/bin/ruff`, `.venv/bin/mypy`, and (if RUN_PYTEST=1) `.venv/bin/pytest`. No changes to plugins in this task.
- **Environment**: Bash, Python (for list_packages.py), and per-plugin venvs are assumed; no new dependencies or config files.

## Reference

- Master plan: `_features/root-pre-commit-and-install/plans/master/` (overview.md, implementation.md, testing.md).
- Interfaces: `plans/master/interfaces.md` — wrapper script invocation, discovery contract, mypy package derivation.
- Discovery: `scripts/list_packages.py` — optional first arg `root` (default CWD); line output is relative paths, sorted; excludes .git, .venv, _archive, node_modules.
