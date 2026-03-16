# AI Context — Patterns & Conventions

## Metadata

| Field | Value |
|-------|--------|
| Version | 1.5 |
| Last Updated | 2026-03-16 |
| Tags | patterns, conventions, TDD, models, DI, validation, testing, meltano, singer |
| Cross-References | [AI_CONTEXT_REPOSITORY.md](AI_CONTEXT_REPOSITORY.md) (architecture), [AI_CONTEXT_QUICK_REFERENCE.md](AI_CONTEXT_QUICK_REFERENCE.md) (commands), [AI_CONTEXT_target-gcs.md](AI_CONTEXT_target-gcs.md), [GLOSSARY_MELTANO_SINGER.md](GLOSSARY_MELTANO_SINGER.md) (tap, target, streams, config/state/Catalog) |

---

## Code Organization

- **Monorepo layout**: Each plugin is a standalone package under `taps/` or `loaders/` with its own `pyproject.toml`, source package, and `tests/`. No shared library; tap and target communicate via Singer JSONL on stdout/stdin.
- **Source package naming**: Source package = plugin directory name with hyphens replaced by underscores (e.g. `target_gcs/`). Entry module is `tap.py` (tap) or `target.py` (target).
- **Target (target-gcs) modules**:
  - `target.py` — Target class, `config_jsonschema`, `default_sink_class`, `get_sink`, `_add_sink_with_client`; injects `storage_client` via `__init__` kwargs.
  - `sinks.py` — `GCSSink` (RecordSink); selects path pattern from config/schema; delegates `process_record` and `close` to pattern; accepts `time_fn`, `extraction_date`, `storage_client` for DI.
  - `paths/` — `base.py` (`BasePathPattern` ABC), `simple.py`, `dated.py`, `partitioned.py`, `_types.py`; constants and helpers in `target_gcs.constants`, `target_gcs.helpers`.
- **Config schema**: Declared on the Target class via `singer_sdk.typing` (`th.PropertiesList`, `th.Property`). Example in `target_gcs/target.py`: `config_jsonschema = th.PropertiesList(th.Property("bucket_name", th.StringType, required=True), ...).to_dict()`.

---

## Type & Model Patterns

- **Config and schema**: Use Singer SDK typing (`singer_sdk.typing` as `th`). Properties use `th.Property(name, type, required=..., description=...)`. No Pydantic/dataclass for config; validation is load-into-SDK-schema and fail fast.
- **Validation over re-checking**: Ingested data that must be parsed is loaded into a model (or SDK schema). If validation fails, do not use the data. Once valid, do **not** check validity again downstream.
- **Typing in code**: Parameters and return types are annotated. Use `typing` for `Optional` and generic types.
- **Path patterns (target-gcs)**: Abstract base `BasePathPattern` in `target_gcs/paths/base.py` defines the interface (`process_record`, `close`, `current_key`, `filename_for_current_file`, `full_key`, `write_record_as_jsonl`, `maybe_rotate_if_at_limit`). All path patterns accept `stream_name`, `config`, `extraction_date` (required), `time_fn` (optional), `storage_client` (required). Concrete implementations (`SimplePath`, `DatedPath`, `PartitionedPath`) are selected in `GCSSink.__init__` from `hive_partitioned` and schema `x-partition-fields`.

---

## Error Handling & Logging

- **Fatal vs non-fatal**: Request/API failures that indicate unrecoverable state surface via SDK or raised exceptions. End-of-stream conditions (e.g. 404 on next page in a tap) are handled without raising when the contract allows.
- **Validation errors**: Invalid config or record shape raises (e.g. `ValueError`). Schema or record constraints are enforced at boundaries; invalid data is rejected, not re-checked downstream.
- **Logging**: Use the SDK/component `self.logger` for info/debug/error. Tests do **not** assert on log output (black-box testing).
- **Backoff**: Rate-limited APIs use config-driven backoff where applicable; streams may override wait behaviour from response headers or body.

---

## Testing & TDD

