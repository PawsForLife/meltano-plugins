# Task Plan: 03 — Add is_sorted to common_properties (tap.py)

**Feature:** restful-api-tap-is-sorted-stream-config  
**Task doc:** `_features/restful-api-tap-is-sorted-stream-config/tasks/03-add-is-sorted-common-properties.md`  
**Master plan:** `_features/restful-api-tap-is-sorted-stream-config/plans/master/`

---

## 1. Overview

This task adds the stream-level config property **`is_sorted`** to the tap's schema in `tap.py` only. It extends `common_properties` with a single `th.Property` so that:

- Config validation (SDK schema load) accepts the `is_sorted` key.
- Task 05 can safely read `stream.get("is_sorted", False)` in `discover_streams()` and pass it into `DynamicStream`.

No wiring in `discover_streams()` or `DynamicStream` in this task; no new Pydantic/dataclass. Validation continues to use the existing Singer SDK schema.

---

## 2. Files to Create/Modify

| File | Action | Change |
|------|--------|--------|
| `taps/restful-api-tap/restful_api_tap/tap.py` | Modify | Append one `th.Property("is_sorted", ...)` to `common_properties` |

**Insertion point:** Inside the `th.PropertiesList(...)` of `common_properties`, **after** the `source_search_query` property (the last property before the closing `)` of the list), i.e. after the comma on the line that closes the `source_search_query` `th.Property` (around line 124).

**Exact addition:**

```python
        th.Property(
            "source_search_query",
            ...
        ),
        th.Property(
            "is_sorted",
            th.BooleanType(),
            default=False,
            required=False,
            description="When true, the stream is declared sorted by replication_key; "
                        "enables resumable state if the sync is interrupted.",
        ),
    )
```

Ensure a comma after the `source_search_query` block and before the new `is_sorted` block; the closing `)` of the list follows the new property.

---

## 3. Test Strategy

- **No new test file** in this task (per task doc).
- **Task 01 tests** (when present) will still fail until task 05 wires `is_sorted` in `discover_streams()` and sets it on the stream; after task 05, those tests validate schema + discovery together.
- **Regression:** Run the existing test suite from `taps/restful-api-tap/`; no existing tests should start failing due to this change. The only effect is that the config schema gains an optional property.
- **Optional sanity check:** Instantiate the tap with a config that includes `streams: [{ "name": "...", "path": "...", "records_path": "...", "is_sorted": true }]` and ensure the tap loads without validation error (schema accepts the key). Not required for task sign-off if the full test suite passes.

---

## 4. Implementation Order

1. Open `taps/restful-api-tap/restful_api_tap/tap.py`.
2. Locate the end of `common_properties` (the `th.Property("source_search_query", ...)` block and the closing `)` of `th.PropertiesList`).
3. After the comma that closes the `source_search_query` property, insert the `is_sorted` `th.Property` block as specified in section 2.
4. Run lint and typecheck from `taps/restful-api-tap/`: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy restful_api_tap`.
5. Run the test suite: `uv run pytest` (or `./install.sh`). Fix any regressions.

---

## 5. Validation Steps

- [ ] `common_properties` in `tap.py` includes exactly one new property: `is_sorted` (type `th.BooleanType()`, `default=False`, `required=False`), with the agreed description.
- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass.
- [ ] `uv run mypy restful_api_tap` passes.
- [ ] `uv run pytest` passes (no new failures; task 01 tests may still fail until task 05).
- [ ] No other files are modified; no new modules or Pydantic/dataclass.

---

## 6. Documentation Updates

None for this task. Stream-level `is_sorted` is documented in task 06 (README and/or meltano.yml).
