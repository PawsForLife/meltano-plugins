# Pipeline Scratchpad

## Feature: restful-api-tap-is-sorted-stream-config

- **Pipeline State:** Phase 4 (per-task plans) complete; Phase 5 in progress
- **Task Completion Status:** Research complete; master plan written; tasks created
- **Execution Order:** 01-add-is-sorted-tests.md → 02-add-is-sorted-plugin-schema.md → 03-add-is-sorted-common-properties.md → 04-add-is-sorted-to-dynamic-stream.md → 05-wire-is-sorted-in-discover-streams.md → 06-update-is-sorted-documentation.md
- **Tasks location:** `_features/restful-api-tap-is-sorted-stream-config/tasks/` (6 task docs)
- **Task list:** `_features/restful-api-tap-is-sorted-stream-config/restful-api-tap-is-sorted-stream-config-task-list.md`
- **Output directory:** `_features/restful-api-tap-is-sorted-stream-config/planning/`
- **Plan location:** `_features/restful-api-tap-is-sorted-stream-config/plans/master/` (overview, architecture, interfaces, implementation, testing, dependencies, documentation)
- **Key findings:** Tap currently does not read or set `is_sorted`; the Meltano Singer SDK already supports resumable incremental state when a stream has `is_sorted = True` and a replication key. No external library is required.
- **Selected solution:** Internal: add stream-level `is_sorted` (boolean, default False) to plugin schema and tap config, read it in `discover_streams()`, pass to `DynamicStream`, and set `self.is_sorted` on the stream instance so the SDK treats interrupted syncs as resumable when the source API returns records ordered by the replication key.
- **Key decisions (plan):**
  - **Schema shape:** `is_sorted` is stream-level only (boolean, default False, optional); no top-level default or new env/CLI. Config validated via existing Singer SDK schema; no new Pydantic/dataclass.
  - **Test strategy:** TDD; black-box tests that assert discovered stream’s `stream.is_sorted` for config variants (true, false, omitted, multiple streams). No assertions on logs or call counts. Optional integration test for resumability can rely on SDK behaviour.
  - **Touchpoints:** Three files only—`meltano.yml` (one setting), `tap.py` (common_properties + discover_streams), `streams.py` (__init__ param + self.is_sorted). No new modules or dependencies.
- **Task plan created:** 01-add-is-sorted-tests at plans/tasks/01-add-is-sorted-tests.md
- **Task plan created:** 02-add-is-sorted-plugin-schema at plans/tasks/02-add-is-sorted-plugin-schema.md
- Task plan created: 03-add-is-sorted-common-properties at plans/tasks/03-add-is-sorted-common-properties.md
- Task plan created: 05-wire-is-sorted-in-discover-streams at plans/tasks/05-wire-is-sorted-in-discover-streams.md
- Task plan created: 06-update-is-sorted-documentation at plans/tasks/06-update-is-sorted-documentation.md
- Task plan created: 04-add-is-sorted-to-dynamic-stream at plans/tasks/04-add-is-sorted-to-dynamic-stream.md
- Task 01-add-is-sorted-tests completed, tests passing
