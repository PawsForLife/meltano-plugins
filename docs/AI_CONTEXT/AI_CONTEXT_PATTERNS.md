# AI Context — Patterns & Conventions

## Metadata

| Field | Value |
|-------|--------|
| Version | 1.4 |
| Last Updated | 2026-03-13 |
| Tags | patterns, conventions, TDD, models, DI, validation, testing, meltano, singer |
| Cross-References | [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) (architecture), [AI_CONTEXT_QUICK_REFERENCE.md](AI_CONTEXT_QUICK_REFERENCE.md) (commands), [AI_CONTEXT_restful-api-tap.md](AI_CONTEXT_restful-api-tap.md), [AI_CONTEXT_target-gcs.md](AI_CONTEXT_target-gcs.md), [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md) |

---

## Code Organization

- **Monorepo layout**: Each plugin is a standalone package under `taps/` or `loaders/` with its own `pyproject.toml`, source package, and `tests/`. No shared library; tap and target communicate via Singer JSONL on stdout/stdin.
- **Source package naming**: Source package = plugin directory name with hyphens replaced by underscores (e.g. `restful_api_tap/`, `target_gcs/`). Entry module is `tap.py` (tap) or `target.py` (target).
- **Module responsibilities**:
  - **Tap**: `tap.py` — Tap class, config schema (`common_properties`, `top_level_properties`), stream discovery (`discover_streams()`); `streams.py` — `DynamicStream`; `auth.py` — `get_authenticator`, `select_authenticator`; `client.py` — `RestApiStream`, `_request`, `request_records`; `pagination.py`; `utils.py` (e.g. `flatten_json`).
  - **Target (target-gcs)**: `target.py` — Target class, `config_jsonschema`, `default_sink_class`, `get_sink`; `sinks.py` — `GCSSink` (delegates to path pattern); `paths/` — `base.py` (`BasePathPattern` ABC), `simple.py`, `dated.py`, `partitioned.py`, `_types.py`; `constants.py`; `helpers.py`.
- **Config schema**: Declared on the Tap/Target class via `singer_sdk.typing` (`th.PropertiesList`, `th.Property`). Target example in `target_gcs/target.py`: `config_jsonschema = th.PropertiesList(th.Property("bucket_name", th.StringType, required=True), ...).to_dict()`. Stream-level and top-level properties are merged in tap config (e.g. `stream.get("key", self.config.get("key", default))` in `discover_streams()`).

---

## Type & Model Patterns

- **Config and schema**: Use Singer SDK typing (`singer_sdk.typing` as `th`). Properties are defined with `th.Property(name, type, required=..., description=...)`. Complex or nested data uses `th.ObjectType()`, `th.ArrayType()`, etc. No Pydantic/dataclass for config; validation is “load into SDK schema + fail fast.”
- **Validation over re-checking**: Ingested data that must be parsed is loaded into a model (or SDK schema). If validation fails, do not use the data. Once valid, do **not** check validity again downstream.
- **Typing in code**: Parameters and return types are annotated (e.g. `def parse_response(self, response: requests.Response) -> Iterable[dict]`). Use `typing` for Optional and generic types where appropriate.
- **Stream/sink construction**: Tap builds stream instances with explicit kwargs from resolved config (e.g. in `tap.py`: `DynamicStream(tap=self, name=..., path=..., schema=..., authenticator=self._authenticator)`). No implicit global state for stream options.
- **Path patterns (target-gcs)**: Abstract base `BasePathPattern` in `target_gcs/paths/base.py` defines the interface (`process_record`, `close`, `current_key`, helpers). Concrete implementations (`SimplePath`, `DatedPath`, `PartitionedPath`) are selected in `GCSSink.__init__` from config and schema; all accept optional `time_fn`, `date_fn`, `storage_client` for DI.

---

## Error Handling & Logging

