# Archive: fix target-gcs-real-client-in-tests

Summary of the bug fix for target-gcs tests failing in CI because the target used the real `google.cloud.storage.Client` and required GCP credentials. The fix makes the GCS client injectable so tests can run without Application Default Credentials (ADC).

---

## The request

### Symptoms

- `uv run pytest` in `loaders/target-gcs` failed in CI (e.g. GitHub Actions).
- Failures occurred in singer-sdk standard target tests such as `TestGCSTarget.test_target_array_data` and `TestGCSTarget.test_target_camelcase`.
- Stack trace showed: `process_record` → `_process_record_single_or_chunked` / `_process_record_partition_by_field` → `gcs_write_handle` or direct `Client()` → `google.auth.default()` → `DefaultCredentialsError` (no credentials in CI).

### Reproduction

1. Use an environment **without** GCP Application Default Credentials (unset `GOOGLE_APPLICATION_CREDENTIALS`, no `gcloud auth application-default login`).
2. From repo root: `cd loaders/target-gcs && uv run pytest`.
3. Tests in `tests/test_core.py` for `TestGCSTarget` that perform a full sync fail with `DefaultCredentialsError`.

Trigger: any test that causes the target to process RECORD messages and write to GCS. First access to `GCSSink.gcs_write_handle` (sinks.py ~line 182) or first write in partition-by-field mode (sinks.py ~line 275) constructed `Client()`, which called `google.auth.default()` and raised when ADC was absent.

### Expected vs actual

| Aspect        | Expected                         | Actual                                                |
|---------------|----------------------------------|-------------------------------------------------------|
| Credentials   | Tests need no GCP credentials    | Tests failed without ADC                               |
| Client usage  | Client injectable / mockable     | Real `Client()` constructed inside sink                |
| CI            | `uv run pytest` passes           | `DefaultCredentialsError` during target test cases      |

### Root cause

The GCS storage client was not injectable. It was built inside `GCSSink` at two call sites (`sinks.py` lines 182 and 275) with no parameter or factory. Singer-sdk standard target tests run a full sync and used this real path; `Client()` calls `google.auth.default()`, which raises in environments without ADC. The cause was the **absence of dependency injection for the GCS client**, not CI or test configuration. This also conflicted with project rules (development_practices.mdc): external API connections must be passed in as parameters.

**Affected components:** `GCSSink` (sinks.py) and `GCSTarget` (target.py) as primary; `test_core.py` and `test_sinks.py` as secondary (tests could not inject a client).

---

## Planned approach

### Chosen fix: Option A — inject storage_client

Inject an optional storage client via the sink constructor and have the target pass it when creating sinks. Tests use a target subclass that sets a mock client.

1. **GCSSink:** Add optional `storage_client=None` to `__init__`. In `gcs_write_handle` and `_process_record_partition_by_field`, use `self._storage_client` when set, otherwise `Client()`.
2. **GCSTarget:** Hold `self._storage_client = None`. Override `get_sink()` so that when creating a new sink, the sink is instantiated with `storage_client=self._storage_client` (plus existing target, stream_name, schema, key_properties and optional time_fn/date_fn).
3. **test_core.py:** Use a target subclass that sets `_storage_client` to a mock (e.g. `MagicMock()`) in `__init__`, and pass that subclass to `get_target_test_class(..., target_class=GCSTargetWithMockStorage)` so standard target tests run without ADC.

**Rationale:** Aligns with development_practices.mdc (external APIs passed in); matches existing GCSSink pattern (time_fn/date_fn) and singer-sdk precedent (SQLTarget overrides `get_sink()` to pass a shared connector). No config or CLI change; when `storage_client` is `None`, behavior is unchanged.

Alternatives rejected: (B) client factory — unnecessary complexity for current needs; (C) patching `Client` in test_core — violates DI rule; (D) config key for client — pollutes config; (E) test-only sink subclass — does not make production sink accept an injected client.

### Task breakdown

