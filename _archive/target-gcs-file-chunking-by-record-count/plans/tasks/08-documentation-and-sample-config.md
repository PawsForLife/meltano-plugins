# Task Plan: 08 — Documentation and Sample Config

**Feature:** target-gcs-file-chunking-by-record-count  
**Task:** 08-documentation-and-sample-config  
**Depends on:** 06-rotation-and-process-record (feature implementation complete). No code behaviour changes in this task.

---

## 1. Overview

This task completes the feature by documenting the new `max_records_per_file` setting and the `{chunk_index}` key token, adding inline comments and docstrings in the sink, and optionally updating the sample config and Meltano/AI context. All changes are documentation-only; behaviour is already implemented in prior tasks.

**Scope:** README, `sinks.py` docstrings/comments, `sample.config.json`, `meltano.yml`, and optionally `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`. Documentation must reflect the implemented behaviour; do not change code behaviour from documentation.

---

## 2. Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/README.md` | Modify: add config row for `max_records_per_file`; extend key token description to include `{chunk_index}` and refreshed `{timestamp}` when chunking is on; add short behaviour subsection for chunking. |
| `loaders/target-gcs/gcs_target/sinks.py` | Modify: extend `GCSSink` class docstring; add one-line comments for `_records_written_in_current_file` and `_chunk_index`; add brief comment at the rotation block. |
| `loaders/target-gcs/sample.config.json` | Modify (optional): add `"max_records_per_file": 1000`; if added, README will note that the sample can include this key for chunking. |
| `loaders/target-gcs/meltano.yml` | Modify: add a setting entry for `max_records_per_file` under `loaders[].settings` and in `config` if present; match existing style (name, env, description). |
| `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` | Modify (optional): under config or key naming, add that `max_records_per_file` and `{chunk_index}` are supported when chunking is enabled. |

### README.md — Specific changes

- **Accepted Config Options table:** Add one row:
  - Property: `max_records_per_file`
  - Env variable: e.g. `TARGET_GCS_MAX_RECORDS_PER_FILE` (align with existing env naming)
  - Type: integer
  - Required: no
  - Default: 0 (no chunking)
  - Description: When set and greater than 0, the target rotates to a new GCS object after that many records per stream; when 0 or omitted, one file per stream per run (unchanged).
- **key_naming_convention row:** Extend the description to state that when chunking is enabled, the token `{chunk_index}` (0-based) is available, and `{timestamp}` is refreshed at the start of each new chunk. Recommend including `{chunk_index}` to avoid collisions when multiple chunks are created in the same second.
- **Behaviour (chunking):** Add a short subsection (e.g. under Configuration or after the table) describing: with chunking on, multiple files per stream; each file has at most `max_records_per_file` records; the last file may have fewer.
- **Sample config:** If `sample.config.json` is updated to include `max_records_per_file`, add a sentence in README that the sample can include this key for chunking.

### sinks.py — Specific changes

- **GCSSink class docstring:** Add a sentence that when `max_records_per_file` is set, the sink rotates to a new file after that many records and uses current timestamp and chunk index in the key.
- **Instance attributes:** Where `_records_written_in_current_file` and `_chunk_index` are initialised (in `__init__` or equivalent), add one-line comments: e.g. “Records written to current file; reset on rotation.” and “0-based chunk index; incremented on rotation.”
- **Rotation block:** Add a brief comment above the rotation logic, e.g. “Rotate to new chunk: close handle, clear key cache, increment chunk index, reset record count.”

### sample.config.json

- Either add `"max_records_per_file": 1000` as an example, or leave omitted to show default no-chunking behaviour. If added, mention in README.

### meltano.yml

- Under `plugins.loaders[target-gcs].settings`, add an entry for `max_records_per_file` consistent with existing entries (e.g. `name`, optional `env`, optional description). If `config` block exists, add `max_records_per_file` with an example value or omit for default.

### AI_CONTEXT_target-gcs.md

- In the config or key-naming section, add that `max_records_per_file` (optional integer) and the `{chunk_index}` token are supported when chunking is enabled; keep the note concise.

---

## 3. Test Strategy

- **No new automated tests.** This task is documentation and sample config only.
- **Manual verification:** After edits, confirm README and sample config are consistent with `target.py` (config schema) and `sinks.py` (rotation and key behaviour).
- **Regression:** Run the full test suite once to ensure no regressions (e.g. no accidental code changes).

---

## 4. Implementation Order

1. **README.md**
   - Add `max_records_per_file` to the Accepted Config Options table (env var name consistent with existing pattern).
   - Update the `key_naming_convention` description to include `{chunk_index}` and refreshed `{timestamp}` when chunking is on; recommend `{chunk_index}` for uniqueness.
   - Add a short “File chunking (optional)” or similar subsection describing behaviour when chunking is enabled.
   - If sample config will include `max_records_per_file`, add a note that the sample can include this key.
2. **sinks.py**
   - Extend `GCSSink` class docstring with chunking behaviour.
   - Add one-line comments for `_records_written_in_current_file` and `_chunk_index` at their declaration/initialisation.
   - Add a single-line comment above the rotation block.
3. **sample.config.json**
   - Optionally add `"max_records_per_file": 1000`; if omitted, no README change for sample.
4. **meltano.yml**
   - Add `max_records_per_file` to `settings` (and to `config` if the project documents default config there).
5. **docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md** (optional)
   - Add a concise note under config/key naming for `max_records_per_file` and `{chunk_index}`.

---

## 5. Validation Steps

1. Read through README: config table and key tokens match `target.py` schema and `sinks.py` behaviour.
2. Confirm sample.config.json is valid JSON and, if present, `max_records_per_file` is an integer.
3. Confirm meltano.yml is valid and the new setting matches existing style.
4. Run the project test suite (e.g. `pytest` from `loaders/target-gcs` with venv active); all tests must pass.
5. Optionally run `target-gcs --about` and spot-check that the new setting appears in capabilities/config if exposed there.

---

## 6. Documentation Updates

| Document | Update |
|----------|--------|
| README.md | As in “Files to Create/Modify” and “Implementation Order” above. |
| sinks.py | Docstring and comments only; no behavioural change. |
| sample.config.json | Optional new key; no separate doc beyond README mention. |
| meltano.yml | New setting entry; no separate doc. |
| AI_CONTEXT_target-gcs.md | Optional short note on config/key naming. |

**Acceptance:** README and code comments reflect the implemented chunking behaviour; documentation is concise and consistent with the code. Code is not changed to match documentation.