- **Fatal vs non-fatal**: Initial request failures (e.g. 404 on first page) are fatal and surface via SDK (e.g. `FatalAPIError`). Next-page 404 is treated as end-of-stream in `restful_api_tap/client.py`: in `_request()`, when `response.status_code == 404` and `_is_next_page_request` is True, return without calling `validate_response(response)`; in `request_records()`, break the loop on 404 and stop yielding.

  Example (`client.py`):

  ```python
  if response.status_code == 404 and getattr(self, "_is_next_page_request", False):
      return response
  self.validate_response(response)
  ```

- **Validation errors**: Invalid config or response shape raises (e.g. `ValueError` for unknown auth method or non-dict record). Schema inference requires dict records; otherwise `ValueError("Input must be a dict object.")`.
- **Logging**: Use the SDK/stream `self.logger` for info/debug/error. No tests assert on log output (black-box testing). Log messages are descriptive (e.g. “Pagination stopped after N pages because no records were found”).
- **Backoff**: Rate-limited APIs use config-driven backoff (`backoff_type`: `message`, `header`, or default). Streams can override `backoff_wait_generator` to yield wait times from response message or header.

---

## Testing & TDD

- **TDD**: Write a failing test first, then implement until it passes.
- **Valid tests**: Every test must be able to fail (no tests that can only pass).
- **Working tests**: If a test fails due to its own logic, fix the test; failing tests (except `@pytest.mark.xfail` / `@unittest.expectedFailure`) are regressions and must be resolved before the task is complete.
- **Test layout**: One test file per source module. Test file name **must** be `test_{module}.py` (source module basename only). Path **must** mirror source under `tests/unit/`: e.g. source `target_gcs/paths/base.py` → `loaders/target-gcs/tests/unit/paths/test_base.py`; source `target_gcs/helpers.py` → `tests/unit/helpers/test_json_parsing.py` (or `test_helpers.py` if testing the whole module). Tests live under each plugin's `tests/` (e.g. `loaders/target-gcs/tests/`).
- **Unit tests in-scope**: Unit tests focus on the behaviour of a single module; they do not mix integration concerns; integration behaviour is covered elsewhere.
- **Integration tests thin**: Integration tests show that the integrating code wires behaviour correctly and applies the right logic; they trust callees and do not re-validate logic already covered by unit tests.
- **No duplication or mixing**: Do not duplicate unit-level validation in integration tests; do not mix unit and integration concerns in the same test file or test case.
- **Black-box**: Tests assert on observable behaviour (returned objects, emitted records, raised exceptions). They do **not** assert on “called_once”, log lines, or internal call counts. For external data changes, the mock (e.g. `requests_mock`) provides the changed response; for internal state, assert on returned or mutated objects.
- **Exception tests**: Use `pytest.raises(ExpectedException)` to assert that a specific exception type is raised (e.g. `with pytest.raises(FatalAPIError): list(stream.get_records({}))`). See `taps/restful-api-tap/tests/test_404_end_of_stream.py::test_initial_request_404_raises_fatal_error`.
- **Fixtures and helpers**: Shared config and API mocks are factored into test helpers (e.g. `build_sink()`, `_build_pattern()` in `loaders/target-gcs/tests/unit/test_sinks.py` and `loaders/target-gcs/tests/unit/paths/test_base.py`). For abstract bases, use a minimal concrete subclass (e.g. `_MinimalPattern` extending `BasePathPattern`) to instantiate in tests. Patch at module boundary (e.g. `_patch_all_pattern_modules()` for `smart_open.open` and `Client`) when testing sink behaviour without real GCS. Schema files under `tests/` (e.g. `tests/schema.json`) are used when discovery is bypassed.
- **SDK standard tests**: Taps use `get_tap_test_class(RestfulApiTap, config=...)`; targets use `get_target_test_class(GCSTarget, config=...)` and a test class that subclasses the result (e.g. `class TestGCSTarget(StandardTargetTests)`).
- **Regression gate**: Any failing test that is not explicitly marked as expected failure is a regression and must be fixed before the task is complete.

---

## Dependency Injection & Validation

