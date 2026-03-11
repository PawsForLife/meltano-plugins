# Master Plan — Dependencies: Stream-level `is_sorted` config

**Feature:** restful-api-tap is_sorted stream config

---

## External Dependencies

- **No new packages.** The Meltano Singer SDK already supports the stream attribute `is_sorted` and resumable incremental state; no new PyPI or system dependencies.
- **Existing:** restful-api-tap continues to use `singer-sdk`, `requests`, `genson`, and other deps as in `taps/restful-api-tap/pyproject.toml`. No version changes required for this feature.

---

## Internal Dependencies

- **tap.py** → **streams.py:** `discover_streams()` instantiates `DynamicStream`; the new `is_sorted` argument is passed from tap to stream. No other modules depend on `is_sorted`.
- **meltano.yml:** Plugin definition only; consumed by Meltano and by developers. No runtime import of meltano.yml by the tap.

---

## System and Environment

- **Python:** Unchanged (e.g. `requires-python = ">=3.12"` for restful-api-tap).
- **Config file:** Existing tap config file (or Meltano-injected config). New key `is_sorted` is optional and stream-level; no new env vars or CLI flags.
- **State file / Catalog:** No change to state file or Catalog shape; the SDK uses existing bookmark and state handling driven by `stream.is_sorted`.

---

## Configuration (Glossary)

Per [GLOSSARY_MELTANO_SINGER.md](../../../docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md):

- **Config file:** JSON (or Meltano-injected) supplying tap parameters. `is_sorted` is a stream-level key under `config.streams[]`.
- **State file:** Optional; holds bookmarks per stream. No schema change; SDK continues to manage resumable vs non-resumable state based on `is_sorted`.
- **Catalog:** Describes streams and replication metadata; produced by discovery or supplied by Meltano. No change to Catalog structure; `is_sorted` is not stored in the Catalog, only on the stream instance at runtime.

---

## Setup for Development and CI

- Use existing restful-api-tap setup: `cd taps/restful-api-tap && ./install.sh` (or `uv venv`, `uv sync --extra dev`, then `uv run pytest`). No new environment variables or secrets for this feature.
