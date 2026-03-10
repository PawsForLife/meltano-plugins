# AI Context — restful-api-tap Component

## Metadata

| Field | Value |
|-------|--------|
| Version | 1.1 |
| Last Updated | 2026-03-11 |
| Tags | restful-api-tap, singer, tap, REST, extractor, meltano, streams, discovery, replication |
| Cross-References | [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) (architecture, data flow), [AI_CONTEXT_QUICK_REFERENCE.md](AI_CONTEXT_QUICK_REFERENCE.md) (commands, troubleshooting), [AI_CONTEXT_PATTERNS.md](AI_CONTEXT_PATTERNS.md) (code patterns), [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md) (tap, streams, SCHEMA/RECORD/STATE, config file, state file, Catalog, Discovery, replication), [AI_CONTEXT_target-gcs.md](AI_CONTEXT_target-gcs.md) (downstream target) |

---

## Module Overview

| Module / File | Responsibility |
|---------------|----------------|
| `restful_api_tap/tap.py` | Tap class `RestfulApiTap`: config schema (`config_jsonschema`), stream discovery (`discover_streams`), schema inference (`get_schema`). Caches authenticator in `_authenticator`. Emits Singer SCHEMA, RECORD, STATE to stdout. |
| `restful_api_tap/streams.py` | `DynamicStream(RestApiStream)`: per-stream config (path, params, records_path, pagination, replication_key, flatten). `parse_response`, `post_process`, `get_new_paginator`, URL/body param builders (`_get_url_params_*`, `prepare_request_payload` when body). |
| `restful_api_tap/client.py` | `RestApiStream(RESTStream)`: base URL from config file (`api_url`), `authenticator` (calls `get_authenticator`), `_request` (404 on next-page → end-of-stream), `request_records` with pagination. |
| `restful_api_tap/auth.py` | `get_authenticator(self)`, `select_authenticator(self)`. `ConfigurableOAuthAuthenticator`, `AWSConnectClient`. Auth methods: `no_auth`, `api_key`, `basic`, `oauth`, `bearer_token`, `aws`. |
| `restful_api_tap/pagination.py` | Custom paginators: `RestAPIBasePageNumberPaginator`, `RestAPIOffsetPaginator`, `SimpleOffsetPaginator`, `RestAPIHeaderLinkPaginator`. |
| `restful_api_tap/utils.py` | `flatten_json(obj, except_keys, store_raw_json_message)`, `unnest_dict(d)`, `get_start_date(self, context)` for replication/since (bookmark or config file start_date). |

---

## Public Interfaces

### Entry Point

- **CLI:** `restful-api-tap` → `restful_api_tap.tap:RestfulApiTap.cli` (from `pyproject.toml`).

### Main Types

- **RestfulApiTap(Tap)** — `name = "restful-api-tap"`, `tap_name`, `_authenticator` (cached). Config: `config_jsonschema` (top-level + common + stream-level properties).
- **DynamicStream(RestApiStream)** — Stream implementation: `name`, `path`, `params`, `headers`, `records_path`, `primary_keys`, `replication_key`, `except_keys`, pagination/replication/flatten options, `authenticator`. Emits SCHEMA and RECORD messages for the stream.
- **RestApiStream(RESTStream)** — Base: `url_base` from `config["api_url"]`, `authenticator` (via `get_authenticator`), `_request`, `request_records`. 404 on next-page request is end-of-stream (no exception).

### Config Contract (summary)

- **Required:** `api_url`, `streams` (array of stream defs; each has `name`).
- **Top-level (examples):** `auth_method`, `api_keys`, `client_id`/`client_secret`, `username`/`password`, `bearer_token`, `refresh_token`, `grant_type`, `scope`, `access_token_url`, `redirect_uri`, `oauth_extras`, `oauth_expiration_secs`, `aws_credentials`; `next_page_token_path`, `pagination_request_style`, `pagination_response_style`, `use_request_body_not_params`; `backoff_type`, `backoff_param`, `backoff_time_extension`; `store_raw_json_message`, `flatten_records`; `pagination_page_size`, `pagination_results_limit`, `pagination_next_page_param`, `pagination_limit_per_page_param`, `pagination_total_limit_param`, `pagination_initial_offset`; `offset_records_jsonpath`; `discovery_request_limit`, `discovery_limit_param`.
- **Per-stream (merge with top-level):** `name`, `path`, `params`, `headers`, `records_path`, `primary_keys`, `replication_key`, `except_keys`, `num_inference_records`, `start_date`, `source_search_field`, `source_search_query`, `schema` (path string, dict, or omitted for inference), `flatten_records`.

### Key Methods

- **RestfulApiTap.discover_streams()** → `List[DynamicStream]`: Builds one `DynamicStream` per config stream; resolves schema from file, dict, or `get_schema(...)` (Discovery).
- **RestfulApiTap.get_schema(records_path, except_keys, inference_records, path, params, headers, flatten_records)** → schema dict: Uses config file auth (and optional `discovery_request_limit`), GETs sample, infers via genson; `flatten_records` controls whether sample is flattened before inference. Used for SCHEMA messages and Catalog.
- **DynamicStream.parse_response(response)** → iterable of dicts: `extract_jsonpath(records_path, response.json())`.
- **DynamicStream.post_process(row, context)** → dict or None: If `flatten_records` true, returns `flatten_json(row, except_keys, store_raw_json_message)`; else returns row (optionally adding `_sdc_raw_json` by reference). Result is emitted as RECORD message payload.
- **RestApiStream.request_records(context)** → iterator of dicts: Paginator loop; `prepare_request` (params or body via `get_url_params` / `prepare_request_payload` when `use_request_body_not_params`) → `_request`; 404 on next-page stops without raising; yields from `parse_response`; SDK applies `post_process` when writing RECORD messages. State (bookmarks) updated per stream.

