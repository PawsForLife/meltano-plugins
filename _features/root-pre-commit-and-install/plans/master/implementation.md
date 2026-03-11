# Implementation — root-pre-commit-and-install

## Order of Work

1. **Wrapper script** — Implement `scripts/run_plugin_checks.sh` (discovery, path→package, run ruff/mypy per plugin; optional pytest). Test manually from repo root.
2. **Root install.sh** — Implement root `install.sh` (discovery via list_packages.py, loop over paths, run each plugin's install.sh; stop on first failure).
3. **Root .pre-commit-config.yaml** — Add `.pre-commit-config.yaml` at repo root with one local hook invoking the wrapper script.
4. **Documentation** — Update README, docs/monorepo/README.md, docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md per documentation.md.

Models/interfaces: No new data models; interfaces are CLI contracts (see interfaces.md). Scripts are Bash; no new Python modules.

## Step 1: Wrapper script `scripts/run_plugin_checks.sh`

- **Create** `scripts/run_plugin_checks.sh`.
- Shebang: `#!/usr/bin/env bash`.
- Resolve repo root: from script location (e.g. `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`, `ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"` if script is in `scripts/`).
- Discovery: run `python "$ROOT/scripts/list_packages.py" "$ROOT"` (or `python scripts/list_packages.py .` when run from ROOT); read output line by line.
- For each line (plugin path): `cd "$ROOT/$path"` (or `cd "$path"` if list_packages outputs paths relative to CWD); if `! [ -d .venv ]` then fail or skip with clear message (recommend fail); run `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`, `.venv/bin/mypy <package>`. Optionally run `.venv/bin/pytest` (env var or default off for speed).
- Package name: from path (e.g. `taps/restful-api-tap` → last component `restful-api-tap` → `restful_api_tap`; `loaders/target-gcs` → `target-gcs` → `gcs_target`). Implement mapping: `restful-api-tap` → `restful_api_tap`, `target-gcs` → `gcs_target`; default rule: replace `-` with `_` for non-targets; for `target-*`, use `*_target` with `-`→`_`.
- Exit: on first failure (non-zero from any command), exit non-zero; else exit 0.
- Make executable: `chmod +x scripts/run_plugin_checks.sh`.

## Step 2: Root `install.sh`

- **Create** `install.sh` at repository root.
- Shebang: `#!/usr/bin/env bash`.
- Resolve repo root: `ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`.
- Discovery: `python "$ROOT/scripts/list_packages.py" "$ROOT"` (or `python scripts/list_packages.py "$ROOT"`); iterate lines.
- For each path: run `(cd "$ROOT/$path" && ./install.sh)`; if exit non-zero, exit with that code (stop on first failure).
- **Install pre-commit if not present**: e.g. `command -v pre-commit` or `pip show pre-commit`; if missing, install via `pip install pre-commit` (or `uv pip install pre-commit` if using uv at root). Use a single mechanism; prefer system/user pip so hooks run without activating a venv.
- **After all plugin installs succeed**: run `pre-commit install` from repo root so git hooks are installed. If pre-commit install fails, exit non-zero.
- Make executable: `chmod +x install.sh`.

## Step 3: Root `.pre-commit-config.yaml`

- **Create** `.pre-commit-config.yaml` at repository root.
- Content: minimal `repos:` list with one entry:
  - `repo: local`
  - `hooks`: one hook: `id` (e.g. `plugin-checks`), `name` (e.g. `Run plugin checks (ruff, mypy)`), `entry: scripts/run_plugin_checks.sh` (or `bash scripts/run_plugin_checks.sh` if needed), `language: system`, `pass_filenames: false`, and either `files: '^taps/|^loaders/'` or `always_run: true`.
- Do not remove `loaders/target-gcs/.pre-commit-config.yaml`; it remains optional for single-plugin use.

## Step 4: Documentation

- **README.md**: Add short "Development" or "Contributing" section: run `./install.sh` at repo root to bootstrap all plugins; install pre-commit (`pip install pre-commit` or equivalent), run `pre-commit install`; optionally `pre-commit run --all-files` to check everything.
- **docs/monorepo/README.md**: State that root `install.sh` runs each plugin's `install.sh` and that root pre-commit runs ruff, mypy (and optionally pytest) per plugin using each plugin's venv; discovery via `scripts/list_packages.py`.
- **docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md**: Add root-level commands (root `./install.sh`, `pre-commit install`, `pre-commit run --all-files`); keep per-plugin command tables for single-plugin workflows.

## Files to Create

| File | Action |
|------|--------|
| `install.sh` | Create (root) |
| `.pre-commit-config.yaml` | Create (root) |
| `scripts/run_plugin_checks.sh` | Create |

## Files to Modify

| File | Change |
|------|--------|
| `README.md` | Add Development/Contributing subsection |
| `docs/monorepo/README.md` | Add root install + pre-commit behaviour |
| `docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md` | Add root commands; note repo-wide install |

## Dependency Injection / Non-determinism

- No non-deterministic systems in scope; discovery is filesystem, commands are fixed. If script reads env (e.g. `RUN_PYTEST`), that is optional behaviour toggle, not injected dependency.
- Paths resolved from script location and repo root; no time or external API.

## Implementation Notes

- **list_packages.py**: Called with root as first argument; script passes `"$ROOT"` or `.` when CWD is root. Script expects line output (no `--json`).
- **Mypy mapping**: Keep mapping in wrapper script (associative array in Bash or case statement) for `restful-api-tap` → `restful_api_tap`, `target-gcs` → `gcs_target`; default: replace `-` with `_` for last path component, with special case for `target-*` → `*_target`.
- **Pytest**: Include in hook or separate; if same hook, script runs pytest per plugin after mypy; if too slow, document pre-push or separate hook (implementation choice; can start with same hook and move later).
