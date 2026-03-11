# Task 01: Add is_sorted tests

## Background

Per TDD and the master plan (testing.md, implementation.md), tests are written first and must fail until the implementation is complete. This feature adds a stream-level `is_sorted` config; the tap must pass it through to `DynamicStream` so that `stream.is_sorted` reflects the config. Tests assert on the discovered stream instance’s `is_sorted` attribute (black-box; no assertions on logs or call counts). This task has no dependencies on other tasks.

## This Task

- **Location:** `taps/restful-api-tap/tests/`. Prefer a dedicated `test_is_sorted.py` or extend existing discovery tests (e.g. `test_tap.py` or `test_streams.py`) so that cases are clear.
- **Approach:** Build minimal config dicts with `streams: [{ "name", "path", "records_path", "is_sorted": True|False|absent }]` (and variants). Instantiate `RestfulApiTap` with config and obtain streams via the public entry point (e.g. `tap.streams` which uses `discover_streams()`). Assert on each stream’s `stream.is_sorted`.
- **Test cases to implement:**
  1. **is_sorted true:** Config with at least one stream with `is_sorted: true`. Assert that the corresponding discovered stream has `stream.is_sorted is True`.
  2. **is_sorted omitted:** Config with a stream that does not set `is_sorted` (key absent). Assert for that stream `stream.is_sorted is False`.
  3. **is_sorted false:** Config with a stream that explicitly sets `is_sorted: false`. Assert for that stream `stream.is_sorted is False`.
  4. **Multiple streams:** Config with two or more streams: one with `is_sorted: true`, one with `is_sorted: false` or omitted. Assert first stream has `is_sorted is True`, second has `is_sorted is False` (per-stream independence).
- **Acceptance criteria:** All four cases are covered; tests fail before `is_sorted` is wired in tap/stream (expected); no assertions on log messages, call counts, or internal function calls. Follow `@.cursor/rules/development_practices.mdc` (black-box, valid tests that can fail).

## Testing Needed

- The tests defined above are the testing deliverable for this task. Run with `uv run pytest` from `taps/restful-api-tap/` (or `-k is_sorted`). Tests must be able to fail (e.g. fail until tasks 02–05 are done); no test that can only pass.