- **TDD**: Write a failing test first, then implement until it passes.
- **Valid tests**: Every test must be able to fail (no tests that can only pass).
- **Working tests**: If a test fails due to its own logic, fix the test. Failing tests (except `@pytest.mark.xfail` / `@unittest.expectedFailure`) are regressions and must be resolved before the task is complete.
- **Test file naming**: Test file name **must** be `test_{module}.py` where `{module}` is the **source module basename only** (folder path has no relevance). Examples: source `paths/simple.py` → `test_simple.py`; source `helpers/json_parsing.py` → `test_json_parsing.py`.
- **Test path mirroring**: The path **within** the source package is mirrored under `tests/unit/`. Example: source `target_gcs/paths/simple.py` → `loaders/target-gcs/tests/unit/paths/test_simple.py`; source `target_gcs/helpers/json_parsing.py` → `tests/unit/helpers/test_json_parsing.py`. The `tests/unit/` subfolder separates unit tests from the base test folder and allows a global `conftest.py` and a `files/` folder for complex JSON (or other) test data when needed.
- **One test file per source module**: Each test file corresponds to one source module for clear coverage and navigation.
- **Unit tests in-scope**: Unit tests focus on the behaviour of a single module; they do not mix integration concerns.
- **Integration tests thin**: Integration tests show that the integrating code wires behaviour correctly; they trust callees and do not re-validate logic already covered by unit tests.
- **Black-box**: Tests assert on observable behaviour (returned objects, emitted records, raised exceptions). They do **not** assert on “called_once”, log lines, or internal call counts.
- **Exception tests**: Use `pytest.raises(ExpectedException)` to assert that a specific exception type is raised.
- **Fixtures and conftest (target-gcs)**: `conftest.py` provides `sample_config`, `fixed_time_fn`, `fixed_date`, `recording_storage_client`; tests construct sinks and path patterns inline with these fixtures (e.g. `GCSSink(..., time_fn=fixed_time_fn, extraction_date=fixed_date, storage_client=recording_storage_client)`). `tests/fixtures/recording_gcs_client.py` provides `RecordingGCSClient` for in-memory GCS I/O. For abstract bases (e.g. `BasePathPattern`), use a minimal concrete subclass in tests. Schema or JSON files under `tests/` or `tests/unit/files/` are used when needed for discovery or test data.
- **Regression gate**: Any failing test not explicitly marked as expected failure is a regression and must be fixed before the task is complete.

---

## Dependency Injection & Validation

- **Non-deterministic and external deps**: Pass them in as parameters or constructor arguments. Do not hardcode `time`, file paths, or API clients inside business logic.
- **Target (target-gcs)**:
  - `GCSTarget.__init__` accepts optional `storage_client` via kwargs; if not provided, uses `google.cloud.storage.Client()`. `_add_sink_with_client` passes `self._storage_client` into the sink.
  - `GCSSink.__init__` accepts `storage_client` (required), optional `time_fn: Callable[[], float]`, and optional `extraction_date: datetime | None` (defaults to `datetime.today()` when `None`). Path patterns are constructed inside the sink with `time_fn`, `storage_client`, and `extraction_date`.
  - Path pattern classes (`BasePathPattern` and subclasses) accept `time_fn`, `storage_client`, and `extraction_date` in `__init__`; `time_fn` is used for `filename_for_current_file()` (timestamp in filename); `extraction_date` is used for path segments (e.g. date in simple path, hive date partitions in DatedPath).
- **Tests**: Use `fixed_time_fn` and `fixed_date` from conftest when constructing `GCSSink` or path pattern instances so key names and paths are deterministic. Use `recording_storage_client` or `GCSTargetWithRecordingStorage` so tests run without real GCS or ADC.
- **Config resolution**: Required settings (e.g. `bucket_name`) are enforced by the config schema. Config is supplied via config file or Meltano-injected env.

---

## Q&A Behavior Examples

### How do I add a new target option?

