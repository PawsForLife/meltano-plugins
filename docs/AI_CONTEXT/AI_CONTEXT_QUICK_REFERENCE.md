# AI Context — Quick Reference

## Metadata

| Field | Value |
|-------|--------|
| Version | 1.2 |
| Last Updated | 2026-03-12 |
| Tags | quick-reference, meltano, singer, sdk, taps, targets, python |
| Cross-References | [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) (architecture, entry points, data flow), [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md) (tap, target, config file, state file, Catalog, streams), [AI_CONTEXT_PATTERNS.md](AI_CONTEXT_PATTERNS.md) (code patterns), [AI_CONTEXT_restful-api-tap.md](AI_CONTEXT_restful-api-tap.md), [AI_CONTEXT_target-gcs.md](AI_CONTEXT_target-gcs.md) |

---

## Project Summary

Monorepo of **Meltano/Singer SDK** plugins (extractors and loaders) maintained by PawsForLife. Two standalone packages:

- **restful-api-tap** — Singer **tap** (extractor): reads from REST API **sources**, emits Singer messages (SCHEMA, RECORD, STATE) to stdout; **streams** and schemas configurable or auto-discovered; multiple auth types.
- **target-gcs** — Singer **target** (loader): reads Singer JSONL from stdin, loads into GCS **destination**; configurable bucket and key naming.

Plugins are **custom** (not on Meltano Hub or PyPI). Install via Meltano by editing `meltano.yml`: set `pip_url` (plain `git+https://...` URL with `#subdirectory=taps/restful-api-tap` or `#subdirectory=loaders/target-gcs`) and `namespace`; **do not set** `variant`. Each plugin has its own `pyproject.toml` under `taps/restful-api-tap/` and `loaders/target-gcs/`.

---

## Environment & Versions

| Item | Value |
|------|--------|
| Language | Python |
| restful-api-tap | `requires-python = ">=3.12"` |
| target-gcs | `requires-python = ">=3.12,<4.0"` |
| Package manager | **uv** (venv, sync deps) |
| Linter / formatter | **Ruff** |
| Type checker | **MyPy** |
| Test runner | **pytest** |
| Config | Per-plugin `pyproject.toml` (no repo root `pyproject.toml`) |

Activate venv before commands: `source .venv/bin/activate` from the plugin directory. Use project dependency files; do not install ad hoc with `pip install ...`.

---

## Key Commands (Shell)

### Repo root

From the repository root:

