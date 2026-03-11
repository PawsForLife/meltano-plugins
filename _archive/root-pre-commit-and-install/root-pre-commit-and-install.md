# root-pre-commit-and-install — Archive Summary

## The request

Plugins (taps, loaders) each had their own `install.sh` and used ruff, mypy, and pytest, but there was no root-level automation to run these consistently before push or to bootstrap all plugins. The goal was to standardise formatting, lint, type-check, and test runs across plugins and catch issues before deployment.

**Requirements:**

- Add a root `.pre-commit-config.yaml` that runs mypy and ruff (format + check) for each plugin using each plugin folder’s virtual environment.
- Add a root `install.sh` that discovers and runs each plugin’s `install.sh` (e.g. by discovering plugin-type folders such as `taps/*/`, `loaders/*/`).
- Document pre-commit hook installation and ensure hooks invoke ruff, mypy, and pytest per plugin in that plugin’s venv.

**Testing:** No new application tests; validation is that root `install.sh` runs and all plugin installs/tests pass, and that `pre-commit run --all-files` succeeds.

---

## Planned approach

**Selected solution:** Pre-commit with a single local hook that invokes a wrapper script. The script discovers plugin directories using the same mechanism as CI (`scripts/list_packages.py`), then for each plugin runs ruff (check + format) and mypy using that plugin’s `.venv`. Pytest is optional (e.g. via `RUN_PYTEST=1`). Root `install.sh` discovers plugins and runs each plugin’s `./install.sh`. No external library beyond pre-commit; the rest is repo-owned scripts and config.

**Key decisions:**

- **Discovery:** Reuse `scripts/list_packages.py` so root `install.sh` and root pre-commit use the same list as CI. Output: one relative path per line. New plugins are included automatically.
- **Mypy package name:** Derived from directory name (e.g. `restful-api-tap` → `restful_api_tap`, `target-gcs` → `gcs_target`) with a fallback map for exceptions.
- **Plugin-level pre-commit:** Keep `loaders/target-gcs/.pre-commit-config.yaml` as optional for single-plugin workflows; root config is the standard for whole-repo commits.
- **Failure behaviour:** Root install stops on first failing plugin; wrapper script exits on first failing check. Pre-commit install runs after all plugin installs succeed; root install installs pre-commit via pip if missing.

**Architecture:**

- **Root `install.sh`:** Resolve repo root, run `list_packages.py`, for each path run `(cd "$ROOT/$path" && ./install.sh)`; stop on first failure. Then ensure pre-commit is available (install via pip if not), run `pre-commit install` at root.
- **Wrapper script** (`scripts/run_plugin_checks.sh`): Resolve root from script location, run `list_packages.py`, for each path cd to path, require `.venv`, run `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`, `.venv/bin/mypy <package>`; optionally `.venv/bin/pytest` when `RUN_PYTEST=1`. Exit on first failure.
- **Root `.pre-commit-config.yaml`:** One `repo: local` hook, `language: system`, entry = wrapper script; `pass_filenames: false`; `files: '^taps/|^loaders/'` (or `always_run: true`).

**Task breakdown (order):**

1. Wrapper script `scripts/run_plugin_checks.sh`
2. Root `install.sh`
3. Root `.pre-commit-config.yaml` (depends on task 01)
4. Documentation updates (README, docs/monorepo, AI_CONTEXT_QUICK_REFERENCE)

---

## What was implemented

All four tasks were completed.

**Task 01 — Wrapper script:** `scripts/run_plugin_checks.sh` was added. It resolves repo root from script location, runs `python "$ROOT/scripts/list_packages.py" "$ROOT"`, and for each path runs ruff check, ruff format --check, and mypy using that path’s `.venv`. Mypy package name is derived via `get_mypy_package()` with a fallback map (`restful-api-tap` → `restful_api_tap`, `target-gcs` → `gcs_target`) and default rules (target-* → *_target, else replace `-` with `_`). If `.venv` is missing, the script prints a clear message and exits non-zero. Optional pytest runs when `RUN_PYTEST` is set and non-zero. The script uses `set -e` and exits on first failure.

**Task 02 — Root install.sh:** `install.sh` at repository root was added. It sets `ROOT` from `BASH_SOURCE`, discovers plugin paths via `list_packages.py`, and runs `(cd "$ROOT/$path" && ./install.sh)` for each path (stop on first failure). It then ensures pre-commit is available (installs via `pip3` or `pip` if missing) and runs `pre-commit install` from repo root. Line trimming and empty-line handling are applied to discovery output.

**Task 03 — Root pre-commit config:** `.pre-commit-config.yaml` at repository root was added with a single local hook: id `plugin-checks`, name "Run plugin checks (ruff, mypy)", entry `scripts/run_plugin_checks.sh`, `language: system`, `pass_filenames: false`, `files: '^taps/|^loaders/'`. Plugin-level config at `loaders/target-gcs/.pre-commit-config.yaml` was left unchanged.

**Task 04 — Documentation:** README.md was updated with a Development section describing root `./install.sh`, pre-commit install, and `pre-commit run --all-files`. docs/monorepo/README.md was updated to describe root install.sh (discovery via `list_packages.py`, running each plugin’s install.sh) and root pre-commit (ruff, mypy, optionally pytest per plugin using that plugin’s venv). docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md was updated with Repo root commands and removal of "No repo-wide install.sh" wording.

**Validation:** Success criteria met: root `./install.sh` runs and all plugin installs/tests pass; `pre-commit run --all-files` succeeds. No new application unit tests were added; regression gate remains existing plugin test suites and CI.
