# Archive: target-gcs-handle-decimal-in-records

## The request

Downstream consumers (e.g. tap-stella-coaching-sessions → target-gcs) hit `TypeError: Type is not JSON serializable: decimal.Decimal` when the loader serialized record dicts to JSONL. Taps built on the Singer SDK can emit `decimal.Decimal` for schema `number` fields; target-gcs used `orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE)` in `gcs_target/sinks.py`, and orjson does not natively serialize `Decimal`. The request was to add handling so records containing `Decimal` (including nested) serialize to valid JSONL without error, with no regression for records without `Decimal`. Fix was to be in the target (one plugin) so any tap emitting `Decimal` would work; no tap or SDK change. Success criteria: records with `Decimal` serialize; output JSONL is valid with numeric values as JSON numbers; records without `Decimal` unchanged; implementation via TDD with a regression test first.

## Planned approach

**Solution:** Option A — orjson `default` callback. Add a small internal helper (e.g. `_json_default(obj)`) that returns `float(obj)` for `decimal.Decimal` and raises `TypeError` for any other type (no silent coercion). Pass it as `default=_json_default` to both `orjson.dumps` call sites in `sinks.py` (`_process_record_single_or_chunked` and `_process_record_partition_by_field`). Add `import decimal` and use `isinstance(obj, decimal.Decimal)`. No new dependencies; no record mutation; orjson traverses and invokes `default` per non-serializable value, so nested `Decimal`s are covered.

**Architecture:** Change confined to `loaders/target-gcs/gcs_target/sinks.py` (imports, new module-level `_json_default`, two call-site edits). No changes to config, CLI, `RecordSink.process_record` contract, or GCS/key/partition logic. Tests in `loaders/target-gcs/tests/test_sinks.py`.

**Task breakdown (TDD):** (1) Add regression test: record with `Decimal` → `process_record` → assert written bytes decode to JSON and numeric value correct; confirm test fails before fix. (2) Add test: record with non-Decimal non-serializable value raises `TypeError`. (3) Add `_json_default` and `decimal` (and `Any`) in `sinks.py`; docstring. (4) Wire `default=_json_default` at both `orjson.dumps` call sites. (5) Run full pytest, ruff check, ruff format --check, mypy from `loaders/target-gcs/`.

## What was implemented

- **Tests (TDD):** In `test_sinks.py`: (1) `test_record_with_decimal_serializes_to_valid_json` — builds sink via `build_sink()`, record with e.g. `"score": Decimal("12.34")`, mocks GCS write to capture payloads, calls `process_record`, asserts written line decodes to JSON and `score` equals `12.34`. (2) `test_non_serializable_non_decimal_type_raises_type_error` — record with e.g. `object()` in a key, asserts `TypeError` when `process_record` runs (black-box; documents that only `Decimal` is coerced).
- **Production code:** In `gcs_target/sinks.py`: added `import decimal` and `Any` in typing imports; added module-level `_json_default(obj: Any) -> float` with Google-style docstring (return `float(obj)` for `decimal.Decimal`, else raise `TypeError`); added `default=_json_default` to both `orjson.dumps(...)` calls in `_process_record_single_or_chunked` and `_process_record_partition_by_field`.
- **Verification:** Full test suite, ruff check, ruff format --check, and mypy from `loaders/target-gcs/` pass. CHANGELOG updated under target-gcs for the feature.

Records containing `decimal.Decimal` (top-level or nested) now serialize to valid JSONL; other non-serializable types still raise `TypeError`. No new dependencies; public API unchanged.
