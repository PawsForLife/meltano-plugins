# target-gcs-hive-default-key-path — Archive Summary

## The request

**Background:** The target-gcs loader supports hive-style partitioning via `partition_date_field` and `partition_date_format`. The partition path is derived from the record’s date and formatted (e.g. `year=%Y/month=%m/day=%d`). When `key_naming_convention` was omitted and partition-by-field was enabled, the sink fell back to `{stream}_{timestamp}.{format}`, which does not include the partition path. Downstream consumers (BigQuery, Spark, etc.) expect a consistent default key pattern for hive-partitioned data: stream, then the hive path (date formatted), then the file.

**Goal:** When `partition_date_field` is set and `key_naming_convention` is omitted, the default key template must be `{stream}/{partition_date}/{timestamp}.jsonl` (or equivalent using the configured `partition_date_format`). When `partition_date_field` is unset, the default must remain `{stream}_{timestamp}.jsonl`. User-supplied `key_naming_convention` must always be respected. Optionally support a `{hive}` token as an alias for `{partition_date}` in the key template. Scope: target-gcs loader only (`loaders/target-gcs`); config, key building, and docs (README, settings, AI context) must reflect the behaviour.

**Testing needs:** Unit test when partition_date_field is set and key_naming_convention omitted → built keys use `{stream}/{partition_date}/{timestamp}.jsonl` (or `{stream}/{hive}/{timestamp}.jsonl` if alias used). Unit test when both are set → user template is used. If `{hive}` is added: test that `{hive}` expands like `{partition_date}`. Regression: when partition_date_field is unset, default remains `{stream}_{timestamp}.jsonl`. All existing tests must pass.

---

## Planned approach

**Chosen solution:** Internal conditional default in the target-gcs sink: when resolving the key template, if `key_naming_convention` is not set and `partition_date_field` is set, use `{stream}/{partition_date}/{timestamp}.jsonl` as the effective default; otherwise keep `{stream}_{timestamp}.jsonl`. Option B was adopted: add `{hive}` as an alias for `{partition_date}` in the format map when partition-by-field is on, and document it.

**Architecture:** No new modules. In `sinks.py`: (1) Module-level constants `DEFAULT_KEY_NAMING_CONVENTION` and `DEFAULT_KEY_NAMING_CONVENTION_HIVE`. (2) A single, testable effective-template rule: if `key_naming_convention` present and non-empty → use it; else if `partition_date_field` set → use hive default; else use non-partition default. (3) Use this rule in both `_build_key_for_record` and the `key_name` property. (4) In `_build_key_for_record`, add `hive=partition_path` to the format map so `{hive}` expands like `{partition_date}`. Config schema unchanged; `key_naming_convention` remains optional.

**Task breakdown (TDD):** Tests first (01–04), then implementation (05–07), then docs (08–09). 01: Regression test — default key when both options omitted (non-partition path). 02: Hive default test — partition_date_field set, no key_naming_convention → key matches `{stream}/{partition_date}/{timestamp}.jsonl`. 03: User template test — both set → key follows user template. 04: `{hive}` alias test — template with `{hive}` produces same partition segment as `{partition_date}`. 05: Add constants and `_get_effective_key_template()` in sinks.py. 06: Wire effective template into `_build_key_for_record` and add `hive` to format map. 07: Wire effective template into `key_name`. 08: Update README (config table, Hive section) and optional schema/meltano.yml. 09: Update AI context and CHANGELOG.

---

## What was implemented

- **Tests (01–04):** Regression test for default key when `partition_date_field` and `key_naming_convention` are omitted (key matches `{stream}_{timestamp}.jsonl`). Test that when `partition_date_field` is set and `key_naming_convention` is omitted, built key uses hive default `{stream}/{partition_date}/{timestamp}.jsonl`. Test that when both are set, built key follows the user template (e.g. custom `dt=...` segment). Test that `{hive}` in `key_naming_convention` expands to the same partition segment as `{partition_date}`. All in `test_partition_key_generation.py`; black-box assertions on key strings; deterministic `time_fn`/`date_fn` and fixed partition_path.

- **Implementation (05–07):** In `sinks.py`: Added `DEFAULT_KEY_NAMING_CONVENTION` and `DEFAULT_KEY_NAMING_CONVENTION_HIVE`; added `_get_effective_key_template(self)` implementing the three-branch rule. `_build_key_for_record` now uses `_get_effective_key_template()` for the base key; format map includes `hive=partition_path` and `format` when the template uses `{format}`; docstring updated. `key_name` uses `_get_effective_key_template()` when `partition_date_field` is unset and `_key_name` is empty; format_map includes `format=self.output_format` for the default template.

- **Documentation (08–09):** README config table and Hive section document the conditional default (hive-style when partition_date_field set and key_naming_convention omitted; flat when unset) and that `{hive}` is an alias for `{partition_date}`. Optional schema description in target.py and meltano.yml comment. AI context (`docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md`) updated for conditional default and `{hive}` token. CHANGELOG (`loaders/target-gcs/CHANGELOG.md`) updated under [Unreleased] with Added/Changed entries for the feature.

All planned tasks (01–09) were executed; full test suite passes; no new config properties or dependencies; behaviour is backward-compatible (non-partition default unchanged, user template always respected).
