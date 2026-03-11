# Task Plan: 05 — Wire is_sorted in discover_streams() (tap.py)

**Feature:** restful-api-tap-is-sorted-stream-config  
**Task doc:** `_features/restful-api-tap-is-sorted-stream-config/tasks/05-wire-is-sorted-in-discover-streams.md`  
**Master plan:** `_features/restful-api-tap-is-sorted-stream-config/plans/master/`

---

## 1. Overview

This task wires the stream-level **`is_sorted`** config into discovery so that every constructed `DynamicStream` receives the correct value. In `discover_streams()` the tap resolves `is_sorted` from each stream's config (default `False` when omitted) and passes it into `DynamicStream(...)`. After this task, the stream instance has `stream.is_sorted` set as intended, and the task 01 tests (all four cases) must pass.

**Prerequisites:** Task 03 (common_properties defines `is_sorted`) and task 04 (DynamicStream accepts `is_sorted` and sets `self.is_sorted`) must be complete. This task does not add schema or stream-class code; it only connects config to the existing parameter.

---

## 2. Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `taps/restful-api-tap/restful_api_tap/tap.py` | Modify | In `discover_streams()`: (1) resolve `is_sorted` from stream config; (2) pass it into `DynamicStream(...)` |

**Change (1) — Resolution (stream-level only):** In the same block where other stream-level keys are resolved (e.g. `flatten_records`, `source_search_query`), add:

```python
is_sorted = stream.get("is_sorted", False)
```

Place it after `flatten_records = stream.get(...)` and before the `schema = {}` block (around line 489). Use stream-level only; no top-level fallback (i.e. do not use `self.config.get("is_sorted", False)`).

**Change (2) — DynamicStream call:** Add one keyword argument to the `DynamicStream(...)` constructor:

```python
is_sorted=is_sorted,
```

Insert after `source_search_query=source_search_query,` and before `use_request_body_not_params=...` (so the stream receives the resolved value). The exact line in the current file is after `source_search_query=source_search_query,` (around line 556) and before `use_request_body_not_params=self.config.get(...)`.

---

## 3. Test Strategy

- **No new test file** in this task (per task doc).
- **Run task 01 tests:** All four cases must pass:
  1. Discovered stream has `is_sorted is True` when config sets `is_sorted: true`.
  2. Discovered stream has `is_sorted is False` when `is_sorted` is omitted.
  3. Discovered stream has `is_sorted is False` when `is_sorted: false` is set.
  4. Multiple streams: per-stream `is_sorted` is independent (one `True`, one `False` or omitted).
- **Full gate:** From `taps/restful-api-tap/`: `./install.sh` (venv, deps, lint, typecheck, test). Any failing test not marked as expected failure is a regression and must be fixed.

---

## 4. Implementation Order

1. Open `taps/restful-api-tap/restful_api_tap/tap.py` and locate `discover_streams()`.
2. In the `for stream in self.config["streams"]:` loop, find the resolution block (e.g. after `flatten_records = stream.get(...)`). Add `is_sorted = stream.get("is_sorted", False)`.
3. Find the `streams.append(DynamicStream(...))` call. In the keyword arguments, add `is_sorted=is_sorted,` after `source_search_query=source_search_query,` and before `use_request_body_not_params=...`.
4. Run lint and typecheck: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy restful_api_tap`.
5. Run tests: `uv run pytest` (or `./install.sh`). Confirm all task 01 tests pass and no regressions.

---

## 5. Validation Steps

- [ ] `is_sorted` is resolved with `stream.get("is_sorted", False)` only (no top-level fallback).
- [ ] Every `DynamicStream(...)` call in `discover_streams()` includes `is_sorted=is_sorted`.
- [ ] Task 01 tests: all four cases pass (true, omitted, false, multiple streams).
- [ ] `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy restful_api_tap` pass.
- [ ] `uv run pytest` passes with no regressions.
- [ ] No other files are modified; no new modules or helpers.

---

## 6. Documentation Updates

None for this task. User-facing documentation for `is_sorted` is updated in task 06.
