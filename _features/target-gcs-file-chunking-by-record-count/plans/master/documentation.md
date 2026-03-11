# Implementation Plan — Documentation: File Chunking by Record Count

**Feature:** target-gcs-file-chunking-by-record-count

---

## Documentation to Create or Update

### 1. README.md (`loaders/target-gcs/README.md`)

- **New setting:** Document `max_records_per_file` (optional integer). Explain: when set and greater than 0, the target rotates to a new GCS object after that many records per stream; when 0 or omitted, behaviour is one file per stream per run (unchanged).
- **Key tokens:** Document that when chunking is enabled, the key naming convention may use `{chunk_index}` (0-based index of the chunk). Describe that `{timestamp}` is refreshed at the start of each new chunk so each chunk gets a distinct key. Recommend including `{chunk_index}` in the convention to avoid collisions when multiple chunks are created in the same second.
- **Behaviour:** Short description: with chunking on, multiple files per stream are written; each file has at most `max_records_per_file` records; the last file may have fewer.

### 2. Inline code (sinks.py)

- **Docstring for GCSSink:** Extend class docstring to mention that when `max_records_per_file` is set, the sink rotates to a new file after that many records and uses current timestamp and chunk index in the key.
- **Rotation logic:** Brief comment at the rotation block (e.g. “Rotate to new chunk: close handle, clear key cache, increment chunk index, reset record count.”).
- **New instance attributes:** One-line comment for `_records_written_in_current_file` and `_chunk_index` (e.g. “Records written to current file; reset on rotation.” and “0-based chunk index; incremented on rotation.”).

### 3. Sample config (`loaders/target-gcs/sample.config.json`)

- Optionally add `"max_records_per_file": 1000` (or omit to show default “no chunking”). If added, add a short comment in README that the sample can include this key for chunking.

### 4. AI context (optional)

- If the project maintains `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`, add a note under config or key naming that `max_records_per_file` and `{chunk_index}` are supported when chunking is enabled.

---

## Code Documentation Requirements

- All new or modified public behaviour (config property, key tokens, rotation) must be reflected in README and in docstrings/comments as above. Use Google-style docstrings where new functions or significant behaviour are added.
- No separate design doc or ADR unless the project requires it; the master plan and README suffice.

---

## User-Facing vs Developer-Facing

- **User-facing:** README and sample config; Meltano setting description if present. Focus on what to set and what behaviour to expect.
- **Developer-facing:** Inline comments and class/method docstrings in `sinks.py` and `target.py`; this plan in `_features/.../plans/master/`.
