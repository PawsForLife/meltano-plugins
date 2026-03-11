# Testing — root-pre-commit-and-install

## Test Strategy

- **No new application unit tests** per feature file: validation is behavioural (root install runs, all plugin installs/tests pass; pre-commit run --all-files succeeds).
- Any **script tests** (if added) must be black-box: assert discovery output, exit codes, and observable outcomes; do not assert call counts or internal invocation details (per development_practices.mdc).
- **Regression gate**: Existing plugin test suites and CI remain the gate; no new pytest marks for expected failures.

## TDD Approach

- Feature does not require writing tests before implementation for application code (no new application code). For scripts, optional: write a small test that runs root install.sh in a subshell and checks exit code when all plugins succeed, or run wrapper script and check exit code. Such tests would run from repo root and require plugins to be in a valid state (venv present).
- If script tests are added: test first (e.g. “root install exits 0 when all plugin installs succeed”; “wrapper script exits non-zero when a plugin has no .venv” or “when mypy fails in a plugin”) then implement to satisfy them.

## Test Cases (Behavioural / Acceptance)

1. **Root install.sh**
   - **Success**: From repo root, run `./install.sh`; exit code 0; each plugin’s install.sh has run (observe by successful completion of ruff/mypy/pytest in each plugin). No assertion on number of invocations.
   - **Failure**: If a plugin’s install.sh fails (e.g. break a plugin temporarily), root install.sh exits non-zero and does not necessarily run remaining plugins (stop-on-first-failure).

2. **Pre-commit**
   - **Success**: After root `./install.sh`, run `pre-commit run --all-files`; exit code 0; all plugins’ ruff and mypy (and optionally pytest) pass. No assertion on how many times tools are invoked.
   - **Failure**: If a plugin has no .venv or mypy fails in a plugin, `pre-commit run --all-files` (or the wrapper script directly) exits non-zero.

3. **Discovery**
   - Plugin list matches `list_packages.py`: directories that contain `pyproject.toml` under root (excluding .git, .venv, _archive, node_modules) are the same set used by root install and wrapper script. Validated implicitly by success of (1) and (2).

## Integration / Manual Validation

- Run from repo root: `./install.sh` → expect 0.
- Run from repo root: `pre-commit run --all-files` → expect 0.
- Add a new plugin directory with pyproject.toml and install.sh → run root install and pre-commit → new plugin is included (no config edit). Manual or CI check.

## Optional Script Tests (Black-Box)

If adding automated script tests (e.g. in `scripts/tests/` or repo root test runner):

- **What to test**: Exit code of `./install.sh` when all plugins succeed; exit code of wrapper script when run from root with all venvs present and passing checks; exit code when a plugin lacks .venv or a check fails.
- **What not to test**: Number of times `list_packages.py` or install.sh is called; log lines; internal script structure. Validate functionality and outcomes only.

## Regression Gate

- All existing plugin tests must continue to pass. No changes to plugin code; root scripts only invoke existing install.sh and venv binaries. CI (plugin-unit-tests.yml) remains the regression gate for PRs.
