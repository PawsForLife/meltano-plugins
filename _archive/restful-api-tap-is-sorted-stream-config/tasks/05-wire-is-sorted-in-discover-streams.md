# Task 05: Wire is_sorted in discover_streams() (tap.py)

## Background

`discover_streams()` must read `is_sorted` from each stream's config and pass it into `DynamicStream(...)`. This task depends on task 03 (common_properties defines the key) and task 04 (DynamicStream accepts the parameter). After this task, task 01 tests should pass.

## This Task

- **File:** `taps/restful-api-tap/restful_api_tap/tap.py`
- **Where:** In the block that builds the `DynamicStream(...)` call (around the existing resolution of `flatten_records`, `source_search_query`, etc., and the `streams.append(DynamicStream(...))` call).
- **Changes:**
  1. Before `streams.append(DynamicStream(...))`, resolve: `is_sorted = stream.get("is_sorted", False)` (stream-level only; same pattern as other stream-level keys like `flatten_records`).
  2. Add to the `DynamicStream(...)` keyword arguments: `is_sorted=is_sorted` (e.g. after `source_search_query=source_search_query`, before `use_request_body_not_params`).
- **Acceptance criteria:** Every constructed `DynamicStream` receives `is_sorted`; value comes from `stream.get("is_sorted", False)`; default False when key is missing; no top-level fallback for `is_sorted`.

## Testing Needed

- Run task 01 tests: all four cases (is_sorted true, omitted, false, multiple streams) must pass. No new test file in this task. Full gate: `./install.sh` from `taps/restful-api-tap/` (venv, deps, lint, typecheck, test).
