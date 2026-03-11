# Selected solution: internal — stream-level `is_sorted` config

**Feature:** Stream-level `is_sorted` config for resumable incremental syncs  
**Decision:** Internal solution; wire existing Meltano Singer SDK `is_sorted` behaviour through tap config.

---

## Overview

The Meltano Singer SDK already supports resumable incremental sync when a stream sets `is_sorted = True` and uses a replication key. The tap currently does not read `is_sorted` from config and does not set it on `DynamicStream`, so the SDK keeps the default `is_sorted = False`. The solution is to add a stream-level config key, read it in discovery, pass it into the stream constructor, and set the instance attribute so the SDK’s existing logic applies.

---

## SDK behaviour (no tap changes to SDK)

- **Incremental replication:** [SDK – Incremental Replication](https://sdk.meltano.com/en/latest/incremental_replication.html) documents that when `is_sorted` is true and the stream uses a replication key, the sync is resumable if interrupted; otherwise progress is not resumable until the stream completes.
- **Stream attribute:** Streams may set `is_sorted` as a class or instance attribute; the SDK uses it for state handling. Setting it on the instance in `DynamicStream` is sufficient.
- **Validation:** If `is_sorted` is true and records arrive out of order by the replication key, the SDK can raise; therefore the tap must only set `is_sorted = True` when the consumer has configured it (i.e. when the source API is known to return records ordered by the replication key).

---

## Implementation guide

### 1. Plugin schema — `taps/restful-api-tap/meltano.yml`

Add one stream-level setting (e.g. under the existing `settings` that include `replication_key`, `source_search_field`, etc.):

```yaml
- name: is_sorted
  kind: boolean
```

No new top-level settings or capabilities are required.

### 2. Tap config schema — `restful_api_tap/tap.py`

- **common_properties:** Append a property:

  - Name: `is_sorted`
  - Type: `th.BooleanType()`
  - Default: `False`
  - Required: `False`
  - Description: When true, the stream is declared sorted by the replication key; enables resumable state if the sync is interrupted.

- **discover_streams():**
  - Resolve `is_sorted` from each stream dict: `is_sorted = stream.get("is_sorted", False)` (and optionally from `self.config.get("is_sorted", False)` if a top-level default is desired; the feature specifies stream-level only, so stream-level is sufficient).
  - Add `is_sorted=is_sorted` to the `DynamicStream(...)` constructor call.

### 3. DynamicStream — `restful_api_tap/streams.py`

- **`__init__`:** Add parameter `is_sorted: Optional[bool] = False` (with other optional params).
- **After `super().__init__(...)`:** Set `self.is_sorted = is_sorted`.

No change to `get_new_paginator`, `get_url_params`, `post_process`, or `parse_response`. No new methods.

### 4. Tests (TDD)

- Test that when a stream config includes `is_sorted: true`, the discovered stream instance has `is_sorted is True`.
- Test that when `is_sorted` is omitted or false, the stream has `is_sorted is False`.
- Optionally: integration-style test that with `is_sorted: true` and incremental config, state is treated as resumable (e.g. bookmark promoted); can rely on SDK tests for full resumability behaviour if preferred.

### 5. Documentation

- **README and/or meltano.yml comments:** Document that `is_sorted` is a stream-level option; when true, the stream is declared sorted by the replication key so that interrupted syncs are resumable, and that the source API must return records ordered by that key.

---

## Interfaces summary

| Location            | Change |
|---------------------|--------|
| `common_properties` | Add `is_sorted` (Boolean, default False). |
| `discover_streams()` | Read `stream.get("is_sorted", False)`; pass to `DynamicStream(..., is_sorted=is_sorted)`. |
| `DynamicStream.__init__` | New parameter `is_sorted`; set `self.is_sorted = is_sorted`. |
| meltano.yml         | One new stream-level setting `is_sorted` (kind: boolean). |

---

## References

- [Meltano Singer SDK – Incremental replication](https://sdk.meltano.com/en/latest/incremental_replication.html) — `is_sorted` and resumability.
- [SDK implementation – State](https://sdk.meltano.com/en/latest/implementation/state.html) — state and bookmarks.
- Feature file: `_features/restful-api-tap-is-sorted-stream-config.md`.
