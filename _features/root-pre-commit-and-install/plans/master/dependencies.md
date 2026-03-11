# Dependencies — root-pre-commit-and-install

## External Dependencies

- **Bash**: Root `install.sh` and `scripts/run_plugin_checks.sh` require Bash (shebang `#!/usr/bin/env bash`). Standard POSIX-style commands; avoid bash-only features if zsh compatibility is desired, otherwise bash is sufficient.
- **Python**: Used to run `scripts/list_packages.py`. No new Python dependencies; script is part of repo. Interpreter: `python` or `python3` (script invokes `python scripts/list_packages.py`; ensure one is available on PATH).
- **pre-commit**: Optional for end users; required only when using git hooks. Install via `pip install pre-commit` (or project-preferred method). No new pre-commit hooks from external repos; only `repo: local` with `language: system`.

## Internal Dependencies

- **scripts/list_packages.py**: Must exist and be runnable from repo root; accepts root path as first argument, outputs one relative path per line. Used by both root install.sh and run_plugin_checks.sh. No code changes required.
- **Per-plugin install.sh**: Each discovered directory must have an executable `install.sh`; root install.sh runs it from that directory. Existing plugins (e.g. taps/restful-api-tap, loaders/target-gcs) already provide this.
- **Per-plugin .venv**: Wrapper script expects each plugin directory to have `.venv` with `ruff`, `mypy` (and optionally `pytest`) in `.venv/bin`. Created by each plugin’s install.sh; users must run root `./install.sh` (or each plugin’s install.sh) before pre-commit hooks.

## System Requirements

- OS: Any supported by Bash and Python (e.g. Linux, macOS). Path and script resolution use standard shell and `list_packages.py` path handling.
- Repo layout: Repository root must contain `scripts/list_packages.py` and (after implementation) `install.sh`, `.pre-commit-config.yaml`, and `scripts/run_plugin_checks.sh`. Plugin directories must be discoverable under root (e.g. taps/, loaders/) with `pyproject.toml` and `install.sh`.

## Environment Setup

- Contributors: Clone repo, from repo root run `./install.sh` to create all plugin venvs, run plugin tests/lint, install pre-commit if missing, and run `pre-commit install` to enable hooks. No new env vars required for basic use; optional env (e.g. `RUN_PYTEST=1`) for wrapper script can be documented if implemented.

## Configuration

- No new config files. Pre-commit config is `.pre-commit-config.yaml` at root. Mypy package name mapping is inside the wrapper script (inline or small map). No tap/target config file, state file, or Catalog involved (see docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md for those terms in plugin context).
