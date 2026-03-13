# Documentation — split-path-filename

## Documentation to Update

### README.md (`loaders/target-gcs/README.md`)

- **Remove:** `key_naming_convention` from config table.
- **Update:** Hive partitioning section — describe fixed path format `{stream}/{hive_path}/{timestamp}.jsonl`; no config override.
- **Remove:** References to `chunk_index` and `date_format` for key building (keep `date_format` only if still used for SimplePath `{date}`).
- **Add/Update:** Key format table matching feature spec (SimplePath, DatedPath, PartitionedPath).

---

### meltano.yml (`loaders/target-gcs/meltano.yml`)

- **Remove:** `key_naming_convention` from settings and config example.

---

### AI Context (`docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`)

- **Config schema:** Remove `key_naming_convention`; document retained options.
- **Key tokens:** Update to reflect fixed format — `{stream}`, `{date}`, `{hive_path}`, `{timestamp}`; no `{chunk_index}`.
- **Path pattern descriptions:** Update SimplePath, DatedPath, PartitionedPath to reference constants and `filename_for_current_file` / `full_key`.
- **GCSSink:** Remove key_naming_convention from constructor/config flow.

---

### AI Context Quick Reference (`docs/AI_CONTEXT/AI_CONTEXT_QUICK_REFERENCE.md`)

- **Core Interfaces:** Update target-gcs config line — remove `key_naming_convention`.

---

### AI Context Repository (`docs/AI_CONTEXT/AI_CONTEXT_REPOSITORY.md`)

- **target-gcs config:** Remove `key_naming_convention` from component responsibilities table.

---

## Code Documentation

### Docstrings (Google style)

- `filename_for_current_file()`: "Returns filename for current chunk: {timestamp}.jsonl. Uses injected time_fn or time.time."
- `full_key(path, filename)`: "Joins path and filename, applies key_prefix, normalizes slashes. Returns final GCS object key."
- `path_for_record(record)` (PartitionedPath): "Returns path for record using hive_path(record) and PATH_PARTITIONED."

### Constants

- Add brief comments in `constants.py` for `PATH_SIMPLE`, `PATH_DATED`, `PATH_PARTITIONED`, `FILENAME_TEMPLATE`.

---

## Changelog

Per `.cursor/CONVENTIONS.md`:

- **Plugin changelog:** `loaders/target-gcs/CHANGELOG.md`
- **Entry:** Under `[Unreleased]` or next version: `### Removed` — `key_naming_convention` config option. `### Changed` — Key format now fixed via path and filename constants; chunking uses timestamp only.
