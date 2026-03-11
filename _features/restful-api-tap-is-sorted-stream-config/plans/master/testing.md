# Master Plan — Testing: Stream-level `is_sorted` config

**Feature:** restful-api-tap is_sorted stream config

---

## Test Strategy

- **TDD:** Write tests first; they must fail until implementation is complete, then pass after changes (see [development_practices.mdc](../../../.cursor/rules/development_practices.mdc)).
- **Black box:** Assert on observable behaviour (discovered stream’s `is_sorted` value, not call counts or log lines).
- **Location:** `taps/restful-api-tap/tests/`. Prefer extending existing test modules (e.g. `test_tap.py` or `test_streams.py`) for discovery/stream behaviour; add a dedicated `test_is_sorted.py` if that keeps cases clearer.

---

## Test Cases (Write First)

### 1. Discovered stream has `is_sorted is True` when config sets `is_sorted: true`

- **What:** With a config that includes at least one stream with `is_sorted: true`, run discovery (or the code path that builds `DynamicStream` from config) and obtain the corresponding stream instance.
- **Assert:** `stream.is_sorted is True`.
- **Why:** Ensures the config value is read and passed through to the stream instance so the SDK can treat the stream as resumable.

### 2. Discovered stream has `is_sorted is False` when `is_sorted` is omitted

- **What:** Config with a stream that does not set `is_sorted` (key absent).
- **Assert:** For that stream, `stream.is_sorted is False`.
- **Why:** Backward compatibility; default must remain False.

### 3. Discovered stream has `is_sorted is False` when `is_sorted: false` is set

- **What:** Config with a stream that explicitly sets `is_sorted: false`.
- **Assert:** For that stream, `stream.is_sorted is False`.
- **Why:** Explicit false is honoured and does not enable resumability.

### 4. Multiple streams: per-stream `is_sorted` is independent

- **What:** Config with two (or more) streams: one with `is_sorted: true`, one with `is_sorted: false` or omitted.
- **Assert:** First stream has `is_sorted is True`, second has `is_sorted is False`.
- **Why:** Ensures resolution is per-stream and not global or last-wins.

---

## Test Implementation Notes

- **Fixtures:** Reuse existing helpers (e.g. `config()`, minimal stream entries) from `test_tap.py` / `test_streams.py`; build a small config dict with `streams: [{ "name": "...", "path": "...", "records_path": "...", "is_sorted": True }]` (and variants). Use existing schema/catalog fixtures if discovery tests already load config.
- **Discovery:** Either instantiate `RestfulApiTap` with config and call `tap.streams` (which uses `discover_streams()`), or call the code path that constructs `DynamicStream` with a test tap and assert on the returned stream’s `is_sorted`. Prefer the public entry point (tap + streams) for black-box behaviour.
- **No assertions on:** log messages, number of calls to `DynamicStream`, or internal function calls. Assert only on the stream instance’s `is_sorted` (and, for multi-stream, on each stream’s value).

---

## Optional: Resumability / state behaviour

- **What:** With `is_sorted: true` and incremental config (replication_key + source_search_field + source_search_query), an interrupted sync is reported as resumable and a subsequent run continues from the bookmark.
- **Approach:** Optional integration-style test; can rely on SDK tests for full resumability behaviour. If added: use mocked API (e.g. `requests_mock`) to simulate a sync that “stops” partway; assert state/bookmark is promoted or that a second run resumes from the bookmark. Document in plan that this is optional and may be covered by SDK or manual verification.

---

## Regression and Validity

- All new tests must be able to fail (e.g. fail before `is_sorted` is wired, pass after). No test that can only pass.
- Any failing test not marked `@pytest.mark.xfail` or `@unittest.expectedFailure` is a regression and must be fixed before the task is complete (see [development_practices.mdc](../../../.cursor/rules/development_practices.mdc)).

---

## Commands

From `taps/restful-api-tap/`: activate venv, then `uv run pytest` (or `uv run pytest tests/test_tap.py tests/test_streams.py -k is_sorted` if tests are named with `is_sorted`). Full gate: `./install.sh` (venv, deps, lint, typecheck, test).