---

## Lifecycle / Entry Points

1. **Invocation:** Meltano or CLI runs `restful-api-tap` with `--config <path>` (config file) and optional `--state` (state file), `--catalog` (catalog). Config can be from file or Meltano-injected.
2. **Discovery:** Tap loads config; `discover_streams()` builds `DynamicStream` list. Schema per stream: from file path, from dict, or inferred via `get_schema` (auth resolved once, cached in `_authenticator`). Output is a Catalog (streams + schemas) to stdout.
3. **Sync:** For each selected stream, SDK drives `request_records(context)`: paginator → prepare_request (params or body by `pagination_response_style` and `use_request_body_not_params`) → `_request` (auth via `authenticator`; 404 on next-page → end-of-stream) → `parse_response` → records yielded; SDK applies `post_process` when writing RECORD messages. Bookmarks (state) updated per stream; STATE messages emitted to stdout.
4. **Output:** Singer JSONL (SCHEMA, RECORD, STATE) to stdout; typically piped to a target (e.g. target-gcs).

---

## Extension Points

- **New stream:** Add entry to `config["streams"]` with `name`, `path`, and optionally `schema`, `records_path`, `primary_keys`, `replication_key`, etc. No code change if existing config and pagination styles suffice.
- **New auth method:** In `auth.py`, extend `select_authenticator(self)` for a new `auth_method` value; return an `APIAuthenticatorBase` (or set `self.http_auth` for request-level auth). Register any new config in `tap.py` `top_level_properties`.
- **New pagination style:** In `pagination.py` add a paginator class (e.g. subclass `BaseOffsetPaginator`/`BasePageNumberPaginator`/`HeaderLinkPaginator`); in `streams.py` add a branch in `get_new_paginator()` for a new `pagination_request_style` and, if needed, a new `_get_url_params_*` or body builder; register in `get_url_params_styles` (and `prepare_request_payload` when `use_request_body_not_params` is true).
- **New top-level or stream-level setting:** Add `th.Property` in `tap.py` (`top_level_properties` or `common_properties`/stream schema); in `discover_streams()` read and pass into `DynamicStream(...)`; use in stream logic (e.g. `get_url_params`, `post_process`).

---

## Examples

### Minimal config (single stream, schema inferred)

```json
{
  "api_url": "https://api.example.com",
  "streams": [
    {
      "name": "items",
      "path": "/items",
      "records_path": "$.items[*]",
      "primary_keys": ["id"]
    }
  ]
}
```

### Stream with INCREMENTAL replication and HATEOAS-style pagination (from config.sample.json)

```json
{
  "api_url": "https://myexample_fhir_api_url/base_folder",
  "pagination_request_style": "jsonpath_paginator",
  "pagination_response_style": "hateoas_body",
  "next_page_token_path": "$.link[?(@.relation=='next')].url",
  "streams": [
    {
      "name": "my_sample_table_name",
      "path": "/ExampleService",
      "records_path": "$.entry[*].resource",
      "primary_keys": ["id"],
      "replication_key": "meta_lastUpdated",
      "start_date": "2001-01-01T00:00:00.00+12:00",
      "source_search_field": "last-updated",
      "source_search_query": "gt$last_run_date"
    }
  ]
}
```

### Schema source options

- **Inferred (default):** Omit `schema`; tap calls source API and uses `get_schema(...)` with `records_path` and `num_inference_records`; optional `discovery_request_limit` limits that request.
- **From file:** `"schema": "path/to/schema.json"`.
- **From object:** `"schema": { "type": "object", "properties": { ... } }`.

### Flatten vs nested

- `flatten_records: true` — Schema inferred from flattened sample; `post_process` returns `flatten_json(row, except_keys, store_raw_json_message)`. Keys like `user_id`, `user_name` at root.
- `flatten_records: false` — Schema inferred from raw nested; `post_process` returns row unchanged (optional `_sdc_raw_json` by reference). Keys like `user.properties.id`.

### Pagination styles (pagination_request_style)

- `default` / `jsonpath_paginator` — next token from response via `next_page_token_path` (default `$.next_page`).
- `offset_paginator` / `style1` — offset/limit params; `pagination_total_limit_param` for total.
- `page_number_paginator` — page number; optional jsonpath for “has more”.
- `restapi_header_link_paginator` — GitHub-style Link header.
- `header_link_paginator` — SDK `HeaderLinkPaginator`.
- `simple_header_paginator` — e.g. `X-Next-Page`.
- `hateoas_paginator`, `single_page_paginator`, `simple_offset_paginator` — additional built-in options.

### 404 handling

- **First-page 404:** `_request` → `validate_response(response)` → fatal error.
- **Next-page 404:** `request_records` breaks the paginator loop and returns only records from previous pages (no exception). See `client.py` and `tests/test_404_end_of_stream.py`.

---

## Tests (reference)

- **test_tap.py:** Schema inference, schema from file/object, `flatten_records` in config schema, `get_schema` with `flatten_records` true/false, multiple streams.
- **test_streams.py:** `post_process` flatten vs nested, stream-level override of top-level `flatten_records`, pagination (default style).
- **test_core.py:** SDK standard tap test class with mocked API.
- **test_utils.py:** `flatten_json` and `except_keys`.
- **test_404_end_of_stream.py:** Initial 404 → `FatalAPIError`; next-page 404 → end-of-stream, only prior pages yielded.

Tests use `tests/test_streams.config()`, `json_resp()`, `url_path()`, `setup_api(requests_mock, ...)` for mocking.
