# Changelog

## [Unreleased]

### Removed

- **target-gcs-function-name-alignment:** Removed dead helper `get_partition_path_from_record` and its tests; sink uses only `get_partition_path_from_schema_and_record` (x-partition-fields). Dropped export from `target_gcs.helpers`. See [_archive/target-gcs-function-name-alignment](../../_archive/target-gcs-function-name-alignment/target-gcs-function-name-alignment.md).
- **Tests:** Removed two redundant tests: duplicate "valid hive schema constructs" in test_sinks (`test_sink_init_hive_partitioned_valid_x_partition_fields_succeeds`; kept `test_hive_partitioned_valid_schema_constructs_successfully`) and duplicate "fallback date in key when no x-partition-fields" in test_partition_key_generation (`test_hive_partitioned_true_without_x_partition_fields_key_contains_fallback_date`; coverage retained in test_sinks).

### Added

- **hive-partition-key-value-paths** — Partition path literal segments as Hive-standard `key=value` (e.g. `region=eu`).
  - Unit tests expect key=value literal segments in partition path (TDD red phase); implementation in task 02.
  - Emit literal segments as `field_name=value` (Hive standard) in `get_partition_path_from_schema_and_record`; docstring updated.
  - Integration and sink tests expect key=value literal segments in partition keys (e.g. dt=2024-03-11, created_at=2024_03_11, region=eu, r=x).
- **hive-partition-format-only** — Details: [hive-partition-format-only.md](../../_archive/hive-partition-format-only/hive-partition-format-only.md)
  - Unit tests for format-only partition path: no format + datetime still date segment; no format + parseable string → literal (xfail until implementation).
  - Integration test updated: no format + parseable string → key contains literal segment (xfail until implementation).
  - Remove string date inference in partition_path: only schema format (and native datetime/date) drive date segments; xfail removed from unit and integration tests. Two key-generation tests updated to expect literal segment when schema has no format.
  - Documentation: AI context (get_partition_path_from_schema_and_record, Hive partitioning) and CHANGELOG updated for format-only string date inference and breaking change.
- **Schema-driven Hive partitioning (task 01):** Add `validate_partition_fields_schema(stream_name, schema, partition_fields)` in `target_gcs.helpers.partition_schema`; validates that each partition field exists in schema properties, is required, and is non-nullable. Exported from `target_gcs.helpers`. Unit tests in `tests/helpers/test_partition_schema.py` (valid case, missing field, not required, required not list, null-only type).
- **Schema-driven Hive partitioning (task 02):** Add `get_partition_path_from_schema_and_record(schema, record, fallback_date, *, partition_date_format)` and `DEFAULT_PARTITION_DATE_FORMAT` in `target_gcs.helpers.partition_path`; builds partition path from `x-partition-fields` and record (fallback when missing/empty; date segments vs path-safe literals; literal slash → underscore). Unit tests in `tests/helpers/test_partition_path.py` (no/empty x-partition-fields, single date/literal, enum+date order, literal with slash, unparseable date → ParserError).
- **Schema-driven Hive partitioning (task 03):** Export `get_partition_path_from_schema_and_record` and `validate_partition_fields_schema` from `target_gcs.helpers` (both in `__all__`). Add import/usage tests that import from `target_gcs.helpers` and assert callability and correct behaviour.
- **Hive default key path:** Add `DEFAULT_KEY_NAMING_CONVENTION`, `DEFAULT_KEY_NAMING_CONVENTION_HIVE`, and `_get_effective_key_template()` in sinks.py; effective template resolution (user override → partition default → non-partition default). `_build_key_for_record` and `key_name` both use effective template and format map (tasks 06–07).

### Changed

- **target-gcs-dedup-split-logic** — Unify partition date format constant: single source for `DEFAULT_PARTITION_DATE_FORMAT` in `partition_path.py`; sinks import it; removed local constant from sinks.py.
  - Add `_flush_and_close_handle` on GCSSink; refactor `_rotate_to_new_chunk` and `_close_handle_and_clear_state` to use it.
  - Add `_apply_key_prefix_and_normalize(base)` on GCSSink; refactor `_build_key_for_record` to use it (prefix + normalize logic centralized).
  - Add `_write_record_as_jsonl(record)`; refactor `_process_record_single_or_chunked` and `_process_record_hive_partitioned` to use it (no duplicated orjson.dumps + write).
