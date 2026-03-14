# hive-partition-format-only — Archive Summary

## The request

The **target-gcs** loader builds Hive-style partition paths from stream schema (`x-partition-fields`) and each record. The feature request was to stop inferring dates from **string** values when the partition field’s schema does not declare a date format. Previously, `get_partition_path_from_schema_and_record` could treat a partition field as a date in three ways: (1) schema `format: "date"` or `"date-time"`, (2) value is native `datetime`/`date`, or (3) value is a string parseable by `dateutil.parser.parse`. The third path added per-record work and inferred “this is a date” from string content instead of the schema.

**Goal:** Rely only on the schema to decide whether a **string** value is parsed as a date. Do not infer dates from field string values; only schema `format` (and native `datetime`/`date` types) should drive date treatment. When schema has no `format` and the value is a string, emit a path-safe literal segment (e.g. `str(value).replace("/", "_")`); when schema has no format and the value is `datetime`/`date`, keep emitting a Hive date segment.

**Scope:** Change only `loaders/target-gcs/target_gcs/helpers/partition_path.py` and related tests. **Acceptance:** Dates are never inferred from string content unless the schema declares `format: "date"` or `"date-time"`; native `datetime`/`date` are still processed as date segments.

**Testing:** Unit tests (no format + string → literal; no format + datetime → still date segment; format present → unchanged). Integration test update so that the sink key test for “dateutil-parseable string with no format” expects a literal segment. TDD: tests first, then implementation.

---

## Planned approach

**Selected solution (Option A):** Internal implementation change only. No new config flag, no external library. Gate date treatment strictly on `prop_schema.get("format") in ("date", "date-time")`. When true, keep existing behaviour (datetime/date as-is; string → dateutil parse → Hive date segment). When false or missing: if value is `datetime`/`date`, still append a Hive date segment; otherwise append path-safe literal and **remove** the branch that tried to parse strings with `dateutil.parser.parse` when format was absent.

**Architecture:** Single module change in `partition_path.py`. `get_partition_path_from_schema_and_record` signature unchanged. Callers (GCSSink), `partition_schema.py`, and helpers `__init__.py` unchanged. Data flow: for each partition field, read `value` and `fmt`; if `fmt in ("date", "date-time")` resolve date and append Hive segment; else if value is datetime/date append Hive segment; else append literal. No new dependencies; `dateutil` still used only when format is date/date-time.

**Task breakdown (TDD order):**

1. **01-unit-tests-partition-path** — Add two unit tests in `test_partition_path.py`: (a) no format + `datetime(2024, 3, 11)` → path contains Hive date segment; (b) no format + `"2024/03/11"` → path contains path-safe literal `2024_03_11`, not a date segment.
2. **02-integration-test-update** — Update `test_sink_key_contains_partition_path_from_dateutil_parsable_format` so that when schema has no format and record has dateutil-parseable string, assert key contains literal segment (e.g. `2024_03_11`) and not Hive date segment; update docstring.
3. **03-partition-path-impl** — In `partition_path.py`, remove the `elif isinstance(value, str): try: dateutil_parser.parse(...); is_date = True except ...` block; update function docstring to state format-only rule and literal when format absent.
4. **04-documentation** — Update `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` (Public Interfaces and Hive partitioning behaviour); add CHANGELOG entry for breaking change (string date inference removed).

**Key decisions:** No config option; behaviour change is unconditional. Black-box tests only (assert path string and key content). Breaking change documented in CHANGELOG for pipelines that relied on value-only date inference.

---

## What was implemented

All four tasks were completed; tests pass.

- **Unit tests** (`tests/helpers/test_partition_path.py`): Added tests so that (a) schema without format and value `datetime(2024, 3, 11)` still yields a Hive date segment, and (b) schema without format and value `"2024/03/11"` yields path-safe literal segment (e.g. `2024_03_11`), not a date segment. Existing tests for schema with `format: "date"` or `"date-time"` left unchanged.

- **Integration test** (`tests/test_partition_key_generation.py`): `test_sink_key_contains_partition_path_from_dateutil_parsable_format` updated to expect a literal segment in the key when schema has no format and record has a dateutil-parseable string; docstring updated to state “no format → literal segment even for parseable string.”

- **Partition path implementation** (`target_gcs/helpers/partition_path.py`): Removed the branch that parsed string values as dates when the partition field’s schema did not have `format` in `("date", "date-time")`. Kept the branch for native `datetime`/`date` so they still produce date segments when format is absent. When format is absent and value is a string, control falls through to the existing `else` that appends `str(value).replace("/", "_")`. Function docstring updated to state that string values are parsed as dates only when schema has format date/date-time; native datetime/date are always date segments; when format is absent and value is a string, path-safe literal is appended with no date parsing.

- **Documentation:** AI context (`docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`) updated so that “date-parseable” is defined by schema `format: "date"` or `"date-time"` only (no value-only inference), and Hive partitioning behaviour states that date-parseable is determined only by schema format. CHANGELOG (`loaders/target-gcs/CHANGELOG.md`) updated with a breaking-change entry: partition path no longer infers dates from string values; only schema format and native datetime/date produce Hive date segments; dateutil-parseable strings without that format now produce path-safe literal segments.

**Outcome:** Partition path behaviour is schema-driven for strings: string values are never parsed as dates unless the property schema has `format: "date"` or `"date-time"`. Native `datetime`/`date` continue to produce date segments regardless of format. Pipelines that set format in the stream schema are unchanged; those that relied on “value looks like a date but schema has no format” now get literal segments and are informed by the CHANGELOG.
