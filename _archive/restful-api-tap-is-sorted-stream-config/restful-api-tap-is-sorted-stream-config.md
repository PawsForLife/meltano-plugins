# Archive: restful-api-tap is_sorted stream config

**Feature:** restful-api-tap-is-sorted-stream-config  
**Plugin:** restful-api-tap (taps/restful-api-tap)

---

## The request

Consumers using incremental replication with a cursor/sequence_id (e.g. Stella Connect) needed a way to declare that the source API returns records **ordered by the replication key**. Without that, the tap left the Meltano Singer SDK default `is_sorted = False`, so the SDK logged that progress was not resumable if a sync was interrupted.

**Goal:** Add a stream-level **`is_sorted`** configuration option so that when the source API is ordered by the replication key, the tap can set `stream.is_sorted = True` and the SDK can treat incremental progress as **resumable** (e.g. cancel and resume the same run). Run-to-run incremental (next run from bookmark) already worked; in-run resumability did not.

**Current behaviour (before):** The tap did not read `is_sorted` from config; `DynamicStream` had no `is_sorted` parameter, so the SDK default remained `False`. Values set in Meltano project config under `config.streams[]` were ignored.

**Acceptance:** Stream-level `is_sorted` documented; when `is_sorted: true` is set, the discovered stream has `stream.is_sorted is True`; with incremental replication, interrupted syncs are reported as resumable; default remains `False` when omitted (backward compatible).

**Testing:** Black-box tests asserting discovered stream `is_sorted` from config (true, omitted, false, multi-stream per-stream independence); no assertions on logs or call counts. TDD: tests written first, expected to fail until implementation.

---

## Planned approach

**Chosen solution:** Internal only. Add `is_sorted` as a stream-level setting and wire it through to the existing Meltano Singer SDK stream attribute `is_sorted`. No new libraries; the SDK already supports resumable state when `is_sorted` is true and the stream uses a replication key. Rejected options: hardcoding `is_sorted = True` for all streams (unsafe for unsorted APIs); no change (did not meet the request).

**Architecture:** Three touchpoints—(1) plugin schema in `meltano.yml`, (2) tap config schema and discovery in `tap.py`, (3) `DynamicStream` in `streams.py`. Data flow: `config.streams[].is_sorted` → `discover_streams()` resolves `stream.get("is_sorted", False)` → `DynamicStream(..., is_sorted=is_sorted)` → `self.is_sorted` set on instance → SDK uses it for resumable state. No change to state shape, bookmarks, pagination, or record emission.

**Task breakdown (six tasks):**

1. **01-add-is-sorted-tests** — Add black-box tests (is_sorted true, omitted, false, multiple streams); TDD first; no other changes.
2. **02-add-is-sorted-plugin-schema** — Add `is_sorted` (kind: boolean) to `meltano.yml` stream-level settings.
3. **03-add-is-sorted-common-properties** — Add `is_sorted` property to `common_properties` in tap.py (BooleanType, default False, required False).
4. **04-add-is-sorted-to-dynamic-stream** — Add `is_sorted` parameter to `DynamicStream.__init__` and set instance attribute; docstring Args.
5. **05-wire-is-sorted-in-discover-streams** — In `discover_streams()` resolve `is_sorted = stream.get("is_sorted", False)` and pass `is_sorted=is_sorted` into `DynamicStream(...)` (depends on 03, 04).
6. **06-update-is-sorted-documentation** — README subsection for `is_sorted`; verify/add `DynamicStream.__init__` Args; optional one-line in `discover_streams()` docstring (depends on 01–05).

Execution order: tests first (01), then schema and code (02–05), then docs (06).

---

## What was implemented

All six tasks were completed.

- **Tests (01):** New module `taps/restful-api-tap/tests/test_is_sorted.py` with four black-box tests: `test_is_sorted_true`, `test_is_sorted_omitted`, `test_is_sorted_false`, `test_is_sorted_multiple_streams`. They use the public entry point (`RestfulApiTap(config=...).discover_streams()`) and assert only on each stream’s `stream.is_sorted`; fixtures reuse `config`, `setup_api`, `url_path` from `test_streams`.

- **Plugin schema (02):** `meltano.yml` extended with stream-level setting `is_sorted` (kind: boolean) under extractor settings.

- **Tap config (03):** `common_properties` in `tap.py` gained one property `is_sorted` (BooleanType, default False, required False) with description for resumable state.

- **DynamicStream (04):** In `streams.py`, `DynamicStream.__init__` gained parameter `is_sorted: Optional[bool] = False`, docstring Args entry, and instance handling. Implementation stores the value in `self._is_sorted` and exposes it via an `is_sorted` property for SDK compatibility (SDK reads the attribute).

- **Discovery wiring (05):** In `discover_streams()` in `tap.py`, `is_sorted = stream.get("is_sorted", False)` is resolved per stream and `is_sorted=is_sorted` is passed into each `DynamicStream(...)` call. All four tests pass after this task.

- **Documentation (06):** README updated with a stream-level option description for `is_sorted` (when to set, effect, default, link to SDK incremental replication). `discover_streams()` docstring includes a line that stream-level `is_sorted` is resolved (default False) and passed to DynamicStream. `DynamicStream.__init__` Args document `is_sorted`.

**Outcome:** Stream-level `is_sorted` is declared in the plugin, validated by the tap schema, read in discovery, and set on each `DynamicStream` instance so the Singer SDK can treat incremental syncs as resumable when the source API returns records ordered by the replication key. Default remains False when omitted; per-stream configuration is independent. CHANGELOG records the feature and links to this archive.
