# Changelog

## [Unreleased]

## [1.7.1] - 2026-03-24

### Fixed

- **medallia-duplicate-pagination-token** — Optional `pagination_stop_on_duplicate_token` (default `false`): when `true`, JSONPath pagination ends cleanly if the API returns the same cursor as the previous request. The Singer SDK otherwise raises `RuntimeError: Loop detected in pagination`, which breaks Medallia/Stella-style `after` + last-record cursor flows.

- **source-search-first-page-only** — When `source_search_field` / `source_search_query` are set, those parameters apply only to the initial request (no pagination token). Later pages keep the API cursor instead of re-applying the run start bookmark, avoiding duplicated or mis-ordered rows during pagination.

## [1.7.0] - 2026-03-18

### Added

- **partition-fields-stream-config** — Stream-level `partition_fields` config option. When set (array of property names), the tap injects `x-partition-fields` into the schema emitted in SCHEMA messages so downstream loaders (e.g. target-gcs with `hive_partitioned: true`) can use Hive-style partitioning. Stream-level overrides top-level; each stream in a multi-stream config can have its own partition fields. See [docs/PARTITION_FIELDS_STREAM_CONFIG.md](../../docs/PARTITION_FIELDS_STREAM_CONFIG.md).

## [1.6.1] - 2026-03-12

### Added

- **readme-and-docs-structure** — Separate user and developer docs; developer guide in plugin docs. Details: [readme-and-docs-structure.md](../../_archive/readme-and-docs-structure/readme-and-docs-structure.md).
  - Add developer guide at `docs/DEVELOPMENT.md` (task 02).
  - README: remove inline Developer Resources; add link to docs/DEVELOPMENT.md (task 04).

### Changed

- Updated type hints to Python 3.12 style (built-in generics and pipe unions).

## [1.6.0] - 2026-03-12

### Changed

- Discovery: stream-level `is_sorted` now falls back to tap-level `is_sorted` when omitted on a stream, so tap-wide `is_sorted` is honored.

### Fixed

- `post_process`: when `flatten_records` is false and `store_raw_json_message` is true, the non-flatten return path now adds `_sdc_raw_json` to the row (raw record copy) so the advertised field is emitted.

## [1.5.0] - 2026-03-10

### Added

- **optional-flatten-config** — Details: [optional-flatten-config.md](_archive/optional-flatten-config/optional-flatten-config.md)
  - Config property `flatten_records` (boolean, default `false`) in tap and stream-level config schema
  - DynamicStream `flatten_records` parameter and post_process branch; sync tests for flatten and non-flatten paths
  - Parameter `flatten_records` on `get_schema()` and schema inference branch (flatten sample vs raw nested)
  - Discovery resolves `flatten_records` per stream and passes to `get_schema()` and `DynamicStream()`
  - Documentation and test alignment for default `flatten_records: false` (README, config.sample.json, AI_CONTEXT)
