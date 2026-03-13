# Task Plan: 09 — Meltano and README

## Overview

This task completes the schema-driven Hive partitioning feature by updating user-facing configuration and documentation. It exposes the new `hive_partitioned` setting in the Meltano plugin definition, removes deprecated partition settings, and documents the config and stream schema convention (`x-partition-fields`) in the README. Optional follow-ups update AI context and CHANGELOG. No new code or automated tests; validation is manual consistency checks.

**Scope:** Meltano plugin definition and README only (config schema and sink behaviour are implemented in tasks 04 and 05–08).

**Dependencies:** Task 04 (config schema) and tasks 05–08 (sink behaviour) must be done so that `meltano.yml` and README accurately describe the implemented config and behaviour.

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `loaders/target-gcs/meltano.yml` | Modify: add `hive_partitioned` setting (boolean, default false); remove `partition_date_field` and `partition_date_format` from `settings` and from `config` (and example comments). |
| `loaders/target-gcs/README.md` | Modify: add/update config table row for `hive_partitioned`; remove rows for `partition_date_field` and `partition_date_format`; replace "Hive partitioning by record date field" section with schema-driven Hive partitioning (hive_partitioned, x-partition-fields, path order/semantics, validation rules, literal sanitization); update key_naming_convention description and any examples that reference old settings. |
| `docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md` | Optional (per plans/master/documentation.md): Update config schema, partition behaviour, and public interfaces to reflect hive_partitioned and x-partition-fields after implementation. |
| `loaders/target-gcs/CHANGELOG.md` | Optional: Add entry for schema-driven Hive partitioning (new config, schema convention, removal of old settings); link to README. |

---

## Test Strategy

- **No new automated tests.** Task is documentation and plugin definition only.
- **Manual validation:** After edits, confirm that:
  1. `meltano.yml` lists only `hive_partitioned` (no `partition_date_field` or `partition_date_format`); default is false; example config is consistent.
  2. README config table and narrative match the actual config schema in `target.py` (hive_partitioned boolean, default false; no old partition properties).
  3. README accurately describes behaviour implemented in the sink: when `hive_partitioned` is true, path from `x-partition-fields` and record or current date; field rules (required, non-nullable); date vs literal segments; literal sanitization (e.g. `/` → `_`).
  4. If AI context or CHANGELOG are updated, they match README and code (no invented behaviour).

---

## Implementation Order

1. **Update meltano.yml**
   - In `settings`: add `- name: hive_partitioned`; remove `- name: partition_date_field` and `- name: partition_date_format`.
   - In `config`: add `hive_partitioned: false` (or omit; default is false); remove `partition_date_field`, `partition_date_format`; update comment for `key_naming_convention` to refer to `hive_partitioned` instead of `partition_date_field`.

2. **Update README.md**
   - **Config table:** Add row for `hive_partitioned` (Type: boolean, Required: no, Default: false, Description: when true, Hive-style partitioning from stream schema or current date). Remove rows for `partition_date_field` and `partition_date_format`. Update `key_naming_convention` default/description to say when `hive_partitioned` is set (and omit) vs when unset.
   - **Hive partitioning section:** Replace "Hive partitioning by record date field" with a section that covers:
     - **hive_partitioned:** When true, partition path is built from stream schema and record, or from current date when the stream has no `x-partition-fields`.
     - **x-partition-fields:** Array of property names on the stream schema (top-level); order = path segment order. Each field must be in `properties`, in `required`, and non-nullable; validation at sink init.
     - **Field semantics:** Date-parseable → one segment `year=.../month=.../day=...`; otherwise literal folder (path-safe; e.g. slash replaced).
     - **Removal:** Note that `partition_date_field` and `partition_date_format` are no longer supported.
   - **Examples:** Replace or add an example using `hive_partitioned: true` and a stream with `x-partition-fields`; remove examples that set `partition_date_field` / `partition_date_format`.
   - **Chunking:** If the README mentions chunking with partition-by-field, reword to "when both `max_records_per_file` and `hive_partitioned` are set".

3. **Optional: AI context and CHANGELOG**
   - **docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md:** Update config schema to list `hive_partitioned` and remove old partition settings; update partition behaviour to "when hive_partitioned is true" and path from schema + record; update public interfaces (path builder and validator) as in documentation.md.
   - **loaders/target-gcs/CHANGELOG.md:** Add a short entry for this feature: schema-driven Hive partitioning, new config `hive_partitioned`, stream schema `x-partition-fields`, removal of `partition_date_field` and `partition_date_format`; link to README for usage.

---

## Validation Steps

1. Run `meltano install` (or equivalent) from a project that uses this plugin and confirm no schema/config errors.
2. Read through README and meltano.yml; ensure no references to `partition_date_field` or `partition_date_format` remain except in "removal" or "no longer supported" notes.
3. Cross-check README against `target_gcs/target.py` config_jsonschema: only `hive_partitioned` (boolean, default false) for partition; key template behaviour described matches sink logic.
4. If CHANGELOG was updated, ensure version/date and entry text are consistent with project conventions.

---

## Documentation Updates

- **README.md:** Primary documentation updates are the implementation steps above (config table, Hive section, examples, chunking wording).
- **meltano.yml:** In-repo example config; comments must describe `hive_partitioned` and key template default when it is set.
- **AI_CONTEXT_target-gcs.md (optional):** Config schema, partition behaviour, and helper interfaces so that future work and AI context stay aligned with the code.
- **CHANGELOG.md (optional):** User-visible record of the feature and breaking change (removal of old partition settings).

All documentation must reflect the implemented behaviour only; do not add behaviour not in the master plan or code.
