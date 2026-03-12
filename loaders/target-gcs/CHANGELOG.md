# Changelog

## [Unreleased]

### Added

- **dateutils-partition-timestamps** — Details: [dateutils-partition-timestamps.md](../../_archive/dateutils-partition-timestamps/dateutils-partition-timestamps.md)
  - Add python-dateutil dependency (>=2.8.1) for partition path parsing.
  - Add TDD tests for dateutil-only partition date formats (slash, RFC-style, long month); marked xfail until Task 05.
  - Add TDD test that unparseable partition timestamp raises (no silent fallback); marked xfail until Task 05.
  - Add TDD test that unsupported timezone in partition timestamp surfaces visibility (warning or error); marked xfail until Task 05.

### Changed

- Updated type hints to Python 3.12 style (built-in generics and pipe unions).

### Breaking

- **Python 3.12 minimum** — Minimum supported Python is now 3.12. Upgrade your environment before installing.

## [2.0.0] - 2026-03-12

### Fixed

- **fix-target-gcs-real-client-in-tests** — Tests no longer perform real GCP actions: GCS client is injectable so CI runs without ADC. Details: [_archive/fix-target-gcs-real-client-in-tests/fix-target-gcs-real-client-in-tests.md](../../_archive/fix-target-gcs-real-client-in-tests/fix-target-gcs-real-client-in-tests.md)
  - GCSSink accepts optional `storage_client`; used in `gcs_write_handle` and partition-by-field path when provided.
  - GCSTarget holds `_storage_client` and overrides `get_sink()` to pass it when creating sinks.
  - test_core uses `GCSTargetWithMockStorage` in `get_target_test_class()` so standard target tests run without credentials.
  - test_sinks `build_sink()` accepts optional `storage_client` for write-path tests.

- **README:** Corrected `key_naming_convention` default in config table from `{timestamp}` to `{stream}_{timestamp}.jsonl` to match GCSSink behavior in `sinks.py`.

- **Chunk rotation:** Refresh cached file timestamp (`_current_timestamp`) in `_rotate_to_new_chunk()` so the next key is unique for the new chunk; avoids reusing or truncating the previous key when `max_records_per_file` triggers rotation.

- **Partition-by-field keys:** Cache extraction timestamp when opening a GCS write handle so keys are stable per handle instead of changing every second. `_build_key_for_record` now uses a cached `_current_timestamp` (set on first use after open, cleared in `_close_handle_and_clear_state`), avoiding new keys/handles per second.

### Changed

- **Tests:** Removed `test_partition_path_fallback_format` (relied on patching `datetime.fromisoformat`; no natural input triggers the strptime fallback; valid/invalid paths already covered by other tests).

- **Tests:** Split partition-path and key-generation tests from `test_sinks.py` into `test_partition_key_generation.py` so each file stays under the 500-line limit.

- **README:** Clarified "Naming with chunking": added comma before "so" in chunk-index sentence; rewrote timestamp explanation so collisions are defined by chunk start time within the same granularity window (e.g. 12:00:00.500 vs 12:00:00.999), not by processing duration.

- **Glossary alignment:** Plugin, package, and directory were renamed for Singer/Meltano glossary alignment: CLI/plugin `target-gcs`, Python package `gcs_target`, path `loaders/target-gcs/`. See the [repo root CHANGELOG](../../CHANGELOG.md) for user migration (update `meltano.yml` to use `target-gcs`, re-run `meltano install`).

- **Package/namespace rename:** Python package and namespace renamed from `gcs_target` to `target_gcs` (normalise-plugin-source-folders). See the [repo root CHANGELOG](../../CHANGELOG.md) for user migration (namespace `target_gcs`, re-run `meltano install`, `mypy target_gcs`).

### Breaking

- **Credentials**: Remove `credentials_file` from config. Authentication uses Application Default Credentials (ADC) only. To use a credentials file, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable; the target no longer accepts a credentials path in config.

## v1.1.0 (2023-03-01)
### Feature
* Make gcp service account credential file optional ([`6e9e36e`](https://github.com/Datateer/target-gcs/commit/6e9e36ec3a9fee4d2e16b994ecade8ddd8eb61c1))

## v1.0.3 (2022-05-27)
### Fix
* Bump version ([`494d3c9`](https://github.com/Datateer/target-gcs/commit/494d3c90c1c58191a9023d95ebeb61995441fa49))

## v1.0.2 (2022-05-26)
### Fix
* Typo ([`b70e738`](https://github.com/Datateer/target-gcs/commit/b70e73870e472516bdf12c2ee592506c0df7a721))

## v1.0.1 (2022-05-26)
### Fix
* Semantic release ([`172004b`](https://github.com/Datateer/target-gcs/commit/172004b412baf115f5a50bf0c391eaf2a16b1484))
