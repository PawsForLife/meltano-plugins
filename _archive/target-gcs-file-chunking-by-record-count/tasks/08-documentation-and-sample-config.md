# Background

Users and operators need to know about `max_records_per_file` and the `{chunk_index}` key token. Inline comments and docstrings help maintainability. The plan specifies README, sample config, optional meltano.yml, and code comments.

**Depends on:** 06-rotation-and-process-record (feature is implemented). No code behaviour changes.

# This Task

- **File:** `loaders/target-gcs/README.md`
  - Document `max_records_per_file` (optional integer): when set and > 0, the target rotates to a new GCS object after that many records per stream; when 0 or omitted, one file per stream per run (unchanged).
  - Document that when chunking is enabled, the key naming convention may use `{chunk_index}` (0-based). Describe that `{timestamp}` is refreshed at the start of each new chunk. Recommend including `{chunk_index}` to avoid collisions when multiple chunks are created in the same second.
  - Short behaviour description: with chunking on, multiple files per stream; each file has at most `max_records_per_file` records; the last file may have fewer.
- **File:** `loaders/target-gcs/gcs_target/sinks.py`
  - Extend `GCSSink` class docstring to mention that when `max_records_per_file` is set, the sink rotates to a new file after that many records and uses current timestamp and chunk index in the key.
  - Add a brief comment at the rotation block (e.g. "Rotate to new chunk: close handle, clear key cache, increment chunk index, reset record count.").
  - One-line comments for `_records_written_in_current_file` and `_chunk_index` in `__init__` (or where they are set).
- **File:** `loaders/target-gcs/sample.config.json`
  - Optionally add `"max_records_per_file": 1000` (or omit to show default no chunking). If added, mention in README that the sample can include this key for chunking.
- **File:** `loaders/target-gcs/meltano.yml`
  - If the project documents target-gcs loader settings here, add a setting for `max_records_per_file` so users can configure it via Meltano. Match existing setting style (name, env, description).
- **Optional:** If `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` exists, add a note under config or key naming that `max_records_per_file` and `{chunk_index}` are supported when chunking is enabled.
- **Acceptance criteria:** README and code reflect the implemented behaviour; documentation is concise and consistent with the code (do not update code from docs).

# Testing Needed

- No automated tests required for documentation. Manually verify README and sample config are consistent with `target.py` and `sinks.py`. Run the test suite once to ensure no regressions.
