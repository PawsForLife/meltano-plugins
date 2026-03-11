# Background

Plugins (taps, loaders) each have their own `install.sh` and use ruff, mypy, and pytest. There is no root-level automation to run these consistently before push or to bootstrap all plugins. A root pre-commit config and root `install.sh` will standardise formatting/lint/type-check and test runs across plugins and catch issues before deployment.

# This Task

- Add a root `.pre-commit-config.yaml` that runs mypy and ruff (format + check) for each plugin, using each plugin folder's virtual environment.
- Add a root `install.sh` that discovers and runs each plugin's `install.sh` (e.g. by globbing plugin-type folders such as `taps/*/`, `loaders/*/`).
- Ensure pre-commit hook installation is documented and that hooks invoke ruff, mypy, and pytest per plugin in that plugin's venv.

# Testing Needed

- No new application tests; validation is that root `install.sh` runs and all plugin installs/tests pass, and that `pre-commit run --all-files` succeeds.
