# Component: restful_api_tap

## Metadata

| Field | Value |
|-------|--------|
| Version | 1.0 |
| Last Updated | 2025-03-10 |
| Tags | restful_api_tap, restful-api-tap, component, singer, meltano-sdk, rest-api, streams, client, auth, pagination |
| Cross-References | [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) (architecture), [AI_CONTEXT_QUICK_REFERENCE.md](AI_CONTEXT_QUICK_REFERENCE.md) (commands, entry points), [AI_CONTEXT_PATTERNS.md](AI_CONTEXT_PATTERNS.md) (patterns) |

---

## Module Overview

The `restful_api_tap` package is the main Singer tap for generic REST APIs. Each module’s role:

| Module | Responsibility |
|--------|----------------|
| **tap.py** | Tap class; config schema; stream discovery; optional schema inference from sample API responses. |
| **streams.py** | `DynamicStream` — per-stream sync, URL/params, pagination strategy selection, post-processing (flatten). |
| **client.py** | `RestApiStream` — HTTP session, request/response handling, 404-as-end-of-stream on next-page. |
| **auth.py** | Authenticator selection and caching (API Key, Basic, Bearer, OAuth, AWS); `get_authenticator(self)`. |
| **pagination.py** | Custom paginators: page-number, offset, header-link, simple-offset; `has_more` / `get_next_url`. |
| **utils.py** | `flatten_json`, `unnest_dict`, `get_start_date` for schema inference, sync params, and pagination. |
| **__init__.py** | Package marker (no public exports). |

---

## Public Interfaces

### tap.py

- **RestfulApiTap(Tap)**  
  - `name = "restful-api-tap"`, `tap_name = name`.  
  - `_authenticator: Optional[APIAuthenticatorBase]` — cached authenticator for discovery and streams.  
  - **config_jsonschema** — top-level (`api_url`, auth, pagination, backoff, streams array) and stream-level (path, params, headers, `records_path`, keys, `schema`, `num_inference_records`, etc.).  
  - **discover_streams() → List[DynamicStream]**  
    - Iterates `config["streams"]`, merges stream vs top-level settings, resolves schema (file path, inline dict, or `get_schema()`), instantiates `DynamicStream` per stream with shared `_authenticator`.  
  - **get_schema(records_path, except_keys, inference_records, path, params, headers, flatten_records=False) → dict**  
    - If auth set, calls `get_authenticator(self)` (caches `_authenticator`). GET to `api_url + path`, extracts records via `records_path`. When `flatten_records` is true, flattens samples then infers; when false, infers from nested records. Uses `genson.SchemaBuilder` (and optional `_sdc_raw_json` when flattening). Raises `ValueError` on invalid response or non-dict record.

### streams.py

- **DynamicStream(RestApiStream)**  
  - Constructor: `tap`, `name`, `records_path`, `path`, `params`, `headers`, `primary_keys`, `replication_key`, `except_keys`, `next_page_token_path`, `schema`, `pagination_request_style`, `pagination_response_style`, pagination params, `start_date`, `source_search_field`, `source_search_query`, `use_request_body_not_params`, backoff params, `store_raw_json_message`, `flatten_records`, `authenticator`.  
  - **get_new_paginator()** — Returns paginator by `pagination_request_style`: `default`/`jsonpath_paginator`, `simple_header_paginator`, `header_link_paginator`, `restapi_header_link_paginator`, `style1`/`offset_paginator`, `hateoas_paginator`, `single_page_paginator`, `page_number_paginator`, `simple_offset_paginator`. Raises `ValueError` for unknown style.  
  - **get_url_params** / **prepare_request_payload** — Selected by `pagination_response_style` (`style1`, `offset`, `page`, `header_link`, `hateoas_body`); inject replication/since and pagination params; default `_get_url_params_page_style`.  
  - **parse_response(response) → Iterable[dict]** — Uses `records_path` (JSONPath) to yield raw records.  
  - **post_process(row, context) → Optional[dict]** — When `flatten_records` is true, returns `flatten_json(row, except_keys, store_raw_json_message)`; when false, returns row unchanged.  
  - **backoff_wait_generator()** — `message` or `header` backoff from config; else SDK default.

### client.py

- **RestApiStream(RESTStream)**  
  - **url_base** — `config["api_url"]`.  
  - **authenticator** — Calls `get_authenticator(self)`; returns cached `_authenticator`.  
  - **_request(prepared_request, context) → requests.Response** — Sends via authenticator and session; if `_is_next_page_request` and status 404, returns response without raising; else `validate_response(response)`.  
  - **request_records(context) → Iterator[dict]** — Paginator loop; on 404 breaks and yields only prior pages; otherwise parse_response → yield records and advance paginator.

### auth.py

