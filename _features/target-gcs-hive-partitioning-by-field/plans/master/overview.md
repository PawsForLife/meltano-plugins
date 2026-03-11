# Master Plan — Overview: Hive partitioning by record date field

**Feature:** target-gcs-hive-partitioning-by-field  
**Plan location:** `_features/target-gcs-hive-partitioning-by-field/plans/master/`

---

## Purpose

Add optional **hive partitioning by a configurable date field** in each record so that GCS object keys (and thus Hive-style paths) reflect the **record’s event or business date** (e.g. `created_at`, `updated_at`) instead of the extraction run date. BigQuery external tables, Spark, and other data lake tooling can discover partitions from paths like `year=YYYY/month=MM/day=DD/`.

---

## Objectives and success criteria

- **Config:** Optional `partition_date_field` (record property name) and optional `partition_date_format` (Hive path segment format; default Hive-style).
- **Key construction:** When enabled, object key includes a partition path derived from the **record’s** date field (parsed and formatted). Multiple keys per stream per run when records have different partition values.
- **Behaviour:** One active write handle; on partition change, close and clear; when partition “returns,” create a new key (new file). Missing/invalid partition field uses run-date fallback; no crash.
- **Backward compatibility:** When `partition_date_field` is unset, behaviour is unchanged (run-date `{date}`, one key per stream per run or per chunk).

---

## Key requirements and constraints

- No new external libraries for date parsing; use `datetime.fromisoformat` plus a small set of fallbacks.
- Handle strategy: **partial chunk (option c)** — one handle; no dict of handles; no reopen of same path; “return” to a partition gets a new file.
- Non-deterministic behaviour (e.g. run date for fallback) must be injectable for tests (dependency injection).
- Config and key naming must remain consistent with existing target-gcs patterns (see `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` and `AI_CONTEXT_PATTERNS.md`).

---

## Relationship to existing systems

- **target-gcs** (`loaders/target-gcs`): Only impacted component. `GCSTarget` gains new config properties; `GCSSink` gains partition-by-field key resolution, partition state, and handle lifecycle (close on partition change; new key on next write).
- **Config file:** New optional keys; existing configs remain valid.
- **Streams:** One sink per stream; partition logic is per-sink and per-record within that stream.

---

## Plan document index

| Document | Content |
|----------|---------|
| [architecture.md](architecture.md) | Component design, data flow, handle lifecycle |
| [interfaces.md](interfaces.md) | Config schema, function signatures, data contracts |
| [implementation.md](implementation.md) | Implementation order, files to change |
| [testing.md](testing.md) | TDD strategy, test cases |
| [dependencies.md](dependencies.md) | External/internal deps, config, env |
| [documentation.md](documentation.md) | README, AI context, docstrings |
