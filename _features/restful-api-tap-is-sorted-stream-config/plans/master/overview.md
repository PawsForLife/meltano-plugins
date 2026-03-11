# Master Plan — Overview: Stream-level `is_sorted` config

**Feature:** restful-api-tap is_sorted stream config  
**Plan location:** `_features/restful-api-tap-is-sorted-stream-config/plans/master/`

---

## Purpose

Enable stream-level configuration of **`is_sorted`** so that when the source REST API returns records ordered by the replication key (e.g. `sequence_id` or `created_at`), the tap can declare the stream as sorted. The Meltano Singer SDK then treats incremental sync progress as **resumable** if a sync is interrupted (e.g. cancel and resume the same run).

Today the tap does not read or set `is_sorted`; the SDK keeps the default `is_sorted = False`, so in-run resumability is not declared even when the API guarantees order.

---

## Objectives

1. **Schema:** Add `is_sorted` (boolean, default `False`, optional) to tap config (stream-level) and plugin definition (`meltano.yml`).
2. **Wiring:** Read `is_sorted` in `discover_streams()` and pass it into `DynamicStream`; set `self.is_sorted` on the stream instance so the SDK’s existing resumability behaviour applies.
3. **Compatibility:** Default remains `False` when omitted; no change to state shape, bookmarks, or other streams.

---

## Success Criteria

- Stream-level config key `is_sorted` is documented (meltano.yml and/or README).
- When `is_sorted: true` is set for a stream, the discovered stream instance has `stream.is_sorted is True`.
- With `is_sorted: true` and incremental replication (replication_key + source_search_field + source_search_query), an interrupted sync is reported as resumable and a subsequent run continues from the bookmark.
- When `is_sorted` is omitted or false, stream has `is_sorted is False` (backward compatible).

---

## Key Requirements and Constraints

- **Scope:** restful-api-tap only; no changes to target-gcs, state backends, or Meltano core.
- **No new dependencies:** Use existing Singer SDK stream attribute `is_sorted`; no new libraries.
- **Config surface:** Stream-level only; no new env vars or CLI flags.
- **Validation:** Rely on SDK schema validation; no new Pydantic/dataclass models (per project patterns, config uses Singer SDK typing).

---

## Relationship to Existing Systems

- **Tap config:** Extends existing stream-level properties in `common_properties` and `discover_streams()` (see [interfaces.md](interfaces.md)).
- **DynamicStream:** Adds one optional constructor argument and one instance attribute; no change to pagination, URL params, or record emission (see [architecture.md](architecture.md)).
- **SDK:** Consumes existing `is_sorted` behaviour; no SDK code changes.

---

## References

- Feature file: `_features/restful-api-tap-is-sorted-stream-config.md`
- Planning: `_features/restful-api-tap-is-sorted-stream-config/planning/selected-solution.md`
- SDK: [Meltano Singer SDK – Incremental replication](https://sdk.meltano.com/en/latest/incremental_replication.html) (is_sorted and resumability)
