# AI Context — Quick Reference

## Metadata

| Field | Value |
|-------|--------|
| Version | 1.0 |
| Last Updated | 2025-03-11 |
| Tags | quick-reference, meltano, singer, sdk, taps, targets, python |
| Cross-References | [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) (architecture, entry points, data flow), [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md) (tap, target, config file, state file, Catalog, streams), [AI_CONTEXT_PATTERNS.md](AI_CONTEXT_PATTERNS.md) (code patterns), [AI_CONTEXT_restful-api-tap.md](AI_CONTEXT_restful-api-tap.md), [AI_CONTEXT_target-gcs.md](AI_CONTEXT_target-gcs.md) |

---

## Project Summary

This repository is a **Meltano/Singer SDK monorepo** of two plugins maintained by PawsForLife (forks of upstream projects):

- **restful-api-tap** — Singer tap (extractor) for REST APIs; auto-discovered **streams** and schemas; supports Basic, API Key, Bearer, OAuth, and AWS auth.
- **target-gcs** — Singer target (loader) for GCS (destination); writes JSONL to a configurable bucket with configurable key naming.

Plugins are **custom** (not published to the Meltano Hub or PyPI). They are installed via Meltano by adding them in `meltano.yml` with `pip_url` (Git URL + `#subdirectory=` for each package) and optionally `variant: petcircle`. Each plugin is a standalone Python package with its own `pyproject.toml` under `taps/restful-api-tap/` and `loaders/target-gcs/`.

---

## Environment & Versions

| Item | Value |
|------|--------|
| Language | Python |
| restful-api-tap | `requires-python = ">=3.12"`; tooling targets `py312` |
| target-gcs | `requires-python = ">=3.8,<4.0"`; tooling targets `py38` / mypy `3.10` |
| Package manager | **uv** (create venv, sync deps) |
| Linter / formatter | **Ruff** (check + format) |
| Type checker | **MyPy** |
| Test runner | **pytest** |
| Config | Per-plugin `pyproject.toml` (no root-level `pyproject.toml`) |

Activate the venv before running commands: `source .venv/bin/activate` (from the plugin directory). Use the project’s dependency file; do not install ad hoc with `pip install ...`.

---

## Key Commands (Shell)

Commands are run **from each plugin’s package root** (`taps/restful-api-tap/` or `loaders/target-gcs/`). There is no repo-wide `install.sh`.

### restful-api-tap (`taps/restful-api-tap/`)

| Action | Command |
|--------|---------|
| Full bootstrap (venv, deps, lint, typecheck, test) | `./install.sh` |
| Create venv (Python 3.12) | `uv venv --python 3.12` |
| Install deps (incl. dev) | `uv sync --extra dev` |
| Lint | `uv run ruff check .` |
| Format check | `uv run ruff format --check` |
| Type check | `uv run mypy restful_api_tap` |
| Tests | `uv run pytest` |
| Optional (full env matrix) | `tox` (if desired) |

### target-gcs (`loaders/target-gcs/`)

| Action | Command |
|--------|---------|
| Full bootstrap (venv, deps, lint, typecheck, test) | `./install.sh` |
| Create venv | `uv venv` |
| Install deps (incl. dev) | `uv sync` |
| Lint | `uv run ruff check .` |
| Format check | `uv run ruff format --check` |
| Type check | `uv run mypy gcs_target` |
| Tests | `uv run pytest` |

### Quality gate

Before considering work complete: run the plugin’s test suite and linters; all tests must pass except those explicitly marked as expected failures.

---

## Runtime Entry Points

Plugins are executed as Singer executables. After installation (via Meltano or `pip install -e .` from the plugin dir), the following entry points are available.

| Plugin | CLI command | Entry point (pyproject) |
|--------|-------------|-------------------------|
| restful-api-tap | `restful-api-tap` | `restful_api_tap.tap:RestfulApiTap.cli` |
| target-gcs | `target-gcs` | `gcs_target.target:GCSTarget.cli` |

### Running via Meltano

These plugins are not on the Meltano Hub; add them in `meltano.yml` with `pip_url` and `#subdirectory=` (see [README](../../README.md) or [docs/monorepo](../monorepo/README.md)). Use `variant: petcircle` in examples from this repo.

1. Add the plugin in `meltano.yml` with `pip_url` (e.g. `restful-api-tap @ git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=taps/restful-api-tap`) and `variant: petcircle`.
2. Run `meltano install`, then e.g. `meltano run restful-api-tap target-gcs`.

### Running standalone (for dev/tests)

From the plugin directory with venv active:

```bash
# Tap: config file (required); optional state file and Catalog
restful-api-tap --config config.json

# Target: reads Singer JSONL from stdin; optional config file
cat stream.jsonl | target-gcs --config config.json
```

- **Config file**: JSON with credentials and parameters (tap: `api_url`, auth, streams; target: `bucket_name`, `key_prefix`). See [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md) for state file and Catalog.

---

## Core Interfaces (Quick View)

- **restful-api-tap**: Subclasses `singer_sdk.Tap`; stream logic in `DynamicStream`; auth via `get_authenticator` and `ConfigurableOAuthAuthenticator`; uses `singer_sdk.typing` for schema and properties.
- **target-gcs**: Subclasses `singer_sdk.target_base.Target`; uses `GCSSink` (subclass of `singer_sdk.sinks.RecordSink`) for writing to GCS; config: `bucket_name`, `key_prefix`, `key_naming_convention`.

Both follow the Singer spec (stdout/stdin JSONL, Discovery, sync; **config file**, **state file**, **Catalog**). See [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) for data flow and component roles.

---

## Frequently Used Imports

**restful-api-tap**

```python
from singer_sdk import Tap
from singer_sdk import typing as th
from singer_sdk.authenticators import APIAuthenticatorBase
from singer_sdk.helpers.jsonpath import extract_jsonpath
from restful_api_tap.tap import RestfulApiTap
from restful_api_tap.streams import DynamicStream
from restful_api_tap.auth import get_authenticator
```

**target-gcs**

```python
from singer_sdk import typing as th
from singer_sdk.target_base import Target
from singer_sdk.sinks import RecordSink
from gcs_target.target import GCSTarget
from gcs_target.sinks import GCSSink
```

---

## Quick Troubleshooting

| Symptom | Check / Action |
|--------|-----------------|
| Command not found (`restful-api-tap` / `target-gcs`) | Ensure the plugin is installed in the active env: `uv sync` (or `meltano install`). Run from plugin root or ensure PATH includes the venv’s `bin`. |
| Import errors for `restful_api_tap` / `gcs_target` | Run from the correct plugin directory; venv must have that package installed (editable: `uv sync` in that plugin). |
| Ruff or mypy failures | Run `ruff check .`, `ruff format --check`, and `mypy <package_name>` from the plugin root; fix reported files. |
| Tests fail | Run `uv run pytest` from the plugin root; fix regressions. No failing tests (except explicitly xfail) before merge. |
| Meltano cannot install plugin | Confirm `pip_url` uses `#subdirectory=taps/restful-api-tap` or `#subdirectory=loaders/target-gcs`; use `variant: petcircle` if following this repo's examples. Check network and Git ref. |
| GCS permission errors | Verify credentials (e.g. `GOOGLE_APPLICATION_CREDENTIALS` or default credentials) and bucket IAM. |
| Tap auth failures | Verify config (e.g. `api_url`, credentials, auth type) and that the API is reachable. |

For deeper architecture and component boundaries, see [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md).
