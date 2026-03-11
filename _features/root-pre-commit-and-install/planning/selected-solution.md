# Selected Solution — root-pre-commit-and-install

## Choice

Use **pre-commit with a single local hook** that invokes a **wrapper script**. The script discovers plugin directories (same as CI via `scripts/list_packages.py`), then for each plugin runs ruff (check + format) and mypy using that plugin’s `.venv`. Optionally run pytest in the same or a separate hook. Root `install.sh` discovers plugins and runs each plugin’s `./install.sh`. No external library beyond pre-commit (already in use); the rest is repo-owned scripts and config.

---

## 1. Root `install.sh`

- **Discovery**: Run `python scripts/list_packages.py .` from repo root; iterate over output lines (one path per line). This matches CI and avoids hardcoding plugin list.
- **Action**: For each path `$dir`, run `(cd "$dir" && ./install.sh)`; if any exits non-zero, record failure and either stop immediately or continue (recommend: stop on first failure for clear feedback).
- **Prereqs**: Bash; Python for list_packages; each plugin must have an executable `install.sh` (already true).
- **Location**: Repo root, executable.

---

## 2. Root `.pre-commit-config.yaml`

- **Structure**: `repos:` with one `repo: local` block. Hooks use `language: system` and `entry` pointing at a script (or `bash -c '...'` that runs the script).
- **Entry**: Call a single script, e.g. `scripts/run_plugin_checks.sh`, which performs discovery and runs per-plugin checks. Use `pass_filenames: false` and `files` regex so the hook runs when any plugin file changes (e.g. `^taps/|^loaders/`) or use `always_run: true` to run on every commit.
- **Stages**: Default (pre-commit) for ruff/mypy; pytest can stay pre-commit or move to pre-push if too slow (implementation choice).
- **Mypy package name**: Script must know the mypy target per plugin (e.g. `restful_api_tap`, `gcs_target`). Options: (a) derive from directory name (e.g. `restful-api-tap` → `restful_api_tap`, `target-gcs` → `gcs_target` by convention), (b) read package name from plugin’s `pyproject.toml` (e.g. `[tool.pytest.ini_options]` or package name), or (c) maintain a small map in the script. Recommended: derive from directory name with a fallback map for exceptions so new plugins follow the same convention without editing the script.

---

## 3. Wrapper script (e.g. `scripts/run_plugin_checks.sh`)

- **Input**: Repo root as working directory; optionally receive list of dirs from `list_packages.py` (script can run `list_packages.py` itself).
- **Logic**:
  1. Run `python scripts/list_packages.py .` to get plugin paths.
  2. For each path: `cd` to path, check `.venv` exists (else skip or fail with clear message), then run:
     - `.venv/bin/ruff check .`
     - `.venv/bin/ruff format --check .`
     - `.venv/bin/mypy <package>` (package from path→package mapping above).
  3. Optionally run `.venv/bin/pytest` per plugin (or separate hook).
  4. Exit non-zero if any command fails.
- **Output**: Clear per-plugin success/failure; script exit code = failure if any plugin failed.
- **Portability**: Use `#!/usr/bin/env bash` and avoid bash-only features if we want zsh compatibility; otherwise bash is fine.

---

## 4. Plugin-level `.pre-commit-config.yaml`

- **loaders/target-gcs** currently has its own `.pre-commit-config.yaml` (Ruff only). Decision: **keep it as optional** for contributors who work only in that plugin and run pre-commit from that directory; root config is the standard for “whole repo” commits. No need to remove it unless we want a single source of truth (then remove and document that root pre-commit covers all plugins).

---

## 5. Documentation updates

- **README.md**: Add a short “Development / Contributing” (or similar) section: run `./install.sh` at repo root to bootstrap all plugins; install pre-commit and run `pre-commit install` to run ruff/mypy (and optionally pytest) on commit; run `pre-commit run --all-files` to check everything.
- **docs/monorepo/README.md**: State that root `install.sh` runs each plugin’s `install.sh` and that root pre-commit runs ruff, mypy (and optionally pytest) per plugin using each plugin’s venv.
- **docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md**: Add root-level commands (root `./install.sh`, `pre-commit install`, `pre-commit run --all-files`); keep per-plugin commands for single-plugin workflows.

---

## 6. Adherence to development practices

- **TDD**: Feature specifies no new application tests; validation is behavioural (root `install.sh` runs, all plugin installs/tests pass, `pre-commit run --all-files` succeeds). Any script tests would assert discovery and exit codes, not internal call counts.
- **DI / non-determinism**: Discovery and paths are deterministic; no time or external API in the hook. If we add a “skip if no .venv” option, it remains a simple conditional.
- **Black box**: Acceptance is “scripts run and overall outcome is pass/fail”; no assertion on how many times a tool is invoked.

---

## 7. Validation (from feature file)

- Root `install.sh` runs successfully and all plugin installs/tests pass.
- `pre-commit run --all-files` succeeds.
- No new application unit tests required; regression gate remains existing plugin test suites and CI.
