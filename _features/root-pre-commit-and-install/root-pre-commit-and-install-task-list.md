# Task list: root-pre-commit-and-install

## Execution order

1. [01-wrapper-script.md](tasks/01-wrapper-script.md) — Wrapper script `scripts/run_plugin_checks.sh`
2. [02-root-install-sh.md](tasks/02-root-install-sh.md) — Root `install.sh`
3. [03-root-pre-commit-config.md](tasks/03-root-pre-commit-config.md) — Root `.pre-commit-config.yaml`
4. [04-documentation-updates.md](tasks/04-documentation-updates.md) — Documentation updates

## Dependencies

- **01**: No feature-task dependencies; requires `scripts/list_packages.py`.
- **02**: No feature-task dependencies; requires `scripts/list_packages.py`.
- **03**: Depends on 01 (wrapper script must exist).
- **04**: Depends on 01–03 (documentation describes implemented behaviour).

## Interface requirements

- Root `install.sh`: no args; exit 0 when all plugin installs and pre-commit install succeed; non-zero on first failure.
- Wrapper script: run from repo root; exit 0 when all plugin checks pass; non-zero if .venv missing or any check fails.
- Root `.pre-commit-config.yaml`: one local hook, `language: system`, entry = wrapper script path.