- **partition-path-extraction-date-clarity:** Parameter and naming clarity: `fallback_date` → `extraction_date` in `get_partition_path_from_schema_and_record`; sink attribute `self.fallback` → `self._extraction_date`. All "fallback" wording in partition-path context (docstrings, comments, test names) → "extraction date" so the no-partition-fields case is clearly the extraction date path, not a fallback. No behaviour change.
- **hive-partition-key-value-paths:** Literal partition path segments are now Hive-standard `key=value` (e.g. `region=eu`, `country=UK`) instead of value-only. Improves compatibility with Athena, Glue, BigQuery external tables, and Spark. Existing object keys that used value-only literal segments are not migrated; new writes use key=value segments.
- **hive-partition-format-only (breaking):** Partition path no longer infers dates from string values; only schema `format: "date"` or `"date-time"` (and native datetime/date) produce Hive date segments. Dateutil-parseable strings without that format now produce path-safe literal segments. See [hive-partition-format-only.md](../../_archive/hive-partition-format-only/hive-partition-format-only.md).
- **Schema-driven Hive partitioning (task 05):** Sink uses `hive_partitioned` instead of `partition_date_field`; when `hive_partitioned` is true and stream schema has non-empty `x-partition-fields`, calls `validate_partition_fields_schema` at init (raises `ValueError` for invalid schema). Partition path is resolved via `get_partition_path_from_schema_and_record` with `DEFAULT_PARTITION_DATE_FORMAT`; removed all use of `partition_date_field` and `partition_date_format` from sink. Init tests: invalid `x-partition-fields` → `ValueError`; valid → no exception. Partition key tests updated to use `hive_partitioned` and schema with `x-partition-fields`.
- **Schema-driven Hive partitioning (task 06):** Record-processing method renamed to `_process_record_hive_partitioned`; partition path comes from `get_partition_path_from_schema_and_record` with `DEFAULT_PARTITION_DATE_FORMAT` only (no config). Handle lifecycle unchanged; `ParserError` re-raised on unparseable date.
- **Schema-driven Hive partitioning (task 07):** `process_record` dispatches on `hive_partitioned` (not `partition_date_field`): when true calls `_process_record_hive_partitioned`, else `_process_record_single_or_chunked`. Docstring describes dispatch by `hive_partitioned` and the two code paths (already in place from task 05/06).
- **Schema-driven Hive partitioning (task 04):** Config schema: add `hive_partitioned` (boolean, default false); remove `partition_date_field` and `partition_date_format`. Update `key_naming_convention` description to reference `hive_partitioned`. Tests: assert `hive_partitioned` in schema and validation with true/false/omitted; assert `partition_date_field` and `partition_date_format` omitted from schema.
- **Hive default key path:** When `partition_date_field` is set and `key_naming_convention` is omitted, the default key template is now `{stream}/{partition_date}/{timestamp}.jsonl`; when unset, default remains `{stream}_{timestamp}.jsonl`. Added `{hive}` as an alias for `{partition_date}` in key templates when partition-by-field is enabled.
- **Hive default key path (task 08):** README config table documents conditional default for `key_naming_convention` (hive-style when `partition_date_field` set and omitted, flat when unset). Hive section documents default key shape `{stream}/{partition_date}/{timestamp}.jsonl` and that `{hive}` is an alias for `{partition_date}`. Optional: schema description for `key_naming_convention` in target.py; meltano.yml comment that example pattern is the default when `partition_date_field` is set.
- **Hive default key path (task 07):** `key_name` property now uses `_get_effective_key_template()` when `partition_date_field` is unset and `_key_name` is empty; format_map includes `format=self.output_format` so the default template `{stream}_{timestamp}.{format}` resolves. Docstring updated to state that the default when `key_naming_convention` is omitted is `DEFAULT_KEY_NAMING_CONVENTION`.
- **Hive default key path (task 06):** `_build_key_for_record` now uses `_get_effective_key_template()` for the base key; format map includes `hive=partition_path` (alias for `partition_date`) and `format` when the template contains `{format}`; docstring updated. Hive default and `{hive}` alias tests no longer xfail.
- **Tests:** Regression test for default key when `partition_date_field` and `key_naming_convention` are omitted (ensures non-partition default `{stream}_{timestamp}.jsonl` is preserved).
- **Tests:** Add test that when `partition_date_field` is set and `key_naming_convention` is omitted, key uses hive default pattern `{stream}/{partition_date}/{timestamp}.jsonl`; xfail removed after task 06.
- **Tests:** Add test that when both `partition_date_field` and `key_naming_convention` are set, built key follows the user template (e.g. `{stream}/dt={partition_date}/{timestamp}.jsonl`); regression guard so user config is never overridden by hive default.
- **Tests:** Add test that `{hive}` in key_naming_convention expands to the same partition segment as `{partition_date}`; xfail removed after task 06 (hive in format map).
- **Tests (task 08):** Sink and key-generation black-box tests: hive_partitioned false/true key behaviour, fallback date path, x-partition-fields literal+date segments, partition-change handle lifecycle; test_partition_key_generation migrated from partition_date_field to hive_partitioned + x-partition-fields; added fallback path, multiple streams order, ParserError for date-format unparseable.
- **Schema-driven Hive partitioning (task 09):** Meltano and README — plugin definition and docs: add `hive_partitioned` setting (boolean, default false); remove `partition_date_field` and `partition_date_format` from meltano.yml; README config table and Hive section document `hive_partitioned` and `x-partition-fields` (path order, validation, literal sanitization, removal of old settings); examples use `hive_partitioned` and `x-partition-fields`. See [README](README.md) for usage.

