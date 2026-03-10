# Quick Reference — restful-api-tap

**Metadata**

| Field | Value |
|-------|--------|
| Version | 1.0 |
| Last Updated | 2025-03-10 |
| Tags | quick-reference, tap, singer, meltano-sdk, rest-api |
| Cross-References | AI_CONTEXT_REPOSITORY.md (architecture), AI_CONTEXT_PATTERNS.md (patterns) |

---

## Project Summary

`restful-api-tap` is a Singer tap for generic REST APIs built with the Meltano SDK. It auto-discovers stream schemas from API responses and supports multiple auth methods (Basic, API Key, Bearer, OAuth, AWS). Main components: **tap** (CLI/entry), **streams** (DynamicStream), **client** (RestApiStream), **auth**, **pagination**, **utils**.

---

## Environment & Versions

- **Runtime:** Python 3.12+
- **Package manager:** `uv` (venv + sync)
- **Config:** `pyproject.toml` — scripts, deps, ruff, mypy, pytest
- **Venv:** `.venv` (create with `uv venv --python 3.12`; activate before commands)

---

## Key Commands (Shell)

| Action | Command |
|--------|---------|
| Full install (venv + deps + tests) | `./install.sh` |
| Activate venv | `source .venv/bin/activate` |
| Install deps (with dev) | `uv sync --extra dev` |
| Run tests | `uv run pytest` |
| Lint + typecheck + tests | `uv run tox -e py` |
| Tap version | `uv run restful-api-tap --version` |
| Tap help | `uv run restful-api-tap --help` |
| About (settings/capabilities) | `uv run restful-api-tap --about` |
| Discover (write catalog) | `uv run restful-api-tap --config CONFIG --discover > ./catalog.json` |
| Run tap (config file + catalog) | `uv run restful-api-tap --config CONFIG --catalog CATALOG` |

Quality gate before merge: `uv run tox -e py` must pass (pytest, ruff, mypy).

---

## Runtime Entry Points

- **CLI:** `restful-api-tap` → `restful_api_tap.tap:RestfulApiTap.cli` (Singer tap entry).
- **Meltano:** executable `restful-api-tap`; e.g. `meltano invoke restful-api-tap --version`, `meltano elt restful-api-tap target-jsonl`.

---

## Core Interfaces (Quick View)

- **Tap:** `RestfulApiTap` in `restful_api_tap.tap` — Singer tap; streams built from config file. Config includes optional `flatten_records` (default false); when true, records and schema are flattened.
- **Streams:** `DynamicStream` in `restful_api_tap.streams` — per-stream sync; uses `RestApiStream`, pagination, auth.
- **Client:** `RestApiStream` in `restful_api_tap.client` — HTTP requests and response handling.
- **Auth:** `get_authenticator` in `restful_api_tap.auth` — returns auth implementation from config (Basic, API Key, Bearer, OAuth, AWS).

---

## Frequently Used Imports

```python
from restful_api_tap.tap import RestfulApiTap

# Streams and client
from restful_api_tap.streams import DynamicStream
from restful_api_tap.client import RestApiStream

# Auth and utilities
from restful_api_tap.auth import get_authenticator
from restful_api_tap.utils import flatten_json, get_start_date
```

---

## Quick Troubleshooting

| Symptom | Check / Action |
|--------|-----------------|
| Command not found | Ensure venv is active: `source .venv/bin/activate`; use `uv run restful-api-tap` if needed. |
| Import errors | Run `uv sync --extra dev` from project root. |
| Tests fail | Run `uv run pytest`; fix regressions before considering task complete (see project TDD/regression rules). |
| Lint/type errors | Run `uv run tox -e py`; fix ruff/mypy in changed files. |
| Tap fails on discover/sync | Validate config file (e.g. `api_url`, `streams` with `name`, `path`, `primary_keys`); run `restful-api-tap --about` for settings. |
| Auth failures | Confirm `auth_method` and required fields (e.g. `api_key`, `username`/`password`, `bearer_token`, OAuth params) in config. |
