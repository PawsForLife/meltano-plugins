# Task 02: Root `install.sh`

## Background

Contributors need one command at repo root to bootstrap all plugins (run each plugin's `install.sh`) and to install pre-commit and git hooks. Discovery reuses `scripts/list_packages.py` so new plugins are included automatically. This task depends only on the existence of `scripts/list_packages.py`; it does not depend on task 01 (wrapper script). The wrapper script is used by pre-commit (task 03), not by install.sh. Implementation order places root install.sh after the wrapper script in the plan.

## This Task

- **Create** `install.sh` at repository root.
- **Shebang**: `#!/usr/bin/env bash`.
- **Repo root**: `ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`.
- **Discovery**: Run `python "$ROOT/scripts/list_packages.py" "$ROOT"`; iterate each line as the relative plugin path.
- **Per plugin**: For each path, run `(cd "$ROOT/$path" && ./install.sh)`; if exit code is non-zero, exit immediately with that code (stop on first failure).
- **Pre-commit availability**: After all plugin installs succeed, check if pre-commit is available (e.g. `command -v pre-commit`); if not, install it (e.g. `pip install pre-commit` or project-preferred method so hooks run without activating a venv).
- **Install hooks**: From repo root, run `pre-commit install`. If that fails, exit non-zero.
- **Top-of-file comment**: State purpose: bootstrap all plugins by running each plugin's install.sh; discovery via list_packages.py; then install pre-commit if missing and run pre-commit install.
- **Make executable**: `chmod +x install.sh`.

## Testing Needed

- No new application unit tests. Validation is behavioural: from repo root, run `./install.sh` and expect exit 0 when all plugin installs and pre-commit install succeed; expect non-zero on first plugin install failure or if pre-commit install fails. Optional black-box script test: run `./install.sh` and assert exit code (e.g. 0 when all succeed). Do not assert invocation counts or internal behaviour.