| Action | Command |
|--------|---------|
| Bootstrap all plugins and pre-push hook | `./install.sh` (discovers plugins via `scripts/list_packages.py`, runs each plugin's `install.sh`, exits on first failure; installs pre-commit if missing, runs `pre-commit install --hook-type pre-push` only) |
| Run all plugin checks (ruff, mypy, pytest) per plugin | `./scripts/run_plugin_checks.sh` (uses each plugin's `.venv`; requires root `install.sh` run first) |
| Install git hook (pre-push only) | `pre-commit install --hook-type pre-push` (run after root install.sh). Checks run on **push** only, not on commit. |
| Run all hooks on all files | `pre-commit run --all-files` |

Per-plugin commands below are for working in a single plugin directory.

### restful-api-tap (`taps/restful-api-tap/`)

| Action | Command |
|--------|---------|
| Bootstrap (venv, deps, lint, typecheck, test) | `./install.sh` |
| Venv (Python 3.12) | `uv venv --python 3.12` |
| Install deps (+ dev) | `uv sync --extra dev` |
| Lint | `uv run ruff check .` |
| Format check | `uv run ruff format --check` |
| Type check | `uv run mypy restful_api_tap` |
| Tests | `uv run pytest` |

### target-gcs (`loaders/target-gcs/`)

| Action | Command |
|--------|---------|
| Bootstrap | `./install.sh` |
| Venv | `uv venv` |
| Install deps | `uv sync` |
| Lint | `uv run ruff check .` |
| Format check | `uv run ruff format --check` |
| Type check | `uv run mypy target_gcs` |
| Tests | `uv run pytest` |

**Quality gate:** Tests and linters must pass before merge; no failing tests except those explicitly marked as expected failures.

---

## Runtime Entry Points

Plugins run as Singer executables. After install (Meltano or `pip install -e .` in plugin dir), use the CLIs below.

| Plugin | CLI | Entry point (pyproject) |
|--------|-----|-------------------------|
| restful-api-tap | `restful-api-tap` | `restful_api_tap.tap:RestfulApiTap.cli` |
| target-gcs | `target-gcs` | `target_gcs.target:GCSTarget.cli` |

### Via Meltano

Add plugins in `meltano.yml` with `pip_url` and `namespace`; **omit** `variant` (custom plugins are not on the Hub).

- **pip_url:** Plain URL only: `git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=taps/restful-api-tap` (or `loaders/target-gcs`). Do **not** use `package @ git+https://...`.
- **namespace:** e.g. `restful_api_tap`, `target_gcs`.
- Then: `meltano install` and e.g. `meltano run restful-api-tap target-gcs`.

Meltano passes **config** (and optionally **state file** and **Catalog**) to the tap; pipes tap stdout into the target stdin. See [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md) for config file, state file, Catalog, and streams.

### Standalone (dev/testing)

From plugin directory with venv active:

```bash
# Tap: Discovery — output catalog to stdout (save to file or pipe)
restful-api-tap --config config.json --discover

# Tap: Sync — config required; optional state file and Catalog
restful-api-tap --config config.json

# Target: reads Singer JSONL from stdin; optional config
cat stream.jsonl | target-gcs --config config.json
```

- **Config file** — JSON with tap params (api_url, auth, streams) or target params (bucket_name, key_prefix). Required for tap; optional for target.
- **State file** — Optional JSON for incremental sync (bookmarks per stream); tap may emit STATE to update it.
- **Catalog** — Describes which **streams** to extract and replication metadata; from tap `--discover` or Meltano. See [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md).

---

## Core Interfaces (Quick View)

- **restful-api-tap:** Subclasses `singer_sdk.Tap`; stream logic in `DynamicStream`; auth via `get_authenticator`; uses `singer_sdk.typing` for schema.
- **target-gcs:** Subclasses `singer_sdk.target_base.Target`; `GCSSink` (RecordSink) writes to GCS; config: `bucket_name`, `key_prefix`, `key_naming_convention`.

Both follow the Singer spec (stdout/stdin JSONL, Discovery, sync). See [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) for data flow.

---

## Frequently Used Imports

**restful-api-tap**

```python
from singer_sdk import Tap
from singer_sdk import typing as th
from singer_sdk.authenticators import APIAuthenticatorBase
from restful_api_tap.tap import RestfulApiTap
from restful_api_tap.streams import DynamicStream
from restful_api_tap.auth import get_authenticator
```

**target-gcs**

```python
from singer_sdk import typing as th
from singer_sdk.target_base import Target
from singer_sdk.sinks import RecordSink
from target_gcs.target import GCSTarget
from target_gcs.sinks import GCSSink
```

---

## Quick Troubleshooting

| Symptom | Check / Action |
|--------|----------------|
| `restful-api-tap` / `target-gcs` not found | Install in active env: `uv sync` (or `meltano install`). Run from plugin root or ensure venv `bin` is on PATH. |
| Import errors `restful_api_tap` / `target_gcs` | Run from correct plugin dir; venv must have that package (`uv sync` there). |
| Ruff/mypy failures | Run `ruff check .`, `ruff format --check`, `mypy <package>` from plugin root; fix reported issues. |
| Tests fail | `uv run pytest` from plugin root; fix regressions. No failures (except explicit xfail) before merge. |
| **"Extractor/Loader 'X' is not known to Meltano"** | Do **not** set `variant` on custom plugins. Set `namespace` and use `pip_url` with `#subdirectory=...` so Meltano uses the project definition. |
| **"Failed to parse: `@`" / "Expected package name..."** | Do not use `package @ git+https://...` in `pip_url`. Use plain URL: `git+https://github.com/.../meltano-plugins.git#subdirectory=...`. |
| Meltano install fails | Confirm `pip_url` and `#subdirectory=`; no `variant`; network and Git ref. |
| GCS errors | Check credentials (`GOOGLE_APPLICATION_CREDENTIALS` or default) and bucket IAM. |
| Tap auth failures | Verify config: `api_url`, credentials, auth type; confirm API reachable. |

More detail: [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md).