- **Non-deterministic and external deps**: Pass them in as parameters or constructor arguments. Do not hardcode `time`, file paths, or API clients inside business logic. Examples: authenticator is passed into `DynamicStream(..., authenticator=self._authenticator)`; `GCSSink` in `target_gcs/sinks.py` accepts optional `time_fn` and `date_fn` callables in `__init__` for deterministic key naming and partition fallback in tests.

  Example (`target_gcs/sinks.py`):

  ```python
  def __init__(self, target, stream_name, schema, key_properties, *,
      time_fn: Callable[[], float] | None = None,
      date_fn: Callable[[], datetime] | None = None,
      storage_client: Any | None = None,
  ):
      ...
      self._time_fn = time_fn
      self._date_fn = date_fn
  ```

  In tests (e.g. `loaders/target-gcs/tests/unit/test_sinks.py`), use `build_sink(time_fn=..., date_fn=...)` so key names and partition paths are deterministic. GCS client is constructed from config context; tests patch `target_gcs.sinks.Client` to assert constructor args (e.g. no credentials path for ADC).

- **Authenticator caching**: The tap caches the authenticator in `_authenticator` and reuses it across streams. OAuth refresh is handled inside the authenticator; `get_authenticator(self)` returns the cached instance or builds one via `select_authenticator(self)` in `auth.py`.
- **Config resolution**: Tap merges top-level and stream-level config (e.g. `params = {**self.config.get("params", {}), **stream.get("params", {})}`). Required settings (e.g. `api_url`, `bucket_name`) are enforced by the config schema and runtime checks. Config is supplied via config file or Meltano-injected env.

---

## Q&A Behavior Examples

### How do I add a new stream?

1. Add a stream entry to the tap config `streams` array with `name`, `path`, and any stream-level overrides (`records_path`, `primary_keys`, `replication_key`, etc.).
2. Streams are created in `RestfulApiTap.discover_streams()` by iterating `self.config["streams"]`, resolving schema (file path, dict, or inferred via `get_schema()`), and instantiating `DynamicStream(...)` with the resolved kwargs.
3. No code change is needed if the stream is fully described in config; for custom behaviour, subclass `DynamicStream` or add a new stream class and wire it in discovery.

### How do I handle auth?

1. Set `auth_method` in config (`no_auth`, `api_key`, `basic`, `oauth`, `bearer_token`, `aws`). Provide the required config keys for that method (see tap `top_level_properties` in `tap.py`).
2. The tap calls `get_authenticator(self)` when it needs auth (e.g. in `get_schema()` and via the stream’s `authenticator` property). Authenticators live in `restful_api_tap/auth.py`; OAuth uses `ConfigurableOAuthAuthenticator`, AWS uses `AWSConnectClient` and sets `self.http_auth`.
3. To add a new auth method: implement a new authenticator (or use an SDK one), add a branch in `select_authenticator()` in `auth.py`, and add any new config properties to `top_level_properties` in `tap.py`.

### How do I add a new target option?

1. Add a `th.Property(...)` to `GCSTarget.config_jsonschema` in `loaders/target-gcs/target_gcs/target.py` (e.g. `date_format`, `max_records_per_file`).
2. Read the option in the sink from `self.config.get("option_name", default)` (e.g. in `GCSSink.key_name` and related logic in `sinks.py`).
3. Add or adjust tests that build the sink with the new config and assert on behaviour (e.g. key name format), not on call counts.

### How do I add a new tap (top-level or stream-level) config property?

1. Add the property to `common_properties` (stream-level and top-level) or `top_level_properties` only in `restful_api_tap/tap.py`, using `th.Property(...)` with type, required, default, and description.
2. If it is stream-level, ensure `discover_streams()` resolves it (e.g. `stream.get("key", self.config.get("key", default))`) and passes it into `DynamicStream(...)`.
3. If the stream or auth logic uses it, add the parameter to `DynamicStream.__init__` and/or the relevant methods. Optionally add a test that asserts the property appears in `config_jsonschema` or that behaviour changes when the property is set.

### How do I treat 404 as end-of-stream?

