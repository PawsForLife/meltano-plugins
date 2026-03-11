# Architecture — root-pre-commit-and-install

## System Design

Two new entry points at repository root, plus one shared script, all using the same discovery mechanism.

```
Repository root
├── install.sh                    # New: bootstrap all plugins
├── .pre-commit-config.yaml       # New: one local hook → wrapper script
└── scripts/
    ├── list_packages.py          # Existing: discovery (unchanged)
    └── run_plugin_checks.sh      # New: per-plugin ruff/mypy [pytest]
```

- **install.sh**: Calls `list_packages.py`, iterates paths, runs `(cd "$dir" && ./install.sh)`; exits non-zero on first failure. Then ensures pre-commit is installed (if not present) and runs `pre-commit install` from repo root.
- **.pre-commit-config.yaml**: Single `repo: local` hook, `language: system`, `entry` pointing at `scripts/run_plugin_checks.sh` (or equivalent path). Uses `pass_filenames: false`; `files` regex (e.g. `^taps/|^loaders/`) or `always_run: true` so hook runs when relevant files change or on every commit.
- **run_plugin_checks.sh**: Runs `list_packages.py .` to get plugin paths; for each path, `cd` to path, verify `.venv` exists, run `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`, `.venv/bin/mypy <package>`, optionally `.venv/bin/pytest`; exit non-zero if any step fails. Package name derived from directory name (e.g. `restful-api-tap` → `restful_api_tap`, `target-gcs` → `gcs_target`) with optional fallback map.

## Component Responsibilities

| Component | Responsibility |
|-----------|-----------------|
| **install.sh** | Discover plugins via list_packages.py; for each, run that plugin's install.sh from its directory; stop on first failure. Then install pre-commit if missing and run `pre-commit install` at repo root. |
| **.pre-commit-config.yaml** | Define one local hook that runs the wrapper script; no inline discovery or tool invocation. |
| **run_plugin_checks.sh** | Discovery via list_packages.py; per-plugin: cd, check .venv, run ruff check, ruff format --check, mypy \<package\>, optionally pytest; report failures and exit non-zero if any plugin fails. |
| **list_packages.py** | Unchanged: discover dirs with pyproject.toml, output one path per line (or JSON with --json). Root scripts use line output. |

## Data Flow

1. **Root install**: User runs `./install.sh` → script resolves repo root → runs `python scripts/list_packages.py <root>` → for each path, `(cd "$root/$path" && ./install.sh)` (stop on first failure) → then ensure pre-commit is installed (if not present) and run `pre-commit install` at root.
2. **Pre-commit**: Git triggers hook → pre-commit runs `scripts/run_plugin_checks.sh` (from repo root) → script runs `python scripts/list_packages.py .` → for each path, cd to path, run venv binaries → first failure sets script exit non-zero; pre-commit reports failure.

No shared state between plugins; each runs in isolation. Discovery is read-only (filesystem).

## Design Principles

- **Single source of truth for discovery**: `list_packages.py` only. Root install and pre-commit both use it; CI already uses it for matrix. New plugins are picked up automatically.
- **Per-plugin isolation**: Each plugin's tools run in that plugin's directory with that plugin's venv; no cross-plugin dependency.
- **Fail fast**: Root install stops on first failing plugin; wrapper script can stop on first failing plugin or first failing command within a plugin (recommend: stop on first failure for clarity).
- **No new languages**: Bash and existing Python; pre-commit already in use (e.g. target-gcs has .pre-commit-config.yaml).

## References

- Discovery and plugin layout: `docs/AI_CONTEXT/AI_CONTEXT_REPOSITORY.md`, `scripts/list_packages.py`.
- Pre-commit local hooks: `language: system`, `repo: local`, entry = path to script; see selected-solution and possible-solutions in planning.