| Task | Scope | Outcome |
|------|--------|---------|
| **01** — GCSSink optional storage_client | sinks.py: add `storage_client` to `GCSSink.__init__`; use at `gcs_write_handle` and `_process_record_partition_by_field`. | Injection point in sink. |
| **02** — GCSTarget storage_client and get_sink | target.py: set `_storage_client` in `__init__`; override `get_sink()` to create/register sinks with `storage_client=self._storage_client` (cannot use base `add_sink()` because it is final and does not pass extra kwargs). | Target passes client into sinks. |
| **03** — test_core subclass and get_target_test_class | test_core.py: define `GCSTargetWithMockStorage(GCSTarget)` setting `_storage_client = MagicMock()` after `super().__init__`; use it in `get_target_test_class()`. | Standard target tests run without ADC. |
| **04** — test_sinks build_sink optional | test_sinks.py: add optional `storage_client=None` to `build_sink()` and pass through to `GCSSink`; optionally use `build_sink(storage_client=MagicMock())` in write-path tests. | Tests can use DI instead of (or with) patches. |

### Success criteria

- All tests in `loaders/target-gcs` pass when run without GCP credentials (e.g. in CI).
- No production config or CLI change; backward compatible.
- GCSSink accepts an optional injected storage client; GCSTarget provides it when creating sinks.
- Standard target tests run without ADC via target subclass with mock client.
- Black-box testing preserved; no assertions on call counts or log lines.

---

## What was implemented

All four tasks were implemented as planned.

### 01 — GCSSink optional storage_client (sinks.py)

- Added optional keyword-only parameter `storage_client: Optional[Any] = None` to `GCSSink.__init__` (after `date_fn`); stored as `self._storage_client`.
- In `gcs_write_handle`: replaced `client = Client()` with `client = self._storage_client if self._storage_client is not None else Client()`.
- In `_process_record_partition_by_field`: same conditional for client construction before `smart_open.open(...)`.

Default path (no client provided) unchanged; existing tests that patch `Client` continue to pass.

### 02 — GCSTarget storage_client and get_sink (target.py)

- Added `GCSTarget.__init__` that calls `super().__init__(...)` then sets `self._storage_client = None`.
- Overrode `get_sink(stream_name, *, record=None, schema=None, key_properties=None)` to mirror base lookup/creation logic but, when a new sink is needed, instantiate the sink class with `storage_client=self._storage_client`, call `sink.setup()`, register in `_sinks_active`, and return it (without calling the base `add_sink()` so the extra kwarg is passed).

Production behavior when `_storage_client` is `None` unchanged; sink still uses `Client()` internally when no client is injected.

### 03 — test_core subclass and get_target_test_class (test_core.py)

- Defined `GCSTargetWithMockStorage(GCSTarget)` with `__init__(self, **kwargs)`: `super().__init__(**kwargs)` then `self._storage_client = MagicMock()`.
- Replaced `get_target_test_class(target_class=GCSTarget, config=SAMPLE_CONFIG)` with `get_target_test_class(target_class=GCSTargetWithMockStorage, config=SAMPLE_CONFIG)`.
- `SAMPLE_CONFIG` left as `{"bucket_name": "test-bucket"}`; no config key for the client.

Standard target tests (e.g. `test_target_array_data`, `test_target_camelcase`) now pass without ADC and act as the regression gate.

### 04 — test_sinks build_sink optional (test_sinks.py)

- Added optional parameter `storage_client=None` to `build_sink()`.
- When `storage_client is not None`, set `kwargs["storage_client"] = storage_client` and pass through to `GCSSink(...)`.

Write-path tests can use `build_sink(storage_client=MagicMock())`; existing tests remain valid.

### Verification

- Tests run without GCP credentials: `cd loaders/target-gcs && uv run pytest` — all tests pass.
- No production config or CLI change; behavior with no injected client unchanged.
- Lint/format/type-check (ruff, mypy) pass.
- Fix aligns with development_practices.mdc (dependency injection for external API connections). CHANGELOG documents the new optional `storage_client` on GCSSink, target `_storage_client` and `get_sink()` override, use of `GCSTargetWithMockStorage` in test_core, and optional `storage_client` on test_sinks `build_sink()`.
