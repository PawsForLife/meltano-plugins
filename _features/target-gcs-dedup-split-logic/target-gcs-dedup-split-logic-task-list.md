# Task list: target-gcs-dedup-split-logic

Tasks are listed in execution order. Each task document lives in `_features/target-gcs-dedup-split-logic/tasks/`.

| Order | Task file | Summary |
|-------|-----------|---------|
| 1 | [01-unify-partition-date-format-constant.md](tasks/01-unify-partition-date-format-constant.md) | Remove local `DEFAULT_PARTITION_DATE_FORMAT` from sinks.py; import from partition_path; export from helpers/__init__.py if needed. |
| 2 | [02-add-flush-and-close-handle.md](tasks/02-add-flush-and-close-handle.md) | Implement `_flush_and_close_handle`; refactor `_rotate_to_new_chunk` and `_close_handle_and_clear_state` to call it. |
| 3 | [03-add-apply-key-prefix-and-normalize.md](tasks/03-add-apply-key-prefix-and-normalize.md) | Implement `_apply_key_prefix_and_normalize`; refactor `_build_key_for_record` to use it. |
| 4 | [04-add-write-record-as-jsonl.md](tasks/04-add-write-record-as-jsonl.md) | Implement `_write_record_as_jsonl`; refactor both record-processing methods to call it. |
| 5 | [05-add-maybe-rotate-if-at-limit.md](tasks/05-add-maybe-rotate-if-at-limit.md) | Implement `_maybe_rotate_if_at_limit`; refactor both record-processing methods to call it before writing. |
| 6 | [06-add-compute-non-hive-key.md](tasks/06-add-compute-non-hive-key.md) | Implement `_compute_non_hive_key` (using `_apply_key_prefix_and_normalize`); refactor `key_name` non-hive branch. |
| 7 | [07-add-init-hive-partitioning.md](tasks/07-add-init-hive-partitioning.md) | Implement `_init_hive_partitioning`; refactor `__init__` hive branch to call it. |
| 8 | [08-add-assert-field-required-and-non-null.md](tasks/08-add-assert-field-required-and-non-null.md) | Implement `_assert_field_required_and_non_null_type` in partition_schema.py; refactor both validators to use it. |
| 9 | [09-update-docstrings-and-ai-context.md](tasks/09-update-docstrings-and-ai-context.md) | Confirm docstrings on all new methods/function; add comments where non-obvious; update AI context to match structure. |

## Execution order

1. **01** — Constant (no dependency).
2. **02** — Flush/close (no dependency on other new code).
3. **03** — Prefix/normalize (no dependency on other new code).
4. **04** — Write record (depends on 01–03 for clean baseline).
5. **05** — Maybe rotate (depends on 04; same call sites).
6. **06** — Non-hive key (depends on 03 for `_apply_key_prefix_and_normalize`).
7. **07** — Init hive (independent; ordered after 06 for consistency).
8. **08** — Schema helper (independent; ordered after 07).
9. **09** — Docs (depends on 01–08 complete).

## Dependency summary

- **03** is required before **06** (`_compute_non_hive_key` uses `_apply_key_prefix_and_normalize`).
- **04** is required before **05** (rotate is called before write in the same methods).
- **09** must run last (documents all new code).
