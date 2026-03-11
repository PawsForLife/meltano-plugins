# Pipeline Scratchpad

## Feature: root-pre-commit-and-install

- **Pipeline State:** Phase 1 Complete; Phase 2 Complete; Phase 3 Complete.
- **Output directory:** _features/root-pre-commit-and-install/planning/
- **Plan location:** _features/root-pre-commit-and-install/plans/master/
- **Key decisions:**
  - Discovery: Reuse `scripts/list_packages.py` (line output) for both root install.sh and wrapper script; single source of truth with CI.
  - Root install: Stop on first plugin failure; no changes to plugin install.sh.
  - Pre-commit: One local hook (`language: system`) invoking `scripts/run_plugin_checks.sh`; mypy package name derived from directory name with fallback map (e.g. target-gcs → gcs_target).
  - No new application tests; validation is behavioural (install.sh and pre-commit run --all-files succeed); optional black-box script tests for exit codes only.
- **Key findings:**
  - Root has no install.sh or .pre-commit today; plugins each have install.sh (uv, ruff, mypy, pytest) and target-gcs has a Ruff-only .pre-commit-config.yaml.
  - CI uses scripts/list_packages.py for discovery; same script can drive root install.sh and root pre-commit for one source of truth.
  - pre-commit local hooks (repo: local, language: system) with a wrapper script that discovers plugins and runs each plugin’s .venv/bin/ruff and .venv/bin/mypy (and optionally pytest) are the right fit; pre-commit does not natively run “per subdirectory with that dir’s venv.”
  - Adding a new plugin stays automatic if discovery is list_packages.py; mypy package name can be derived from directory name (e.g. restful-api-tap → restful_api_tap) with an optional fallback map.
- **Selected solution:** Pre-commit with a single local hook that invokes a wrapper script; the script uses list_packages.py to discover plugins and runs ruff + mypy (and optionally pytest) per plugin using that plugin’s .venv; root install.sh discovers plugins via list_packages.py and runs each plugin’s ./install.sh.
- **Tasks directory:** _features/root-pre-commit-and-install/tasks/
- **Task count:** 4.
- **Execution order:** 01-wrapper-script.md, 02-root-install-sh.md, 03-root-pre-commit-config.md, 04-documentation-updates.md.
- **Task Completion Status:** Task 01-wrapper-script completed, tests passing. Task 02-root-install-sh completed, tests passing.
- Task plan created: 03-root-pre-commit-config at plans/tasks/03-root-pre-commit-config.md
- Task plan created: 04-documentation-updates at plans/tasks/04-documentation-updates.md
- Task plan created: 02-root-install-sh at plans/tasks/02-root-install-sh.md
- Task plan created: 01-wrapper-script at plans/tasks/01-wrapper-script.md
