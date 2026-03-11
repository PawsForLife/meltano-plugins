# Task Plan: 04 — Add is_sorted to DynamicStream (streams.py)

**Feature:** restful-api-tap-is-sorted-stream-config  
**Task doc:** `_features/restful-api-tap-is-sorted-stream-config/tasks/04-add-is-sorted-to-dynamic-stream.md`  
**Master plan:** `_features/restful-api-tap-is-sorted-stream-config/plans/master/`

---

## 1. Overview

This task adds an **`is_sorted`** parameter and instance attribute to `DynamicStream` in `streams.py` so that:

- The constructor accepts `is_sorted: Optional[bool] = False` and sets `self.is_sorted` on the instance.
- The Singer SDK can read `stream.is_sorted` for resumable incremental state when the source API returns records ordered by the replication key.
- Task 05 can pass the resolved config value from `discover_streams()` into `DynamicStream(..., is_sorted=is_sorted)`.

No changes to pagination, URL params, or record emission. No dependency on task 03 in this file; task 05 depends on both task 03 (common_properties) and this task (DynamicStream signature).

---

## 2. Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `taps/restful-api-tap/restful_api_tap/streams.py` | Modify | Add `is_sorted` parameter to `DynamicStream.__init__`, docstring Args entry, and `self.is_sorted` attribute |

**Insertion points (from current `streams.py`):**

**a. Parameter list** (after `flatten_records`, before `authenticator`; ~line 85):

- Add: `is_sorted: Optional[bool] = False,`

**b. Docstring Args** (in the `__init__` docstring, after the `flatten_records` entry, before `authenticator`):

- Add: `is_sorted: when True, stream is declared sorted by replication_key for resumable state. Default False.`

**c. Instance attribute** (after `self.flatten_records = flatten_records`, ~line 169):

- Add: `self.is_sorted = is_sorted`

No new imports required; `Optional` is already imported from `typing`.

---

## 3. Test Strategy

- **No new test file** in this task (per task doc). Task 01 tests assert discovered stream `is_sorted` end-to-end once task 05 wires the value from config; those tests will still fail until task 05 is done.
- **Optional unit test:** A test that instantiates `DynamicStream(..., is_sorted=True)` and asserts `stream.is_sorted is True`, and `DynamicStream(...)` (default) asserts `stream.is_sorted is False`. The task doc states this is optional and can be covered by task 01’s black-box discovery tests; if the implementer adds it, place it in an existing stream test module (e.g. `test_streams.py`) and keep it black-box (assert on the instance attribute only, no call-count or log assertions).
- **Regression:** Run the full test suite from `taps/restful-api-tap/`. No existing tests should fail due to this change; the new parameter is optional and defaulted.

---

## 4. Implementation Order

1. Open `taps/restful-api-tap/restful_api_tap/streams.py`.
2. In `DynamicStream.__init__`, add `is_sorted: Optional[bool] = False` to the parameter list after `flatten_records`, before `authenticator`.
3. In the same `__init__` docstring, add an Args entry for `is_sorted` (after `flatten_records`, before `authenticator`).
4. After `self.flatten_records = flatten_records`, add `self.is_sorted = is_sorted`.
5. Run lint and typecheck: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy restful_api_tap` (from `taps/restful-api-tap/`).
6. Run the test suite: `uv run pytest` (or `./install.sh`). Fix any regressions.

---

## 5. Validation Steps

- [ ] `DynamicStream.__init__` has parameter `is_sorted: Optional[bool] = False` in the correct position.
- [ ] Docstring Args include `is_sorted` with the agreed description (sorted by replication_key, resumable state, default False).
- [ ] `self.is_sorted = is_sorted` is set after `self.flatten_records = flatten_records`.
- [ ] `DynamicStream(..., is_sorted=True)` yields `stream.is_sorted is True`; default (or `is_sorted=False`) yields `stream.is_sorted is False`.
- [ ] No change to pagination, URL params, or record emission; SDK can read `stream.is_sorted`.
- [ ] `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy restful_api_tap` pass.
- [ ] `uv run pytest` passes (no new failures; task 01 discovery tests may still fail until task 05).

---

## 6. Documentation Updates

None for this task. Stream-level `is_sorted` behaviour is documented in task 06 (README and/or meltano.yml).