1. Add a `th.Property(...)` to `GCSTarget.config_jsonschema` in `loaders/target-gcs/target_gcs/target.py` (e.g. `date_format`, `max_records_per_file`).
2. Read the option in the sink or path pattern from `self.config.get("option_name", default)` (e.g. in `GCSSink` or path pattern constructors).
3. Add or adjust tests that build the sink or pattern with the new config and assert on behaviour (e.g. key name format), not on call counts.

### How do I validate that the target does not accept a credentials file?

Assert on the public config schema: load `GCSTarget.config_jsonschema` and assert `"credentials_file" not in (schema.get("properties") or {})`. Optionally patch `Client` and check constructor args to document that auth is ADC or env-only.

### How do I make tests deterministic for time/date?

Inject time and date via constructor. In `target_gcs/sinks.py`, `GCSSink` accepts optional `time_fn` and `extraction_date`; production uses `time.time` (via pattern’s `filename_for_current_file`) and `datetime.today()` when not provided. In tests, use conftest fixtures `fixed_time_fn` and `fixed_date` when constructing `GCSSink` or path pattern instances (e.g. `GCSSink(..., time_fn=fixed_time_fn, extraction_date=fixed_date, storage_client=recording_storage_client)`). Do not patch `time` or `datetime` inside the unit under test; pass functions or values as parameters (DI).

### How do I add a new path pattern (e.g. for target-gcs)?

1. Implement a class inheriting from `BasePathPattern` in `loaders/target-gcs/target_gcs/paths/` (e.g. `custom.py`). Implement `process_record` and `close`; use `filename_for_current_file()`, `full_key()`, `write_record_as_jsonl()`, `maybe_rotate_if_at_limit()` from the base. Accept `time_fn`, `storage_client`, and `extraction_date` in `__init__` for DI.
2. Export the class from `target_gcs/paths/__init__.py` and add a branch in `GCSSink.__init__` (in `sinks.py`) to select the new pattern based on config/schema (e.g. a new config flag or `x-*` schema property).
3. Add unit tests under `loaders/target-gcs/tests/unit/paths/test_custom.py` (mirroring source path). Use `fixed_time_fn`, `fixed_date`, and `recording_storage_client`; assert on returned key shape or written content, not call counts.

### How do I run the test suite?

Per-plugin: from the plugin directory run `./install.sh` (creates venv, installs deps, runs tests) or activate the venv and run `pytest` (e.g. `cd loaders/target-gcs && source .venv/bin/activate && pytest`). Use the project’s test runner and linters as defined in each plugin’s `pyproject.toml`; resolve style/type issues before considering the task complete.

### How is path pattern selection done in target-gcs?

In `GCSSink.__init__`: if `hive_partitioned` is false or unset → `SimplePath`; if `hive_partitioned` is true and schema has non-empty `x-partition-fields` → `PartitionedPath`; if `hive_partitioned` is true and no/empty `x-partition-fields` → `DatedPath`. All patterns receive `stream_name`, `config`, `time_fn`, `storage_client`, and `extraction_date`.

### Where do I put a test for a new source file?

Create a test file named `test_{module}.py` where `{module}` is the basename of the source module. Place it under `tests/unit/` mirroring the source path. Example: new file `target_gcs/paths/custom.py` → new test file `tests/unit/paths/test_custom.py`.

---

## File Reference (short)

| Purpose | Target (target-gcs) |
|--------|----------------------|
| Entry, config schema | `loaders/target-gcs/target_gcs/target.py` |
| Sink logic | `loaders/target-gcs/target_gcs/sinks.py` |
| Path patterns | `target_gcs/paths/base.py`, `simple.py`, `dated.py`, `partitioned.py` |
| Helpers / constants | `target_gcs/constants.py`, `target_gcs/helpers/` |
| Tests | `loaders/target-gcs/tests/unit/` (mirror: `paths/test_*.py`, `test_sinks.py`, `test_target.py`, `helpers/test_*.py`) |
| Conftest / fixtures | `loaders/target-gcs/tests/conftest.py`, `tests/fixtures/recording_gcs_client.py` |
