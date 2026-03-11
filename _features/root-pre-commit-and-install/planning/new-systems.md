# New Systems — root-pre-commit-and-install

## Summary

This document describes the new artefacts and behaviours introduced by the feature. All are at repository root or in shared scripts; no new application modules inside plugin packages.

---

## 1. Root `install.sh`

| Attribute | Description |
|-----------|-------------|
| **Location** | Repository root: `install.sh`. |
| **Purpose** | One-command bootstrap of all plugins: discover plugin directories, then for each run that plugin’s `install.sh`. |
| **Behaviour** | Discover plugins (e.g. via `scripts/list_packages.py` or globs `taps/*/`, `loaders/*/` with `pyproject.toml` or `install.sh`). For each directory, run `./install.sh` from that directory (e.g. `cd "$dir" && ./install.sh`). Aggregation of exit codes: either fail on first failure or run all and report (implementation choice). |
| **Dependencies** | Bash; `scripts/list_packages.py` if used for discovery; each plugin’s `install.sh` must exist and be executable. |
| **Invocation** | From repo root: `./install.sh`. No arguments required. |

---

## 2. Root `.pre-commit-config.yaml`

| Attribute | Description |
|-----------|-------------|
| **Location** | Repository root: `.pre-commit-config.yaml`. |
| **Purpose** | Run ruff (check + format) and mypy (and optionally pytest) for each plugin using that plugin’s virtual environment, so hooks use the same tool versions and config as the plugin. |
| **Behaviour** | One or more local hooks (`repo: local`) that, for each discovered plugin directory: (1) use that directory’s `.venv` (e.g. `plugin/.venv/bin/ruff`), (2) run from that directory so paths and `pyproject.toml` are correct, (3) run ruff check, ruff format --check, mypy with the correct package name for that plugin. Optionally a separate hook or stage for pytest. Hooks must discover plugin list (same discovery as root `install.sh`). |
| **Dependencies** | pre-commit installed (system or repo); plugin directories must have `.venv` (e.g. after running root `install.sh` or each plugin’s `install.sh`). |

---

## 3. Optional: helper script for pre-commit

| Attribute | Description |
|-----------|-------------|
| **Location** | e.g. `scripts/run_plugin_checks.sh` or equivalent. |
| **Purpose** | Single entry point for “run ruff + mypy (and optionally pytest) in each plugin with its venv”. Pre-commit config then has one local hook that invokes this script. |
| **Behaviour** | Input: list of plugin directories (from stdin, args, or by calling `list_packages.py`). For each dir: `cd` to dir, run `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`, `.venv/bin/mypy <package>`, optionally `.venv/bin/pytest`. Package name for mypy can be derived (e.g. from directory name or a small mapping). Exit non-zero if any step fails. |
| **Alternative** | Inline in `.pre-commit-config.yaml` with `language: system` and `entry: bash -c '...'` that loops over directories; script is clearer and testable. |

---

## 4. Pre-commit hook installation and docs

| Attribute | Description |
|-----------|-------------|
| **New behaviour** | Users run `pre-commit install` at repo root so that git commit triggers the root config. Document in README (and optionally docs/monorepo, QUICK_REFERENCE) that contributors should: (1) run root `./install.sh`, (2) install pre-commit (`pip install pre-commit` or equivalent), (3) run `pre-commit install`. |
| **Validation** | Feature acceptance: root `install.sh` runs and all plugin installs/tests pass; `pre-commit run --all-files` succeeds. |

---

## 5. Plugin discovery contract

| Attribute | Description |
|-----------|-------------|
| **Source of truth** | Reuse `scripts/list_packages.py` so root `install.sh` and root pre-commit use the same list as CI. Discovery = directories under root that contain `pyproject.toml`, excluding `.git`, `.venv`, `_archive`, `node_modules`. |
| **Mypy package name** | Not provided by list_packages. Options: (a) derive from directory name (e.g. `restful-api-tap` → `restful_api_tap`, `target-gcs` → `gcs_target`), (b) read from plugin’s `pyproject.toml` (e.g. package name), or (c) small root-level mapping. Implementation detail in selected-solution. |

---

## 6. No new systems

- No new Python packages or modules inside `taps/` or `loaders/`.
- No new CI jobs; existing plugin-unit-tests workflow remains.
- No new Meltano or Singer behaviour.
