# Interfaces — root-pre-commit-and-install

## Public Interfaces

### 1. Root `install.sh`

- **Invocation**: From repo root: `./install.sh`. No arguments. Caller's working directory must be repository root (or script resolves root from its own path).
- **Input**: None (discovery uses repo root as root for `list_packages.py`).
- **Output**: Stdout/stderr from each plugin's `install.sh`, then pre-commit install if applicable. Exit code: 0 if all plugin installs and pre-commit install succeeded; non-zero on first plugin failure or if pre-commit install fails.
- **Contract**: Script is executable (`chmod +x`); depends on `python` (or `python3`) and `scripts/list_packages.py`; each discovered path must have an executable `install.sh`. After all plugin installs succeed, script installs pre-commit if not present (e.g. via pip) and runs `pre-commit install` at repo root.

### 2. Wrapper script (e.g. `scripts/run_plugin_checks.sh`)

- **Invocation**: From repo root: `./scripts/run_plugin_checks.sh` or via pre-commit (pre-commit runs from repo root). Optional: accept list of paths as arguments to override discovery (future-proof); if no args, run `list_packages.py` with repo root.
- **Input**: Working directory = repo root. Optional env (e.g. `RUN_PYTEST=1`) to include pytest (implementation choice).
- **Output**: Per-plugin progress to stdout/stderr; exit 0 if all plugins pass all checks; non-zero if any plugin fails any of ruff check, ruff format --check, mypy, or (if enabled) pytest.
- **Contract**: Script is executable; depends on `python`/`python3`, `scripts/list_packages.py`, and each plugin directory having a `.venv` with `ruff`, `mypy` (and optionally `pytest`) in `.venv/bin`. Package name for mypy is derived from directory name (see below) or fallback map.

### 3. Plugin discovery (`list_packages.py`) — consumed interface

- **Invocation**: `python scripts/list_packages.py [ROOT]`. ROOT defaults to current working directory; typically `.` when run from repo root.
- **Output**: One relative path per line (no `--json`). Paths are relative to ROOT; sorted lexicographically. Excludes dirs under `.git`, `.venv`, `_archive`, `node_modules`.
- **Contract**: Existing script; no changes required. Root scripts assume line-based output and that each line is a directory containing `pyproject.toml` and (for install.sh) `install.sh`.

### 4. Plugin `install.sh` — consumed interface

- **Invocation**: From plugin directory: `./install.sh`. No arguments.
- **Contract**: Must be executable; creates/uses `.venv`, installs deps, runs ruff, mypy, pytest (or equivalent). Exit code reflects success/failure. Root `install.sh` runs this from plugin dir via `(cd "$dir" && ./install.sh)`.

### 5. Root `.pre-commit-config.yaml`

- **Structure**: `repos:` with one entry: `repo: local`, hooks with `language: system`, `entry` pointing to wrapper script (e.g. `scripts/run_plugin_checks.sh`). Use `pass_filenames: false`. Optionally `files: '^taps/|^loaders/'` or `always_run: true`.
- **Contract**: pre-commit runs the entry from repo root; script must be executable and behave as in §2.

## Mypy package name derivation

- **Rule**: Map directory name to Python package name. Examples: `restful-api-tap` → `restful_api_tap` (replace `-` with `_`); `target-gcs` → `gcs_target` (convention for targets: `target-*` → `*_target` with `-` → `_`).
- **Interface**: Script implements a function or inline logic: `path_to_mypy_package(relative_path: str) -> str`. Fallback: small map for exceptions (e.g. `target-gcs` → `gcs_target`). New plugins follow convention so no map entry needed when pattern holds.

## Dependencies Between Interfaces

- Root `install.sh` depends on: list_packages.py (discovery), each plugin's install.sh (execution).
- Wrapper script depends on: list_packages.py (discovery), each plugin's .venv and directory layout (execution).
- Pre-commit config depends on: wrapper script (entry point). Pre-commit framework runs the script.
- No interface exposes internal call counts or implementation details; acceptance is behavioural (exit code, all plugins pass).
