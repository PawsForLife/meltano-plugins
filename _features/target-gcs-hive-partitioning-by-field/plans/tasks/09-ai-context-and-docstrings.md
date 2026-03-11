# Task Plan: 09 — AI context and docstrings

**Feature:** target-gcs-hive-partitioning-by-field  
**Task file:** `tasks/09-ai-context-and-docstrings.md`  
**Master plan:** `plans/master/overview.md`, `documentation.md`, `implementation.md`

---

## Overview

This task updates the target-gcs AI context file and ensures all new partition-by-field code has clear Google-style docstrings so future maintainers and agents understand config, key naming, and behaviour. It is documentation-only: no new automated tests; validation is by review that AI context and docstrings match the implementation and are consistent with the README and master plan.

**Scope:** AI context edits, in-code docstrings, and verification of config schema property descriptions. Depends on implementation tasks 01–07 being complete (config schema, partition resolution, sink state, key building, handle lifecycle, integration, regression). Task 08 (README/sample config) may be done in parallel; this task does not duplicate README content but keeps AI context aligned with it.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` | Modify |
| `loaders/target-gcs/gcs_target/sinks.py` | Modify (docstrings only) |
| `loaders/target-gcs/gcs_target/target.py` | Verify only |

### 1. `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`

- **Config schema:** In the config list (e.g. under `config_jsonschema` or equivalent section), add:
  - `partition_date_field` (optional): record property name used for partition path; when set, partition-by-field is enabled.
  - `partition_date_format` (optional): strftime format for partition path segments; default Hive-style (e.g. `year=%Y/month=%m/day=%d`).
- **Key naming:** In the tokens list, add `{partition_date}`: available when `partition_date_field` is set; replaced with the partition path per record (e.g. `year=YYYY/month=MM/day=DD`); not available when partition-by-field is off.
- **Behaviour:** Add a short paragraph: partition-by-field uses one active handle; on partition change the sink closes and clears; when the partition “returns,” the next write gets a new key (new file). Fallback for missing or invalid partition field: run date (formatted with `partition_date_format`).
- **Extension points:** Note that custom sinks can override partition resolution or key building if needed.
- **Constructor / interfaces:** If the doc lists GCSSink constructor args, add `date_fn` (optional) and any partition-related state; ensure key_name / _build_key_for_record are described where key naming is documented.
- Keep the file under the project doc length limit (e.g. 500 lines); if near the limit, keep new text concise.

### 2. `loaders/target-gcs/gcs_target/sinks.py`

- **`get_partition_path_from_record`:** Ensure a Google-style docstring: Args (record, partition_date_field, partition_date_format, fallback_date), Returns (partition path string), and behaviour when the field is missing or unparseable (use fallback_date). If the function was added in task 03, verify or add this docstring.
- **`GCSSink` class:** Update the class docstring to mention partition-by-field: when `partition_date_field` is set, the key is derived per record from that field; one handle; on partition change the sink closes and clears; when the partition “returns,” the next write creates a new key (new file).
- **`_build_key_for_record`:** Ensure a short docstring: when partition-by-field is on, builds the key from stream, partition_date, timestamp, chunk_index (if chunking); used by process_record. If the method was added in task 05, verify or add.
- No change to logic; docstrings only.

### 3. `loaders/target-gcs/gcs_target/target.py`

- **Verify only:** Confirm `partition_date_field` and `partition_date_format` are declared with `th.Property(..., description="...")` so they appear in generated schema docs. If task 01 already added these, no edit; otherwise add the descriptions.

---

## Test Strategy

- **No new automated tests.** The task is documentation and docstrings.
- **Review:** After edits, re-read the AI context document and the implementation (sinks.py, target.py) and fix any inconsistencies. Ensure no contradictions with the README (task 08) or the master plan (overview, documentation, implementation).

---

## Implementation Order

1. **Read current state:** Open `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`, `loaders/target-gcs/gcs_target/sinks.py`, and `loaders/target-gcs/gcs_target/target.py`. Confirm the partition-by-field implementation from tasks 01–07 (e.g. `get_partition_path_from_record`, `_build_key_for_record`, GCSSink partition state, config properties).
2. **Update AI context:** Edit `AI_CONTEXT_target-gcs.md`: add config properties, `{partition_date}` token, behaviour paragraph, and extension-point note. Update any constructor/interface section to reflect `date_fn` and partition behaviour.
3. **Add or verify docstrings in sinks.py:** Add or complete docstrings for `get_partition_path_from_record`, `GCSSink` class, and `_build_key_for_record` per the “Files to Create/Modify” section.
4. **Verify target.py:** Check that `partition_date_field` and `partition_date_format` have `description=` in `config_jsonschema`; add if missing.
5. **Consistency review:** Re-read the AI context and the code; fix wording so behaviour and tokens match the implementation. Cross-check with README and master documentation for alignment.

---

## Validation Steps

- [ ] `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` includes `partition_date_field` and `partition_date_format` in config, `{partition_date}` in key tokens, behaviour paragraph, and extension-point note.
- [ ] `get_partition_path_from_record` has a Google-style docstring (Args, Returns, fallback behaviour).
- [ ] `GCSSink` class docstring describes partition-by-field (one handle, close on partition change, new key when partition returns).
- [ ] `_build_key_for_record` has a docstring describing inputs and usage when partition-by-field is on.
- [ ] `target.py` config properties for `partition_date_field` and `partition_date_format` have descriptions.
- [ ] Final read of AI context and implementation shows no contradictions with README or master plan.

---

## Documentation Updates

- **AI context:** Updated by this task (see “Files to Create/Modify”).
- **Code docstrings:** Updated in `sinks.py` and verified in `target.py`.
- **README / sample config:** Handled in task 08; this task only ensures AI context and docstrings are consistent with them.