## [3.0.0] - 2026-03-12

### Added

- **Partition field schema validation** — Details: [target-gcs-partition-field-validation.md](../../_archive/target-gcs-partition-field-validation/target-gcs-partition-field-validation.md)
  - Add unit tests for validate_partition_date_field_schema.
  - Implement validate_partition_date_field_schema in partition_schema.py; export from target_gcs.helpers.
  - Add sink integration tests for partition_date_field validation (build_sink extended with optional schema/stream_name; tests for missing field, null-only, integer, valid string, unset; ValueError message asserts stream and field name).
  - Call validate_partition_date_field_schema in GCSSink.__init__ when partition_date_field is set; misconfiguration (missing or non–date-parseable field) is caught at sink init.
  - Document partition_date_field validation in AI context and changelogs (init-time check, ValueError with stream/field/reason; helper in target_gcs.helpers.partition_schema).
  - Require partition_date_field to be in schema `required`: validator raises if `schema.required` is not a list or does not contain the field.

- **dateutils-partition-timestamps** — Details: [dateutils-partition-timestamps.md](../../_archive/dateutils-partition-timestamps/dateutils-partition-timestamps.md)
  - Add python-dateutil dependency (>=2.8.1) for partition path parsing.
  - Add TDD tests for dateutil-only partition date formats (slash, RFC-style, long month); marked xfail until Task 05.
  - Add TDD test that unparseable partition timestamp raises (no silent fallback); marked xfail until Task 05.
  - Add TDD test that unsupported timezone in partition timestamp surfaces visibility (warning or error); marked xfail until Task 05.
  - Implement partition path dateutil parsing: string timestamps parsed with dateutil.parser.parse (no tzinfos); unparseable raises ParserError; unknown timezone surfaces UnknownTimezoneWarning; xfail removed from partition path tests.
  - Sink exception handling: in _process_record_partition_by_field, catch ParserError from get_partition_path_from_record and re-raise so the run fails visibly when a record has an unparseable partition date (no silent skip).
  - Integration tests for partition key: record with dateutil-parsable non-ISO partition value (e.g. "2024/03/11") produces key containing expected partition path; unparseable partition field leads to ParserError from process_record.
  - Documentation: AI context (docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md) updated to describe partition path resolution with dateutil (python-dateutil), ParserError for unparseable values (no silent fallback), and UnknownTimezoneWarning for unsupported timezone; aligned Public Interfaces, GCSSink record processing, and Partition-by-field behaviour sections.

### Changed

- **AI context (target-gcs)** — Partition-date-field validation docs: document that the partition field must be in `schema["required"]`, that non-list `schema["required"]` is rejected, and that failures raise `ValueError` with stream name, field name, and reason.
- **dateutils-partition-timestamps** — Add types-python-dateutil to dev dependencies for mypy.
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
