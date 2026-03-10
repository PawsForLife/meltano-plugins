# AI Context — Patterns & Conventions

## Metadata

| Field | Value |
|-------|--------|
| Version | 1.0 |
| Last Updated | 2025-03-10 |
| Tags | patterns, conventions, TDD, typing, validation, testing |
| Cross-References | [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) (architecture), [AI_CONTEXT_QUICK_REFERENCE.md](AI_CONTEXT_QUICK_REFERENCE.md) (commands) |

---

## Code Organization

- **Package layout**: Single top-level package `restful_api_tap/` with flat modules: `tap.py`, `streams.py`, `client.py`, `auth.py`, `pagination.py`, `utils.py`. No `models/` subpackage; config and schema are expressed via Singer SDK types and dicts.
- **Naming**: Modules are lowercase with underscores; classes are PascalCase (`RestfulApiTap`, `DynamicStream`, `RestApiStream`). Test files mirror source with `test_<module>.py` (e.g. `tests/test_tap.py`, `tests/test_streams.py`).
- **Entry point**: Tap CLI is registered in `pyproject.toml` as `restful-api-tap = "restful_api_tap.tap:RestfulApiTap.cli"`; the Tap class lives in `restful_api_tap/tap.py`.
- **Dependencies between components**: `tap` → streams, auth, utils; `streams` → client, pagination, utils; `client` → auth. Utils and auth have no internal tap dependencies. See AI_CONTEXT_REPOSITORY.md for the full dependency table.

---

## Type & Model Patterns

- **Config schema**: The tap uses Singer SDK typing helpers in `restful_api_tap/tap.py`: `th.PropertiesList`, `th.Property`, `th.StringType`, `th.ArrayType`, etc. Top-level and stream-level config are defined there and merged at runtime in `discover_streams()`.
- **No Pydantic/dataclasses for API payloads**: Ingested API data is handled as plain dicts. Stream records come from `parse_response()` (JSONPath extraction). Flattening is conditional on `flatten_records`: when true, `post_process()` flattens via `flatten_json()`; when false, nested structure is preserved. Schema inference respects `flatten_records` (flatten samples then infer vs infer from nested).
- **Type hints**: All public functions and methods use annotations (e.g. `Optional[dict]`, `List[DynamicStream]`, `Iterator[dict]`, `requests.Response`). Parameters and return types are declared per project rules.

---

## Error Handling & Logging

- **HTTP responses**: The SDK’s `validate_response(response)` is used in `RestApiStream._request()` in `restful_api_tap/client.py`. A 404 on a **next-page** request is treated as end-of-stream: the response is returned without calling `validate_response`, and `request_records()` breaks and yields only prior pages. A 404 on the **initial** request still goes through `validate_response` and raises (e.g. `FatalAPIError`).
- **Schema inference**: In `get_schema()` in `restful_api_tap/tap.py`, a non-OK response leads to `self.logger.error(...)` and `raise ValueError(r.text)`. If a record is not a dict, the same pattern is used and `ValueError("Input must be a dict object.")` is raised.
- **Logging**: Uses `self.logger` (Singer SDK) for info/debug/error. Example: `self.logger.info("No schema found. Inferring schema from API call.")` and `self.logger.debug(...)` for schema output. No custom logging config in the tap.

---

## Testing & TDD

- **Location**: All tests live under `tests/`. Files: `test_tap.py`, `test_streams.py`, `test_utils.py`, `test_core.py`, `test_404_end_of_stream.py`. Shared fixtures and helpers (e.g. `config()`, `json_resp()`, `url_path()`, `setup_api()`) are in `tests/test_streams.py` and reused by other test modules.
- **TDD**: Per `.cursor/rules/development_practices.mdc`, write a failing test first, then implement until it passes. All tests must be able to fail (valid tests) and must pass before a task is complete (regression gate).
- **Black-box style**: Tests assert on observable outcomes only: returned records, stream schema, stream attributes. They do not assert on call counts, log lines, or internal function calls. For exceptions, use `pytest.raises(...)` and assert the expected exception type (e.g. `FatalAPIError` in `tests/test_404_end_of_stream.py`).
- **HTTP mocking**: Use `requests_mock` (e.g. `requests_mock.get(url_path(), json=json_resp())`). For pagination or 404 behaviour, use `additional_matcher` to distinguish first vs next-page requests and set `status_code`/`json` per matcher. See `test_404_end_of_stream.py` for 404-on-next-page vs initial-404.
- **Standard tap tests**: `tests/test_core.py` uses `get_tap_test_class(RestfulApiTap, config=config())` from `singer_sdk.testing` with `requests_mock` to run the SDK’s standard tap test suite.

---

## Dependency Injection & Validation

