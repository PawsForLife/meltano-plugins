# Possible solutions — Hive partitioning by record date field

**Feature:** target-gcs-hive-partitioning-by-field  
**Scope:** target-gcs loader (loaders/target-gcs).

---

## External vs internal

- **External:** No Singer target or common library was found that implements “partition GCS object key by a configurable record date field” as a drop-in. BigQuery’s Hive partitioning applies when *reading* GCS (HivePartitioningOptions); writing partition paths is the target’s responsibility. Datateer/target-gcs and similar targets use run-time date in the key, not record-derived. **Conclusion:** implement internally inside target-gcs.
- **Date parsing:** Python’s `datetime.fromisoformat` plus one or two fallbacks (e.g. `%Y-%m-%d`) suffice; no extra library required. Keep parsing in a small, testable helper.

---

## Handle / file strategies (internal options)

Three ways to route records to the correct GCS key when partition-by-field is enabled:

### (a) Dict of handles per partition path

- **Idea:** Maintain a mapping `partition_path -> (key_name, gcs_write_handle)`. For each record, compute partition path from the record; look up or create handle for that path; write to that handle.
- **Pros:** One open file per distinct partition; minimal number of files when records are grouped by partition; efficient for many records per partition.
- **Cons:** Must track and close all handles on sink drain; memory and fd usage grow with number of distinct partitions; more state and edge cases (e.g. many partitions in one stream).

### (b) Close and reopen on partition change

- **Idea:** Single current handle. When the partition value changes (compared to the previous record), close the current handle and clear key cache; on the next write, open a new handle for the new (or same) partition path.
- **Pros:** Only one handle open at a time; predictable resource use; same partition can be reopened if records interleave (e.g. A, B, A).
- **Cons:** Reopen logic and key caching must account for “same partition again”; possible extra open/close if records alternate between two partitions frequently.

### (c) Partial chunk — new file per partition visit, no reopen

- **Idea (user-specified alternative):** Continue writing to the current handle while the partition value stays the same. When the partition value *changes*, close the handle and clear state. When the partition value *returns* to a previously seen value, do **not** reopen the old file; create a **new** key (e.g. with a timestamp or per-visit chunk index) and open a new file. So: one active handle; on partition change, close; on “return” to a prior partition, new file.
- **Pros:** No dict of handles; no reopen of the same path; logic is simple (current partition + current key/handle only; on change, close and next write gets a new key).
- **Cons:** More, smaller files when records revisit the same partition (e.g. A, B, A produces two files for A); acceptable for many use cases and keeps implementation and testing simpler.

---

## Comparison

| Criterion        | (a) Dict of handles | (b) Close/reopen   | (c) Partial chunk (new file per visit) |
|-----------------|---------------------|--------------------|---------------------------------------|
| Max open handles| One per partition   | One                | One                                    |
| Files per partition | One              | One (reopen same)   | One per “visit” to that partition     |
| Complexity      | Higher (dict, drain)| Medium (reopen key)| Lower (no reopen, no dict)             |
| Resource usage  | FDs per partition   | One FD             | One FD                                 |
| Interleaved data| Single file per partition | Single file per partition | Multiple files per partition (one per visit) |

---

## Recommendation for architect

- **Config and key token:** Same for all options: add `partition_date_field`, optional `partition_date_format`, and a token (e.g. `{partition_date}`) in key naming; partition path from record with defined fallback for missing/invalid.
- **Default choice for implementation:** Option **(c)** unless the product requires exactly one file per partition regardless of visit order—then (a) or (b). Document (a) and (b) in this doc so the architect can compare and choose.
