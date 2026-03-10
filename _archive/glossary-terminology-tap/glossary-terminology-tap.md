# Archive: glossary-terminology-tap

Summary of the **glossary-terminology-tap** feature pipeline. Single source of truth for terminology: `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md`.

---

## The request

**Background:** The project adopted `docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md` as the source of truth for Meltano and Singer terminology. The **restful-api-tap** (Singer tap / Meltano extractor) had to use the glossary’s terms consistently in code, docstrings, tests, config samples, and in-package docs so that naming and comments align with the Singer Spec and Meltano Singer SDK.

**Scope:** Only the tap under `taps/restful-api-tap/`. Project-level docs (`docs/`, `docs/AI_CONTEXT/`) are covered by the separate feature **glossary-terminology-docs**.

**Goal:** Update the restful-api-tap package so that all code, docstrings, tests, config samples, and in-package documentation use the correct glossary terms. File or module renames were in scope only where necessary to fix terminology; the package name and executable name (`restful-api-tap`) were to remain.

**Key terms to align:** Tap, Stream, Source, Catalog, Discovery, config file, state file, message types (SCHEMA, RECORD, STATE), replication key, bookmark, key properties, primary keys (SDK), replication method (INCREMENTAL, FULL_TABLE).

**Testing needs:** Run the full tap test suite (`./install.sh` or `uv run pytest` in `taps/restful-api-tap/`). All tests must pass. No new tests required for terminology-only changes. Optional manual check: grep for anti-patterns (e.g. “loader”, “destination” in tap context) and confirm fixes.

---

## Planned approach

**Chosen solution:** Manual glossary-driven edits. Apply glossary terms consistently across the tap package via direct edits to source, tests, config descriptions, and in-package docs, using the project glossary as the single source of truth. No external library; optional one-off grep for anti-patterns to guide edits.

**Constraints:** No behavior changes; no CLI, config key, or Meltano plugin renames unless a key was explicitly wrong per spec. Use “config file” / “state file” in prose when referring to the files; variable names like `config` for the in-memory object remain. Use “key properties” (Singer/catalog) vs “primary keys” (SDK/config) consistently in prose.

**Architecture:** No system or data-flow changes. Terminology alignment only: docstrings, comments, test names, and in-package documentation under `taps/restful-api-tap/` were updated to match the glossary. Component boundaries and module responsibilities were unchanged.

**Task breakdown (10 tasks, ordered):**

| # | Task | Scope |
|---|------|--------|
| 01 | Update tap.py docstrings | `restful_api_tap/tap.py`: class/method docstrings, property descriptions; “rest-api tap” → “REST API tap”; glossary terms throughout. |
| 02 | Update streams.py docstrings | `restful_api_tap/streams.py`: stream (not sink), replication key, bookmark, key properties/primary keys; “singer context object” → stream context/stream state/bookmarks. |
| 03 | Update client.py docstrings | `restful_api_tap/client.py`: REST API stream, records, stream, end-of-stream; config file/source in prose. |
| 04 | Update auth.py docstrings | `restful_api_tap/auth.py`: “Tap Config”/“Stream Config” → “config file”/“stream-level config” where describing the file. |
| 05 | Update pagination.py docstrings | `restful_api_tap/pagination.py`: stream, RECORD, source in docstrings and comments. |
| 06 | Update utils.py docstrings | `restful_api_tap/utils.py`: stream state, bookmark, config file; “singer context object”/“start_date parameter” → glossary terms. |
| 07 | Update __init__.py docstrings | `restful_api_tap/__init__.py`: any user-facing docstrings/comments to glossary terms; skip if minimal. |
| 08 | Update tap tests terminology | `tests/*.py`: docstrings, test names, assertion messages; glossary terms; black-box behavior unchanged. |
| 09 | Update config and plugin terminology | `config.sample.json`, `meltano.yml`: terminology in descriptions/comments only; no key renames. |
| 10 | Update tap README and in-package docs | `README.md`, `taps/restful-api-tap/docs/*`: config file, state file, bookmarks, key properties, primary keys, SCHEMA/RECORD/STATE. |

Execution order: 01 first; 02–06 parallelizable after 01; 07 after 02–06; 08–09 after 01–07; 10 after 08–09. Existing test suite was the regression gate; no new tests required.

---

## What was implemented

All 10 tasks were completed (per pipeline scratchpad). Terminology was aligned across:

- **Source package:** `tap.py`, `streams.py`, `client.py`, `auth.py`, `pagination.py`, `utils.py`, `__init__.py` — docstrings and comments updated to use Tap, Stream, Source, Catalog, Discovery, config file, state file, SCHEMA/RECORD/STATE, replication key, bookmark, key properties, primary keys. “rest-api” was replaced with “REST API” where it improved clarity; “singer context object” was replaced with stream context/stream state/bookmarks.
- **Tests:** `test_tap.py`, `test_streams.py`, `test_core.py`, `test_utils.py`, `test_404_end_of_stream.py` — docstrings, test names, and presentational messages updated to glossary terms; test logic and black-box behavior unchanged.
- **Config and plugin:** `config.sample.json` (no key changes; prose only if present), `meltano.yml` — descriptions/comments updated to use config file, state file, and related terms where applicable.
- **In-package docs:** `README.md` and `taps/restful-api-tap/docs/` (e.g. AI_CONTEXT_*.md) — informal “config”/“state” replaced with “config file”/“state file”/“bookmarks”/“stream state” by context; key properties vs primary keys and SCHEMA/RECORD/STATE used consistently.

**Outcomes:** Tap discovery, sync, and config file/state file behaviour are unchanged from a user perspective. CLI name, package name, and config keys (e.g. `primary_keys`, `replication_key`) were preserved. The test suite was run after the changes and passed. No new modules or functionality were added.
