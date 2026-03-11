# Feature request: Stream-level `is_sorted` config for resumable incremental syncs

**Plugin:** restful-api-tap (taps/restful-api-tap)  
**Requested by:** Consumers using incremental replication with cursor/sequence_id (e.g. Stella Connect extraction)  
**Status:** Request

---

## Summary

Add support for a stream-level **`is_sorted`** configuration option so that when the source API returns records ordered by the replication key (e.g. `sequence_id`), the tap can declare the stream as sorted. This enables the Singer SDK to treat progress as **resumable** if a sync is interrupted (e.g. cancel and resume).

Without this, the tap always leaves the SDK default `is_sorted = False`, so the SDK logs: *"Stream is assumed to be unsorted, progress is not resumable if interrupted"* and does not promote bookmarks to resumable state.

---

## Motivation

- Many REST APIs return paginated results **ordered by** the replication key (e.g. `sequence_id` or `created_at`). In that case, "last seen" replication key value is a valid high-water mark and sync progress can be safely resumed after interruption.
- The [Meltano Singer SDK](https://sdk.meltano.com/en/latest/incremental_replication.html) supports this via the stream attribute **`is_sorted`**: when `True`, the SDK treats the stream as sorted by the replication key and allows resumable state; when `False` (default), progress is not resumable.
- Today, restful-api-tap does **not** read `is_sorted` from stream config and does not set it on `DynamicStream`, so consumers cannot enable resumability even when their API guarantees order. Run-to-run incremental (next run continues from bookmark) still works; **in-run** resumability (cancel and resume the same run) does not.

---

## Current behaviour

- In `tap.py`, `discover_streams()` reads many stream keys (`replication_key`, `source_search_field`, `source_search_query`, etc.) but never reads `is_sorted`.
- `DynamicStream` in `streams.py` has no `is_sorted` parameter; the stream always keeps the SDK default `is_sorted = False`.
- The plugin’s `meltano.yml` does not list `is_sorted` as a stream-level setting.

Consumers may already set `is_sorted: true` in their project’s `meltano.yml` under `config.streams[]`; that value is ignored by the tap.

---

## Proposed solution

### 1. Plugin schema (meltano.yml)

In `taps/restful-api-tap/meltano.yml`, add a stream-level setting alongside `replication_key`, `source_search_field`, etc.:

```yaml
- name: is_sorted
  kind: boolean
```

### 2. Tap config schema (tap.py)

In **common_properties**, add:

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

In **discover_streams()**, read the value and pass it to `DynamicStream`:

```python
is_sorted = stream.get("is_sorted", False)
# ...
streams.append(
    DynamicStream(
        # ...existing args...
        is_sorted=is_sorted,
    )
)
```

### 3. DynamicStream (streams.py)

- Add to `__init__` signature: `is_sorted: Optional[bool] = False`.
- After `super().__init__(...)`, set: `self.is_sorted = is_sorted`.

The Singer SDK accepts `is_sorted` as a stream attribute (class or instance); setting it on the instance is sufficient for resumable state.

---

## Acceptance criteria

- [ ] Stream-level config key `is_sorted` is documented in the plugin (meltano.yml and/or README).
- [ ] When `is_sorted: true` is set for a stream, the tap passes it to the stream instance so that `stream.is_sorted` is `True`.
- [ ] With `is_sorted: true` and incremental replication (replication_key + source_search_field + source_search_query), an interrupted sync is reported as resumable and a subsequent run continues from the bookmark without re-processing from the start.
- [ ] Default remains `False` when `is_sorted` is omitted (backward compatible).

---

## References

- [Singer SDK – Incremental replication](https://sdk.meltano.com/en/latest/incremental_replication.html) (is_sorted and resumability)
- [Meltano state backends](https://docs.meltano.com/concepts/state_backends/) (state storage)
- Consumer projects using this pattern: incremental replication with `replication_key`, `source_search_field`, `source_search_query`, and (once supported) `is_sorted` for APIs that return data ordered by the replication key (e.g. sequence_id + `after` param).