- **get_authenticator(self)** — Reads `auth_method` from config (tap or stream); caches `_authenticator` on `self`; OAuth checks token validity and refreshes; AWS sets `http_auth`. Returns SDK authenticator or `APIAuthenticatorBase` when no auth.  
- **select_authenticator(self)** — Maps `auth_method` to `APIKeyAuthenticator`, `BasicAuthenticator`, `ConfigurableOAuthAuthenticator`, `BearerTokenAuthenticator`, or AWS (`AWSConnectClient` + `AWS4Auth`). Uses `api_keys`, `username`/`password`, OAuth params, `bearer_token`, `aws_credentials`. Raises `ValueError` for unknown method.  
- **ConfigurableOAuthAuthenticator** — `oauth_request_body` from config; `get_initial_oauth_token` for discovery.  
- **AWSConnectClient** — Builds boto3 session and `AWS4Auth` from config/env; `get_awsauth()`, `get_aws_session_client()`.

### pagination.py

- **RestAPIBasePageNumberPaginator** — `has_more(response)` from JSONPath or `hasMore`.  
- **RestAPIOffsetPaginator** — Offset/limit; `has_more` from response pagination object and `pagination_total_limit_param`.  
- **SimpleOffsetPaginator** — `has_more` by comparing record count (optional `offset_records_jsonpath`) to page size.  
- **RestAPIHeaderLinkPaginator** — Link header "next"; optional results limit and `use_fake_since_parameter` for replication_key-based early exit; `get_next_url(response)`.

### utils.py

- **flatten_json(obj, except_keys=None, store_raw_json_message=False) → dict** — Recursive flatten; lists and `except_keys` become JSON strings; keys normalized (`-.` → `__`); optional `_sdc_raw_json`.  
- **unnest_dict(d) → dict** — Single-level flatten of nested dicts (pagination).  
- **get_start_date(self, context) → Any** — Bookmark timestamp formatted or replication key value; fallback to `start_date`-derived value.

---

## Lifecycle / Entry Points

- **CLI:** `restful-api-tap` → `restful_api_tap.tap:RestfulApiTap.cli` (in `pyproject.toml`). Singer usage: `--config` (config file), `--catalog`, `--state` (state file), `--discover`.
- **Discovery:** Tap loads config file → `discover_streams()` builds catalog (list of `DynamicStream`); per stream, schema from file/dict or `get_schema(..., flatten_records)` (GET + optional flatten + genson). Authenticator obtained once and cached in `_authenticator`. Output is catalog (streams with SCHEMA).
- **Sync:** For each stream, `request_records(context)` uses `get_new_paginator()` → prepare_request (auth, replication key/bookmarks, pagination) → `_request` → `parse_response` → `post_process` (flatten if `flatten_records` true, else row unchanged) → emit RECORD/STATE messages. 404 on next-page ends stream without raising.

---

## Extension Points

- **Stream discovery:** Override `discover_streams()` to change stream list or config resolution.  
- **Schema:** Provide `schema` (path or object) on a stream to skip inference; or extend `get_schema()` for custom inference.  
- **Auth:** In `auth.select_authenticator()`, add a branch for a new `auth_method` and return an SDK-compatible authenticator.  
- **Pagination:** In `DynamicStream.get_new_paginator()`, add a branch for a new `pagination_request_style` and return a paginator (e.g. subclass of `BaseOffsetPaginator`/`BasePageNumberPaginator`/`HeaderLinkPaginator` with `current_value`, `advance()`, `finished`). Optionally add a `get_url_params`/`prepare_request_payload` style in streams (e.g. in the `get_url_params_styles` dict).  
- **Backoff:** `DynamicStream.backoff_wait_generator()` supports `message` and `header`; extend for other response shapes.  
- **Post-processing:** Override `DynamicStream.post_process()` (e.g. after `super()`) to add or transform fields.  
- **HTTP behaviour:** `RestApiStream._request()` and `request_records()` are the extension points for custom HTTP/404 handling.

---

## Examples

**Discover and run tap (CLI; config file + optional catalog/state file):**

```bash
uv run restful-api-tap --config config.json --discover > catalog.json
uv run restful-api-tap --config config.json --catalog catalog.json
```

**Stream config (schema from inference):**

```json
{
  "streams": [
    {
      "name": "users",
      "path": "/users",
      "records_path": "$.items[*]",
      "primary_keys": ["id"],
      "replication_key": "updated_at"
    }
  ]
}
```

**Using flatten and start date in code:**

```python
from restful_api_tap.utils import flatten_json, get_start_date

flat = flatten_json({"a": {"b": 1}, "c": [1, 2]}, except_keys=["c"])
# flat["a_b"] == 1, flat["c"] == "[1, 2]"

# get_start_date(stream, context) used inside stream's get_url_params/prepare_request_payload
```

**Custom paginator style (conceptual):**

In `streams.py` `get_new_paginator()`, add e.g.:

```python
elif self.pagination_request_style == "my_cursor_paginator":
    return MyCursorPaginator(next_cursor_path=self.next_page_token_jsonpath)
```

Implement `MyCursorPaginator` with `current_value`, `advance(resp)`, and `finished`.

---

*End of document. For repository layout and data flow see [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md). For commands see [AI_CONTEXT_QUICK_REFERENCE.md](AI_CONTEXT_QUICK_REFERENCE.md).*
