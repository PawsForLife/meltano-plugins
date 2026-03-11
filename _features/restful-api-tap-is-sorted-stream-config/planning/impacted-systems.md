# Impacted systems: `is_sorted` stream config

**Feature:** Stream-level `is_sorted` config for resumable incremental syncs  
**Plugin:** restful-api-tap (`taps/restful-api-tap`)

---

## Summary

This feature touches the tap’s config schema, stream discovery, and the dynamic stream class. No new modules or external systems are introduced; existing behaviour is extended so the tap can declare streams as sorted when the source API returns records ordered by the replication key.

---

## Impacted modules and interfaces

### 1. `taps/restful-api-tap/restful_api_tap/tap.py`

- **`common_properties`**  
  Add a stream-level property `is_sorted` (Boolean, default `False`, optional) so config/UI can pass the value. No other properties are removed or changed.

- **`discover_streams()`**  
  Read `is_sorted` from each stream entry in `config["streams"]` (with fallback to `False`) and pass it into the `DynamicStream` constructor. No change to schema inference, auth, or other stream keys.

- **`RestfulApiTap`**  
  No change to tap name, capabilities, or top-level config; only stream-level schema and discovery logic are extended.

### 2. `taps/restful-api-tap/restful_api_tap/streams.py`

- **`DynamicStream.__init__`**  
  Add an optional parameter `is_sorted: Optional[bool] = False`. After `super().__init__(...)`, set `self.is_sorted = is_sorted` so the Meltano Singer SDK uses it for resumable state (the SDK already supports this attribute on stream instances).

- **`DynamicStream`**  
  No change to pagination, URL params, `post_process`, or record emission; only the new constructor argument and instance attribute are added.

### 3. `taps/restful-api-tap/meltano.yml`

- **`settings` (stream-level)**  
  Add a stream-level setting for `is_sorted` (e.g. `kind: boolean`) so Meltano projects can configure it under `config.streams[]`. No change to extractor name, executable, or capabilities.

---

## Impacted functionality

| Area | Current behaviour | Change |
|------|-------------------|--------|
| Stream config schema | No `is_sorted`; value in meltano.yml is ignored. | Schema and discovery accept and pass `is_sorted`. |
| Incremental sync | Run-to-run resume from bookmark works; in-run resume is not declared resumable. | When `is_sorted: true`, stream is declared sorted and in-run resume is resumable (SDK behaviour). |
| Default | N/A | Default remains `False` when `is_sorted` is omitted (backward compatible). |

---

## Dependencies

- **Meltano Singer SDK**  
  Relies on existing stream attribute `is_sorted` and incremental replication behaviour; no SDK code changes.

- **State / bookmarks**  
  No change to state shape or bookmark format; the SDK continues to manage resumable vs non-resumable state based on `is_sorted`.

---

## Out of scope

- No change to targets, state backends, or pipelines.
- No change to auth, pagination, or record parsing.
- No new CLI flags or environment variables.
