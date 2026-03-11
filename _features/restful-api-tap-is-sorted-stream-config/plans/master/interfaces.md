# Master Plan — Interfaces: Stream-level `is_sorted` config

**Feature:** restful-api-tap is_sorted stream config

---

## Config Schema (tap.py)

### common_properties

**Add one property:**

| Name       | Type            | Default | Required | Description |
|-----------|------------------|--------|----------|-------------|
| `is_sorted` | BooleanType()  | `False` | No       | When true, the stream is declared sorted by replication_key; enables resumable state if the sync is interrupted. |

**Signature (conceptual):** Append to existing `th.PropertiesList` in `common_properties`:

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

**Contract:** If present in `config["streams"][i]`, the value is a boolean; if omitted, treat as `False`. Validation is via SDK schema load; no extra runtime checks.

---

## discover_streams() (tap.py)

**Change:** Resolve `is_sorted` per stream and pass to `DynamicStream`.

- **Read:** `is_sorted = stream.get("is_sorted", False)` (stream-level only).
- **Pass:** Add keyword argument `is_sorted=is_sorted` to the `DynamicStream(...)` constructor call (e.g. after `source_search_query=source_search_query`, before `use_request_body_not_params` or `authenticator`).

**Contract:** Every constructed `DynamicStream` receives an `is_sorted` value; default is `False` when key is missing.

---

## DynamicStream.__init__ (streams.py)

**New parameter:**

| Parameter   | Type              | Default | Description |
|------------|--------------------|--------|-------------|
| `is_sorted` | `Optional[bool]`  | `False` | When True, stream is declared sorted by replication_key for SDK resumability. |

**Placement:** Add with other optional parameters (e.g. after `flatten_records`, before `authenticator`).

**New attribute:** After `super().__init__(...)` and existing assignments (e.g. after `self.flatten_records = flatten_records`), set:

```python
self.is_sorted = is_sorted
```

**Contract:** The SDK reads `stream.is_sorted`; the instance must expose it as a boolean. Callers pass the value from config; no conversion beyond `stream.get("is_sorted", False)`.

---

## meltano.yml (plugin schema)

**New setting (stream-level):**

```yaml
- name: is_sorted
  kind: boolean
```

**Placement:** Under `settings`, with other stream-level settings (e.g. after `source_search_query`).

**Contract:** Meltano and the tap accept `is_sorted` in stream config; type is boolean; no new top-level or capability changes.

---

## Dependencies Between Interfaces

- **meltano.yml** → defines allowed config surface for the plugin.
- **common_properties** → defines tap config schema; must include `is_sorted` for validation and discovery.
- **discover_streams()** → reads from config and calls **DynamicStream(__init__)** with `is_sorted`.
- **DynamicStream** → exposes `self.is_sorted` for the SDK; no other modules depend on it directly.

---

## Glossary

Terms (tap, stream, config file, state file, Catalog, replication key) follow [GLOSSARY_MELTANO_SINGER.md](../../../docs/AI_CONTEXT/GLOSSARY_MELTANO_SINGER.md).