- Only for **next-page** requests. In `RestApiStream._request()` (`taps/restful-api-tap/restful_api_tap/client.py`), when `response.status_code == 404` and `_is_next_page_request` is True, return the response without calling `validate_response(response)`. In `request_records()`, when the response is 404, break the loop and do not yield further records. The initial request must still raise on 404 (e.g. `FatalAPIError`). Tests: `taps/restful-api-tap/tests/test_404_end_of_stream.py` — e.g. `test_initial_request_404_raises_fatal_error` uses `pytest.raises(FatalAPIError)` and `test_next_page_request_404_treated_as_end_of_stream` asserts record count from first page only.

### How do I add a new pagination style?

1. Implement a paginator (or use an SDK base) and optionally a `_get_url_params_*` style in `restful_api_tap/streams.py`.
2. Register the style in `get_new_paginator()` (e.g. by `pagination_request_style` string) and, if needed, in the `get_url_params_styles` dict for request body vs params.
3. Add config properties for any new parameters (e.g. `pagination_*`) in `tap.py` and pass them into `DynamicStream`. Add tests that mock paged responses and assert record count or last page behaviour.

### How do I validate that the target does not accept a credentials file?

- Assert on the public config schema: in a test, load `GCSTarget.config_jsonschema` and assert `"credentials_file" not in (schema.get("properties") or {})`. Optionally assert that the GCS client is constructed without a credentials path by patching `Client` and checking constructor args (e.g. in `loaders/target-gcs/tests/unit/test_sinks.py`). This documents that auth is ADC or env-only.

### How do I make tests deterministic for time/date?

- Inject time/date via constructor. In `target_gcs/sinks.py`, `GCSSink` accepts optional `time_fn` and `date_fn` callables; production uses `time.time` and `datetime.today` when not provided. In tests (e.g. `loaders/target-gcs/tests/unit/test_sinks.py`), use `build_sink(time_fn=..., date_fn=...)` so key names and partition paths are deterministic. Do not patch `time` or `datetime` inside the unit under test; pass functions as parameters (DI).

### How do I add a new path pattern (e.g. for target-gcs)?

1. Implement a class inheriting from `BasePathPattern` in `loaders/target-gcs/target_gcs/paths/` (e.g. `custom.py`). Implement `process_record` and `close`; use `filename_for_current_file()`, `full_key()`, `write_record_as_jsonl()`, `maybe_rotate_if_at_limit()` from the base. Accept `time_fn`, `date_fn`, `storage_client` in `__init__` for DI.
2. Export the class from `target_gcs/paths/__init__.py` and add a branch in `GCSSink.__init__` (in `sinks.py`) to select the new pattern based on config/schema (e.g. a new config flag or `x-*` schema property).
3. Add unit tests under `loaders/target-gcs/tests/unit/paths/test_custom.py` (mirroring source path). Use a deterministic `time_fn`/`date_fn` and mock `Client`/`smart_open.open`; assert on returned key shape or written content, not call counts.

### How do I run the test suite?

- Per-plugin: from the plugin directory run `./install.sh` (creates venv, installs deps, runs tests) or activate the venv and run `pytest` (e.g. `cd loaders/target-gcs && source .venv/bin/activate && pytest`). Use the project’s test runner and linters as defined in each plugin’s `pyproject.toml`; resolve style/type issues before considering the task complete.

---

## File Reference (short)

| Purpose | Tap | Target (target-gcs) |
|--------|-----|----------------------|
| Entry, config schema | `taps/restful-api-tap/restful_api_tap/tap.py` | `loaders/target-gcs/target_gcs/target.py` |
| Stream/sink logic | `restful_api_tap/streams.py`, `client.py` | `target_gcs/sinks.py` |
| Path patterns | — | `target_gcs/paths/base.py`, `simple.py`, `dated.py`, `partitioned.py` |
| Auth | `restful_api_tap/auth.py` | — |
| Helpers | `restful_api_tap/utils.py`, `pagination.py` | `target_gcs/constants.py`, `target_gcs/helpers.py` |
| Tests | `taps/restful-api-tap/tests/*.py` | `loaders/target-gcs/tests/unit/*.py` (mirror: `paths/test_*.py`, `test_sinks.py`, `test_target.py`) |
