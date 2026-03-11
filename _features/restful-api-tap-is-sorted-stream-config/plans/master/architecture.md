# Master Plan — Architecture: Stream-level `is_sorted` config

**Feature:** restful-api-tap is_sorted stream config

---

## Design Summary

The feature extends the tap’s existing config → discovery → stream pipeline with a single boolean stream-level option. No new modules or classes; three existing touchpoints are updated so the SDK’s built-in `is_sorted` handling is honoured when the consumer opts in.

---

## Component Breakdown

### 1. Plugin definition (`taps/restful-api-tap/meltano.yml`)

- **Role:** Declare `is_sorted` as a stream-level setting so Meltano projects can set it under `config.streams[]`.
- **Change:** One new entry in `settings` (e.g. after `source_search_query`): `name: is_sorted`, `kind: boolean`.
- **Pattern:** Same as other stream-level settings (e.g. `replication_key`, `source_search_field`); see [AI_CONTEXT_PATTERNS.md](../../../docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md) “How do I add a new tap config property”.

### 2. Tap config schema and discovery (`restful_api_tap/tap.py`)

- **common_properties:** Add one `th.Property("is_sorted", th.BooleanType(), default=False, required=False, description=...)`. Config validation remains “load into SDK schema”; no new models.
- **discover_streams():** For each stream, resolve `is_sorted = stream.get("is_sorted", False)` and pass `is_sorted=is_sorted` into `DynamicStream(...)`.
- **Data flow:** Config file (or Meltano-injected config) → `config["streams"]` → per-stream dict → `DynamicStream` constructor. No change to schema inference, auth, or other stream keys.

### 3. DynamicStream (`restful_api_tap/streams.py`)

- **__init__:** Add parameter `is_sorted: Optional[bool] = False` (with other optional params). After `super().__init__(...)` and existing attribute assignments, set `self.is_sorted = is_sorted`.
- **Behaviour:** The Singer SDK already reads `stream.is_sorted` for incremental replication and state handling; setting the instance attribute is sufficient. No change to `get_new_paginator`, `get_url_params`, `post_process`, or `parse_response`.

---

## Data Flow

```
Config (streams[].is_sorted)
    → discover_streams() reads stream.get("is_sorted", False)
    → DynamicStream(..., is_sorted=is_sorted)
    → self.is_sorted = is_sorted on stream instance
    → SDK uses stream.is_sorted for resumable state when sync is interrupted
```

State and bookmarks remain unchanged; the SDK continues to manage resumable vs non-resumable state based on `is_sorted`.

---

## Design Patterns

- **Config resolution:** Stream-level override only (no top-level default for `is_sorted` in this feature); consistent with “stream-level overwrites” for other options (see [AI_CONTEXT_PATTERNS.md](../../../docs/AI_CONTEXT/AI_CONTEXT_PATTERNS.md)).
- **Stream construction:** Explicit kwargs from resolved config (see [AI_CONTEXT_restful-api-tap.md](../../../docs/AI_CONTEXT/AI_CONTEXT_restful-api-tap.md)); no global state.
- **Dependency injection:** No new external services; config is already injected via Tap/stream constructors.

---

## Out of Scope

- No change to targets, state backends, or pipeline orchestration.
- No change to auth, pagination, or record parsing.
- No new CLI flags or environment variables.
