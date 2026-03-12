# Pipeline Scratchpad

## Bug: target-gcs-real-client-in-tests

**Pipeline State:** Phase 6 Complete. Phase 7 Pending.
**Task Completion Status:** 01, 02, 03, 04 completed; tests passing.
**Plan location:** `_bugs/target-gcs-real-client-in-tests/plans/master/` (overview, root-cause-analysis, fix-approach, implementation, testing, validation).
**Tasks:** `_bugs/target-gcs-real-client-in-tests/tasks/` — 4 tasks. Ordered list: `01-gcssink-optional-storage-client.md`, `02-gcstarget-storage-client-and-get-sink-override.md`, `03-test-core-subclass-and-get-target-test-class.md`, `04-test-sinks-build-sink-optional.md`. **Execution order:** 01 → 02 → 03 → 04 (03 depends on 01 and 02; 04 depends on 01; 04 is optional for the fix).

---

## Phase 1 handoff: target-gcs-real-client-in-tests

- **Bug name:** target-gcs-real-client-in-tests
- **Investigation directory:** `_bugs/target-gcs-real-client-in-tests/investigation/`
- **Root cause hypothesis:** The GCS storage client is constructed inside the sink (`Client()` at `sinks.py` lines 182 and 275) with no injection point, so tests run the real code path and hit `google.auth.default()` → `DefaultCredentialsError` in CI. Making the client injectable (per development_practices.mdc) will allow tests to pass without ADC.
- **Affected components:** `loaders/target-gcs/target_gcs/sinks.py` (GCSSink), `loaders/target-gcs/target_gcs/target.py` (GCSTarget), `loaders/target-gcs/tests/test_core.py` (TestGCSTarget / standard target tests), `loaders/target-gcs/tests/test_sinks.py` (unit tests that could use an injected client for write tests).

---

## Phase 2 (Research) — key findings and applicable solutions

- **Internal/external alignment:** development_practices.mdc and AI context require external API connections to be passed in; GCSSink already uses optional `time_fn`/`date_fn` injection. Singer SDK’s SQLTarget (PR #1864) overrides `get_sink()` to pass a shared connector into sinks—same pattern applies for a shared GCS client.
- **Recommended fix (Option A):** Add optional `storage_client=None` to `GCSSink.__init__`; use it in `gcs_write_handle` and `_process_record_partition_by_field` when set, else `Client()`. Have `GCSTarget` hold `_storage_client` and override `get_sink()` to pass it when creating sinks. In test_core, use a target subclass that sets `_storage_client` to a mock and pass that subclass to `get_target_test_class()` so standard target tests run without ADC.
- **Research output:** `_bugs/target-gcs-real-client-in-tests/research/` — internal-documentation.md, external-research.md, similar-issues.md, applicable-solutions.md (options B–E documented; A recommended).

---

## Phase 3 (Plan) — fix approach summary

**Chosen solution (Option A):** Make the GCS storage client injectable via optional `storage_client` on the sink and target override of `get_sink()` so the target passes the client when creating sinks. Production keeps current behavior when no client is provided (sink uses `Client()`). Add a target subclass in test_core that sets `_storage_client` to a mock and pass that subclass to `get_target_test_class()`, so standard target tests run without ADC. Implementation order: (1) regression test that fails without fix, (2) GCSSink optional `storage_client` and use at both call sites, (3) GCSTarget `_storage_client` and `get_sink()` override, (4) test_core subclass and switch to it, (5) optional test_sinks `build_sink(storage_client=...)` and reduce patches. Success: all tests pass without GCP credentials; no config/CLI change; DI aligned with development_practices.mdc.

---

## Phase 4 (Task list) — decomposition complete

- **Tasks dir:** `_bugs/target-gcs-real-client-in-tests/tasks/` (4 tasks).
- **Ordered task files:** `01-gcssink-optional-storage-client.md`, `02-gcstarget-storage-client-and-get-sink-override.md`, `03-test-core-subclass-and-get-target-test-class.md`, `04-test-sinks-build-sink-optional.md`.
- **Execution order:** 01 → 02 → 03 → 04. Task 03 depends on 01 and 02; task 04 depends on 01; task 04 is optional for the bug fix.
- **Blocking dependencies:** None for 01; 02 depends on 01; 03 depends on 01 and 02; 04 depends on 01.

---

- **Task plan created:** 01-gcssink-optional-storage-client at plans/tasks/01-gcssink-optional-storage-client.md
- **Task plan created:** 02-gcstarget-storage-client-and-get-sink-override at plans/tasks/02-gcstarget-storage-client-and-get-sink-override.md
- **Task plan created:** 04-test-sinks-build-sink-optional at plans/tasks/04-test-sinks-build-sink-optional.md
- **Task plan created:** 03-test-core-subclass-and-get-target-test-class at plans/tasks/03-test-core-subclass-and-get-target-test-class.md
