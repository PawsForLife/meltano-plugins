# Task 03: Add is_sorted to common_properties (tap.py)

## Background

The tap config schema in `tap.py` must include `is_sorted` so that config validation accepts the key and `discover_streams()` can read it. This task adds only the property to `common_properties`; wiring in `discover_streams()` is task 05. Depends on nothing; required before task 05 so the schema accepts the key.

## This Task

- **File:** `taps/restful-api-tap/restful_api_tap/tap.py`
- **Where:** Inside the `th.PropertiesList(...)` of `common_properties`, after the last property (e.g. after `source_search_query`-related or adjacent stream-level property, before the closing `)` of that list).
- **Change:** Append to the properties list:
  ```python
  th.Property(
      "is_sorted",
      th.BooleanType(),
      default=False,
      required=False,
      description="When true, the stream is declared sorted by replication_key; "
                  "enables resumable state if the sync is interrupted.",
  ),
  ```
- **Acceptance criteria:** `common_properties` includes `is_sorted` (BooleanType, default False, required False); validation remains via existing SDK schema load; no new Pydantic/dataclass.

## Testing Needed

- No new test file in this task. Task 01 tests will still fail until task 05 wires the value; after task 05, task 01 tests validate that the schema and discovery path work together.
