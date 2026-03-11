# Task Plan: 08-documentation-readme-and-sample-config

**Feature:** target-gcs-hive-partitioning-by-field  
**Task:** Add user-facing documentation (README, sample config, optional Meltano settings) for partition-by-field so the feature is discoverable and accurately described.  
**Master plan:** [../master/overview.md](../master/overview.md), [../master/implementation.md](../master/implementation.md), [../master/documentation.md](../master/documentation.md)

---

## 1. Overview

This task delivers user-facing documentation for the partition-by-field feature after implementation tasks 01–07 are complete. It does not change code. Documentation must reflect the implemented behaviour (config keys, `{partition_date}` token, fallback, chunking interaction). Per project rules: update documentation to reflect code; never update code to match documentation.

**Scope:** README.md (new config options, token, fallback, example, chunking); sample.config.json (example with partition options); meltano.yml (optional settings). No automated tests; validation is manual review and consistency check against `target.py` schema and `sinks.py` behaviour.

---

## 2. Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `loaders/target-gcs/README.md` | Modify | **Config table:** Add rows for `partition_date_field` and `partition_date_format` (type, required, default, description). **New subsection:** "Hive partitioning by record date field" covering: purpose of the two options; strftime for `partition_date_format`; default Hive-style value (e.g. `year=%Y/month=%m/day=%d`); `{partition_date}` token (available when `partition_date_field` is set; replaced with partition path per record, e.g. `year=YYYY/month=MM/day=DD`); note that `{date}` remains run-date when partition-by-field is used. **Fallback:** When the record is missing the field or value is unparseable, partition path uses run date (formatted with `partition_date_format`); no crash. **Example:** Minimal config and `key_naming_convention` using `{partition_date}` (e.g. `{stream}/export_date={partition_date}/{timestamp}.jsonl`). **Chunking:** When both `max_records_per_file` and `partition_date_field` are set, rotation happens within the current partition (same partition path, new file via timestamp/chunk index). Keep README concise; do not exceed 500 lines (content_length.mdc). |
| `loaders/target-gcs/sample.config.json` | Modify | Add example demonstrating partition-by-field: include `partition_date_field` (e.g. `"created_at"`), optional `partition_date_format` (e.g. `"year=%Y/month=%m/day=%d"`), and `key_naming_convention` using `{partition_date}`. Either add a second example block (if project uses multiple examples) or extend the existing single example with optional partition keys and a comment, or add a dedicated partition example. Ensure JSON remains valid and keys match `target.py` config_jsonschema. |
| `loaders/target-gcs/meltano.yml` | Modify (optional) | If Meltano UI/env configuration for the new options is desired: under `loaders[target-gcs].settings`, add entries for `partition_date_field` and `partition_date_format` with appropriate `kind` (e.g. `string`). Align with existing settings style (env, description if present). |

**No new files.** All work is in existing README, sample config, and meltano.yml.

---

## 3. Test Strategy

**No automated tests.** The task explicitly specifies manual review only.

- **Manual checks:** README and sample config match implementation: config key names match `gcs_target/target.py` config_jsonschema; token name is `{partition_date}` as in sinks key building; fallback behaviour (missing/invalid field → run date, no crash) is described correctly.
- **Acceptance criteria (from task doc):** README is concise and accurate; sample config (if updated) validates (valid JSON, valid key names); docs do not contradict implementation.

---

## 4. Implementation Order

1. **Inspect implementation**  
   Read `loaders/target-gcs/gcs_target/target.py` for exact property names and descriptions of `partition_date_field` and `partition_date_format`. Read `loaders/target-gcs/gcs_target/sinks.py` for default partition format constant, token name `{partition_date}`, and fallback behaviour. Ensure documentation wording matches.

2. **Update README.md**  
   - Add `partition_date_field` and `partition_date_format` to the "Accepted Config Options" table (env vars if applicable, type, required, default, description).  
   - Add subsection "Hive partitioning by record date field" (or equivalent) with: purpose; token `{partition_date}` and that `{date}` stays run-date; fallback behaviour; minimal example config and key_naming_convention; chunking within partition.  
   - Keep existing structure (e.g. "Naming with chunking") and cross-reference where relevant.

3. **Update sample.config.json**  
   Add partition-by-field example: `partition_date_field`, optional `partition_date_format`, and `key_naming_convention` using `{partition_date}`. Preserve valid JSON; if the repo uses a single canonical example, add the new keys to it or add a commented/second example per project convention.

4. **Update meltano.yml (optional)**  
   If adding Meltano settings: add `partition_date_field` and `partition_date_format` under the target-gcs loader settings, with same naming and type as in README/schema.

5. **Consistency pass**  
   Re-read README and sample config; confirm no contradictions with target.py or sinks.py. Confirm sample.config.json is valid (e.g. `target-gcs --config loaders/target-gcs/sample.config.json --about` or equivalent if available).

---

## 5. Validation Steps

- [ ] README includes `partition_date_field` and `partition_date_format` in the config table with correct types and defaults.
- [ ] README documents `{partition_date}` token, its availability when `partition_date_field` is set, and that `{date}` remains run-date.
- [ ] README describes fallback (missing/unparseable → run date, no crash).
- [ ] README includes a minimal example (config + key_naming_convention with `{partition_date}`).
- [ ] README states that with both `max_records_per_file` and `partition_date_field` set, chunking rotates within the current partition.
- [ ] sample.config.json is valid JSON and includes an example using partition-by-field options and `{partition_date}` in key_naming_convention.
- [ ] If meltano.yml was updated: new settings are present and consistent with schema.
- [ ] No statements in README or sample contradict `target.py` or `sinks.py` (manual review).
- [ ] README length remains under 500 lines (content_length.mdc).

---

## 6. Documentation Updates

This task **is** the documentation update for user-facing docs and sample config. AI context (`docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`) and code docstrings are updated in **task 09** (ai-context-and-docstrings); do not change them in this task.

---

## Dependencies

- **Tasks 01–07:** Must be complete. Documentation describes the implemented schema (target.py), token and key building (sinks.py), and behaviour (fallback, handle lifecycle, chunking). If task 07 changed any behaviour, README must align with the final implementation.
