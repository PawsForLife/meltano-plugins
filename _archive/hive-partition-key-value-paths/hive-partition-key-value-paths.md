# Archive: Hive partition key=value paths

## The request

The target-gcs loader builds Hive-style partition paths from stream schema (`x-partition-fields`) and each record. Date-parseable fields already produced key=value segments (e.g. `year=2024/month=03/day=11`). **Literal** (non-date) partition fields produced **value-only** segments (e.g. `eu` for `region=eu`). The goal was to emit Hive-standard **key=value** for every partition directory (e.g. `region=eu`) so paths are self-documenting and tools (Athena, Glue, BigQuery, Spark) can discover partition keys from the path. The README and docs already described paths like `region=eu`; the implementation was to match that.

**Scope:** `loaders/target-gcs/target_gcs/helpers/partition_path.py` (and related tests, docs). For each literal partition field, append a path segment `field_name=value` with path-unsafe characters in the value sanitized (e.g. `/` → `_`). Date segments unchanged.

**Testing:** Unit tests in `test_partition_path.py` to assert literal segments are `field_name=value`; integration/key tests in `test_partition_key_generation.py` and sink tests updated so keys contain key=value literal segments. TDD: tests first, then implementation; all tests must pass.

---

## Planned approach

**Solution (selected):** Internal implementation only—no new dependencies. In `get_partition_path_from_schema_and_record`, when appending a literal segment, use the partition field name as the key: `field_name=value` with existing value sanitization. PyArrow and other third-party formatters were considered and rejected (PyArrow is for reading/discovery, not building paths).

**Architecture:** Behaviour-only change in the existing partition path builder. No new components or APIs. `GCSSink` continues to call `get_partition_path_from_schema_and_record` and pass the result to `_build_key_for_record`; only the format of literal segments in the returned path changes. Signature and return type unchanged.

**Task breakdown (TDD):**

1. **01 — Unit tests (partition path):** Update expectations in `test_partition_path.py` so literal segments are `field_name=value` (e.g. `region=eu`, `region=a_b`, `dt=2024_03_11`, and combined literal+date paths). Run tests; they must fail (red phase).
2. **02 — Partition path implementation:** One-line change in `partition_path.py`: replace `segments.append(str(value).replace("/", "_"))` with `segments.append(f"{field}={str(value).replace('/', '_')}")`. Update docstring. Unit tests pass (green).
3. **03 — Integration tests (key generation):** Update `test_partition_key_generation.py` and `test_sinks.py` so assertions expect key=value literal segments in keys (e.g. `dt=2024-03-11`, `created_at=2024_03_11`, `region=eu`, `r=x`). Full suite passes.
4. **04 — Documentation:** Update AI context (`AI_CONTEXT_target-gcs.md`), CHANGELOG (literal segments now key=value; compatibility note), optional README clarification.

**Compatibility:** New writes use key=value literal segments. Existing object keys with value-only segments are not migrated; documented as a behaviour change in CHANGELOG.

---

## What was implemented

- **Partition path logic:** In `partition_path.py`, literal segments are now appended as `field_name=value` (e.g. `region=eu`). Value sanitization (`/` → `_`) unchanged. Docstring updated to state literal segments are Hive-standard `field_name=value` with example `"region=eu/year=2024/month=03/day=11"`.

- **Unit tests:** `test_partition_path.py` updated so five tests expect key=value literal segments: single literal (`region=eu`), enum-then-date and date-then-enum order, slash-sanitized value (`region=a_b`), and no-format string literal (`dt=2024_03_11`). Tests assert on returned path strings only (black-box).

- **Integration and sink tests:** `test_partition_key_generation.py` and `test_sinks.py` updated so keys are asserted to contain key=value literal segments (e.g. `dt=2024-03-11`, `created_at=2024_03_11`, `created_at=not-a-date`, `region=eu`; segment order preserved). Sink test asserts `r=x` and date segment in key with order (literal before date).

- **Documentation:** CHANGELOG entry added: literal partition path segments are now Hive-standard key=value; improves compatibility with Athena, Glue, BigQuery, Spark; existing value-only keys not migrated. README states that every partition segment is key=value and literal segments are `field_name=value` (e.g. `region=eu`).

No new modules, config, or public API changes. All tests pass; no regressions.
