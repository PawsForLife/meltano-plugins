# fix-dateutils-record-timestamps — Archive Summary

## The request

Target-gcs failed when taps emitted date/time strings in non-ISO form (e.g. `'2024-05-13 02:17:54 UTC'`), raising `ValueError: Could not parse value '...' for field 'created_at'`. Parsing was done by Singer SDK's `_parse_timestamps_in_record` using `datetime.fromisoformat()`, which accepts only strict ISO. Expected: record date-time fields in common formats parse successfully. Partition path parsing in target-gcs already used dateutil; record-level parsing did not.

## Planned approach

Override `_parse_timestamps_in_record` in `GCSSink` so string date/datetime values are parsed with `dateutil.parser.parse` instead of the SDK's fromisoformat. Preserve schema and key checks; on parse failure call the SDK's `handle_invalid_timestamp_in_record` so `datetime_error_treatment` is unchanged. Keep `time` type using `time_fromisoformat`. Tasks: (1) Add unit tests for non-ISO string parsed successfully and unparseable string handled per treatment; (2) Implement override in `target_gcs/sinks.py`; (3) Update plugin CHANGELOG.

## What was implemented

- **Task 01 — Tests:** Added `tests/unit/test_sinks/test_record_timestamps.py`: `test_record_with_non_iso_datetime_string_parsed_successfully` (record with `created_at: '2024-05-13 02:17:54 UTC'` parsed without error; value is datetime) and `test_record_with_unparseable_datetime_string_raises` (invalid string raises).
- **Task 02 — Override:** In `target_gcs/sinks.py`, overrode `_parse_timestamps_in_record`: for properties with type date or date-time and string value, use `dateutil.parser.parse(value)` and assign `.date()` for date type; for time type use `time_fromisoformat`; on `ValueError` or `DateutilParserError` call `handle_invalid_timestamp_in_record`. Non-string date/datetime values left unchanged.
- **Task 03 — Changelog:** Under `loaders/target-gcs/CHANGELOG.md` ### Fixed, added fix-dateutils-record-timestamps entry with link to this archive.

All 131 target-gcs tests pass. No new dependencies; python-dateutil already present.
