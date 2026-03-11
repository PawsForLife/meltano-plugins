# Master Plan — Implementation: Stream-level `is_sorted` config

**Feature:** restful-api-tap is_sorted stream config

---

## Implementation Order

Follow TDD and models-first where applicable. This feature has no new data models; config uses existing Singer SDK typing. Order:

1. **Tests first** — Add tests that assert discovered stream `is_sorted` from config (see [testing.md](testing.md)).
2. **Plugin schema** — Add `is_sorted` to `meltano.yml` so the config surface is declared.
3. **Tap config and discovery** — Add property to `common_properties`, then resolve and pass in `discover_streams()`.
4. **DynamicStream** — Add parameter and set `self.is_sorted`.
5. **Docs** — Update README and/or meltano.yml comments (see [documentation.md](documentation.md)).

---

## Files to Modify

### 1. `taps/restful-api-tap/meltano.yml`

- **Where:** Under `plugins.extractors.settings`, with other stream-level settings.
- **Change:** Add one entry after `source_search_query` (or adjacent stream-level setting):

```yaml
- name: is_sorted
  kind: boolean
```

---

### 2. `taps/restful-api-tap/restful_api_tap/tap.py`

**a. common_properties**

- **Where:** Inside the `th.PropertiesList(...)` of `common_properties`, before the closing `)` of that list (e.g. after the `source_search_query` property, around line 123).
- **Change:** Append:

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

**b. discover_streams()**

- **Where:** In the block that builds the `DynamicStream(...)` call (around lines 518–565).
- **Change:**
  - Before the `streams.append(DynamicStream(...))` block, resolve: `is_sorted = stream.get("is_sorted", False)` (reuse the same pattern as other stream-level keys, e.g. `flatten_records`).
  - Add to the `DynamicStream(...)` keyword arguments: `is_sorted=is_sorted` (e.g. after `source_search_query=source_search_query`, before `use_request_body_not_params`).

---

### 3. `taps/restful-api-tap/restful_api_tap/streams.py`

**a. DynamicStream.__init__**

- **Where:** In the parameter list of `__init__` (around lines 53–85).
- **Change:** Add parameter: `is_sorted: Optional[bool] = False` (e.g. after `flatten_records`, before `authenticator`).

**b. Docstring**

- **Where:** In the `Args` section of the same `__init__`.
- **Change:** Add: `is_sorted: when True, stream is declared sorted by replication_key for resumable state. Default False.`

**c. Instance attribute**

- **Where:** After existing attribute assignments (e.g. after `self.flatten_records = flatten_records`, around line 169).
- **Change:** Add: `self.is_sorted = is_sorted`.

---

## Code Organization

- No new modules or classes.
- No new helper functions; resolution is a single `stream.get("is_sorted", False)` in `discover_streams()`.
- Type hints: use `Optional[bool]` for `is_sorted` in `DynamicStream.__init__`; no new imports required.

---

## Dependency Injection

- Config is already supplied via Tap (config file / Meltano). No new injectables.
- `is_sorted` is passed explicitly into `DynamicStream` from resolved config; no globals or implicit state.

---

## Implementation Dependencies

| Step | Depends on |
|------|------------|
| Tests | Nothing (write first; they will fail until impl is done). |
| meltano.yml | Nothing. |
| common_properties | Nothing. |
| discover_streams() | common_properties (so schema accepts the key). |
| DynamicStream.__init__ | Nothing (can be done in parallel with tap.py after tests are written). |
| Documentation | All code changes (describe final behaviour). |

Recommended sequence: tests → meltano.yml → common_properties + discover_streams() + DynamicStream (then run tests) → documentation.
