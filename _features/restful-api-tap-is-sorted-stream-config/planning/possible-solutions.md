# Possible solutions: `is_sorted` stream config

**Feature:** Stream-level `is_sorted` config for resumable incremental syncs

---

## Problem

When the source API returns records ordered by the replication key (e.g. `sequence_id`), the tap could declare the stream as sorted so that interrupted syncs are resumable. Today the tap does not read or set `is_sorted`, so the SDK keeps the default `is_sorted = False` and does not treat progress as resumable.

---

## Option 1: Internal — stream-level config and wire to SDK (recommended)

**Approach:** Add `is_sorted` as a stream-level setting in the tap config and in `meltano.yml`. In `discover_streams()`, read it and pass it into `DynamicStream`; in `DynamicStream.__init__`, set `self.is_sorted = is_sorted`. Rely on the existing Meltano Singer SDK behaviour for resumable state when `is_sorted` is true.

**Pros:**

- Uses existing SDK support; no new libraries or runtime behaviour.
- Backward compatible: default `False` when omitted.
- Per-stream control: only streams whose API is sorted need it.
- Aligns with feature request and documented SDK usage.

**Cons:**

- None significant; small, localized code changes.

---

## Option 2: Internal — hardcode `is_sorted = True` for all streams

**Approach:** Set `self.is_sorted = True` in `DynamicStream` for every stream, with no config.

**Pros:**

- Minimal code change.

**Cons:**

- Wrong for streams whose API does not return records ordered by the replication key; SDK may raise if records are out of order, and claiming resumability when data is unsorted is unsafe.
- Not backward compatible for existing unsorted streams.
- Does not meet the requirement for a configurable, stream-level option.

**Verdict:** Rejected.

---

## Option 3: No change (current behaviour)

**Approach:** Leave the tap as-is. Consumers rely only on run-to-run resume (next run continues from bookmark); in-run resume (cancel and resume the same run) remains non-resumable.

**Pros:**

- No implementation effort.

**Cons:**

- Does not satisfy the feature request; consumers with sorted APIs cannot enable resumability.

**Verdict:** Rejected.

---

## External libraries

The behaviour required is: *declare a stream as sorted so incremental sync state is resumable when interrupted*. The Meltano Singer SDK already implements this via the stream attribute `is_sorted` and its incremental replication and state handling. No third-party library is needed to “add” resumability; the tap only needs to expose the existing SDK option via config.

Research (SDK docs, incremental replication page) confirms:

- `is_sorted = True` on a stream enables resumable state when the stream uses incremental replication.
- The SDK documents this and uses it for state/bookmark handling.
- No separate plugin or library provides this; it is built into the SDK.

**Conclusion:** An internal solution (Option 1) that wires a new stream-level config through to the existing SDK attribute is the correct approach. No external library is required.
