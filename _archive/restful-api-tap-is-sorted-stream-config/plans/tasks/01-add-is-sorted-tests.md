# Task Plan: 01-add-is-sorted-tests

**Feature:** restful-api-tap-is-sorted-stream-config  
**Task:** Add tests that assert discovered stream `is_sorted` from config (TDD; tests written first, expected to fail until implementation in tasks 02–05).

---

## 1. Overview

This task adds black-box tests that verify the tap passes stream-level `is_sorted` config through to each discovered `DynamicStream` instance. No implementation is done in this task; tests are written first and **must fail** until `is_sorted` is added to the plugin schema, common_properties, `discover_streams()`, and `DynamicStream` (tasks 02–05). The tests assert only on the observable outcome: each stream’s `stream.is_sorted` value. No assertions on log messages, call counts, or internal function calls (per master plan and development_practices.mdc).

---

## 2. Files to Create/Modify

| File | Action |
|------|--------|
| `taps/restful-api-tap/tests/test_is_sorted.py` | **Create.** New test module containing four test functions for `is_sorted` behaviour. |

No other files are created or modified in this task.

---

## 3. Test Strategy

- **TDD:** Write all four tests in this task; they will fail until tasks 02–05 implement the feature. A test that can only pass is invalid; a test that fails for the right reason (e.g. missing `is_sorted` or wrong value) is correct.
- **Black-box:** Assert only on the discovered stream instance’s `stream.is_sorted` (and, for the multi-stream case, on each stream’s value). Do not assert on logs, `DynamicStream` call count, or internal helpers.
- **Discovery path:** Use the public entry point: `RestfulApiTap(config=..., parse_env_config=True).discover_streams()`. Discovery may call `get_schema()` when schema is not provided in config, so tests that need discovery must mock the API (e.g. reuse `setup_api` from `test_streams`) or supply a schema in config (e.g. from file or dict) to avoid real HTTP.
- **Fixtures:** Reuse `config()` and `setup_api()` from `tests/test_streams` (or equivalent minimal config builder). Build configs with `streams: [{ "name", "path", "records_path", "is_sorted": True|False|absent }]` as required by each case.

### Test cases (order in file)

1. **is_sorted true** — Config with at least one stream with `is_sorted: true`. Assert that the corresponding discovered stream has `stream.is_sorted is True`.
2. **is_sorted omitted** — Config with a stream that does not set `is_sorted` (key absent). Assert for that stream `stream.is_sorted is False`.
3. **is_sorted false** — Config with a stream that explicitly sets `is_sorted: false`. Assert for that stream `stream.is_sorted is False`.
4. **Multiple streams** — Config with two or more streams: one with `is_sorted: true`, one with `is_sorted: false` or omitted. Assert first stream has `is_sorted is True`, second has `is_sorted is False` (per-stream independence).

---

## 4. Implementation Order

1. **Create test module**  
   Add `taps/restful-api-tap/tests/test_is_sorted.py`. Import `RestfulApiTap` and, from `test_streams`, `config` and `setup_api` (and any other helpers needed for minimal discovery, e.g. schema or `requests_mock`).

2. **Implement test 1: is_sorted true**  
   Build config with one stream including `"is_sorted": True`. Ensure discovery runs (mock API with `setup_api` or provide schema in config). Instantiate tap, call `discover_streams()`, take the first stream. Assert `stream.is_sorted is True`. Add a short docstring: what is being tested and why (config true → stream is_sorted True).

3. **Implement test 2: is_sorted omitted**  
   Build config with one stream that has no `is_sorted` key. Run discovery, get that stream. Assert `stream.is_sorted is False`. Docstring: default when omitted is False (backward compatibility).

4. **Implement test 3: is_sorted false**  
   Build config with one stream with `"is_sorted": False`. Run discovery, get that stream. Assert `stream.is_sorted is False`. Docstring: explicit false is honoured.

5. **Implement test 4: multiple streams**  
   Build config with two streams: first has `is_sorted: true`, second has `is_sorted: false` or no key. Run discovery, get both streams. Assert `streams[0].is_sorted is True` and `streams[1].is_sorted is False`. Docstring: per-stream independence.

6. **Run tests**  
   From `taps/restful-api-tap/`, run `uv run pytest tests/test_is_sorted.py -v`. Confirm all four tests exist and currently fail (e.g. `AttributeError` or assertion failure because `is_sorted` is not yet set on the stream). Do not mark tests as xfail; they are expected to pass after tasks 02–05.

---

## 5. Validation Steps

- From `taps/restful-api-tap/`: `uv run pytest tests/test_is_sorted.py -v` (or `-k is_sorted`) runs exactly four tests.
- All four tests fail before implementation (e.g. missing attribute or wrong value). No test is skipped or xfail.
- After tasks 02–05 are implemented, the same four tests pass without modification.
- Lint and type-check: `uv run ruff check tests/test_is_sorted.py`, `uv run ruff format --check tests/test_is_sorted.py`, `uv run mypy restful_api_tap` (no new code in package; test file may be excluded by mypy config or pass). Resolve any issues in the new test file.
- Full gate (optional): `./install.sh` from `taps/restful-api-tap/` to ensure no regressions in other tests.

---

## 6. Documentation Updates

None. This task only adds tests. User-facing documentation (README, meltano.yml comments) is updated in task 06 (update-is-sorted-documentation). No changes to AI context or feature docs are required for this task.