- **Authenticator**: Non-deterministic external auth is injected and cached. The tap calls `get_authenticator(self)` in `restful_api_tap/auth.py`, which caches the result on `self._authenticator`. Streams receive the same authenticator via the `authenticator` argument when building `DynamicStream` in `discover_streams()`; it is stored as `assigned_authenticator` and used by `RestApiStream.authenticator` in `restful_api_tap/client.py`. New auth methods are added by extending `select_authenticator()` in `auth.py` and returning an SDK-compatible authenticator.
- **Validation over re-testing**: Ingested data that must be parsed is loaded into a single source of truth (e.g. config via JSON Schema, records into `flatten_json` and `SchemaBuilder`). If validation fails (e.g. invalid JSON or non-dict record in `get_schema()`), the code raises and does not use the data. Once valid, the code does not re-validate the same data.
- **Config file**: Tap and stream settings are validated by the Singer SDK via `config_jsonschema`; stream-level values override or merge with top-level in `discover_streams()`.

---

## Q&A Behavior Examples

**Q: How do I add a new stream-level or top-level config property?**  
A: Add a `th.Property(...)` to the appropriate `PropertiesList` in `restful_api_tap/tap.py` (e.g. under `common_properties` or a stream-specific block). In `discover_streams()`, read the value with `stream.get("new_key", self.config.get("new_key", default))` and pass it into the `DynamicStream(...)` constructor. If the stream uses it (e.g. in `get_url_params` or `post_process`), add the parameter to `DynamicStream.__init__` in `restful_api_tap/streams.py` and use it where needed.

**Q: How do I add a new pagination style?**  
A: In `restful_api_tap/streams.py`, extend `get_new_paginator()` to handle a new `pagination_request_style` value and return an instance of a paginator class (from `restful_api_tap/pagination.py` or Singer SDK). Implement the paginator with `current_value`, `advance(response)`, and `finished`. If URL or body params differ, add or extend the branch in `get_url_params` / `prepare_request_payload` that corresponds to your `pagination_response_style`.

**Q: How do I test that sync returns the correct records for a stream?**  
A: Use `requests_mock` to stub the API URL(s) and response body (e.g. `json_resp()` from `tests/test_streams.py`). Build a tap with `config()` (and optional stream `schema` so discovery does not call the API). Call `tap.discover_streams()[0].get_records({})` and assert on the list of records (e.g. `assert records == expected_records`). See `test_next_page_request_404_treated_as_end_of_stream` in `tests/test_404_end_of_stream.py` for a full example with first page 200 and next page 404.

**Q: How do I test that an error is raised when the API fails?**  
A: Use `pytest.raises(ExpectedException):` and inside it perform the call that should fail (e.g. `list(stream.get_records({}))`). Mock the API to return the failing response (e.g. 404 on the first request). See `test_initial_request_404_raises_fatal_error` in `tests/test_404_end_of_stream.py` for initial 404 → `FatalAPIError`.

**Q: How do I add a new auth method?**  
A: In `restful_api_tap/auth.py`, add a branch in `select_authenticator()` for the new `auth_method` string. Return an authenticator that implements the SDK’s expected interface (e.g. callable that prepares the request). Credentials can come from `self.config` or environment variables. Ensure `get_authenticator()` continues to cache the result on `self._authenticator` so discovery and sync share one authenticator.

**Q: Where is stream schema defined or inferred?**  
A: In `discover_streams()` in `restful_api_tap/tap.py`. Discovery builds the catalog; per stream, if `schema` is a file path (string), the schema is loaded from JSON. If it’s a dict, it’s passed to `SchemaBuilder` and converted. Otherwise `get_schema(..., flatten_records)` is called: when true, sample records are flattened then inferred; when false, inference uses raw nested records. The result is passed to `DynamicStream(schema=schema, ...)` and emitted in SCHEMA messages.

**Q: How is post-processing applied to each record?**  
A: `DynamicStream.post_process()` in `restful_api_tap/streams.py` receives each raw record from `parse_response()`. When `flatten_records` is true, it returns `flatten_json(row, ...)`; when false, it returns the row unchanged. To add transformations, override `post_process()` (e.g. call `super().post_process(...)` then modify the returned dict).

**Q: How do I add a new utility used by multiple components?**  
A: Add a function in `restful_api_tap/utils.py` with type hints and a short docstring. Use it from `tap.py`, `streams.py`, or `pagination.py` as needed. Keep pure logic in utils; avoid importing tap/stream/client there so the dependency graph stays one-way.

---

*End of document. For architecture and data flow see [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md). For commands and entry points see [AI_CONTEXT_QUICK_REFERENCE.md](AI_CONTEXT_QUICK_REFERENCE.md).*
