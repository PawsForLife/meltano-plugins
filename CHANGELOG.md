# Changelog

## 2026-03-12

### Changed

- **AI context** — Quick reference table: target-gcs Python constraint updated to `>=3.12,<4.0` to match `loaders/target-gcs/pyproject.toml`.
- **typing-312-standards** — Updated Python type hints to 3.12 style (built-in generics and pipe unions) across tap, target, and scripts.
- **python-3.12-minimum** — Repo standard and **target-gcs** now require Python 3.12 minimum. target-gcs `pyproject.toml` and tool config (ruff, mypy) updated; lockfile and code aligned to 3.12. restful-api-tap was already 3.12. Details: [_archive/python-3.12-minimum/python-3.12-minimum.md](_archive/python-3.12-minimum/python-3.12-minimum.md)

## 2025-03-12

### Changed

- **Root changelog format** — Root `CHANGELOG.md` now uses date-based headings (`## YYYY-MM-DD`) only; no version numbers. Repo is released by pushing. Feature and bug pipelines, CONVENTIONS § Changelogs, and implement workflows updated accordingly.

- **README Development section** — Document that push-time and local pre-commit checks run ruff, mypy, and pytest (pre-commit hook and wrapper already did; README now matches).
- **Normalise plugin source folders** — Details: [normalise-plugin-source-folders.md](_archive/normalise-plugin-source-folders/normalise-plugin-source-folders.md)
  - Rename source package `gcs_target` to `target_gcs` in loaders/target-gcs (directory rename only; config and imports in later tasks).
  - Point plugin config to `target_gcs`: pyproject.toml (scripts entry point and wheel packages), meltano.yml (namespace), install.sh (mypy target).
  - Update Python imports and test patches in loaders/target-gcs from `gcs_target` to `target_gcs` (target.py, tests/__init__.py, test_core.py, test_sinks.py, test_partition_key_generation.py).
  - Derive mypy package from plugin path in `scripts/run_plugin_checks.sh` and `.github/workflows/plugin-unit-tests.yml`: last path component with hyphens replaced by underscores (no plugin-specific case blocks).
  - Update documentation: README and AI context use `target_gcs`; root and plugin CHANGELOGs add migration note.
- **target-gcs migration (normalise-plugin-source-folders):** Package/namespace renamed from `gcs_target` to `target_gcs`. Users: update `meltano.yml` namespace to `target_gcs` and re-run `meltano install`; verification commands use `mypy target_gcs`.
- **target-gcs** — Add `_close_handle_and_clear_state()` helper in `GCSSink`; use it in `_process_record_partition_by_field` for partition change and key-change paths to remove duplicated flush/close/clear-key logic (refactor, behaviour unchanged).
- **root-pre-commit-and-install archive** — Update failure-behaviour and root install.sh description to match implementation: root install runs all plugin installs, prints succeeded/failed summary, exits non-zero if any failed (no longer "stop on first failure").
- **target-gcs-split-process-record** — Details: [target-gcs-split-process-record.md](_archive/target-gcs-split-process-record/target-gcs-split-process-record.md)
  - Extract single-file/chunked path to _process_record_single_or_chunked; process_record delegates when partition_date_field unset (task 01).
  - Extract partition-by-field path to _process_record_partition_by_field; process_record delegates when partition_date_field set (task 02).
  - Make process_record thin dispatch only: config read, branch on partition_date_field, delegate; docstring updated (task 04).
- **custom-meltano-plugins-documentation** — Details: [custom-meltano-plugins-documentation.md](_archive/custom-meltano-plugins-documentation/custom-meltano-plugins-documentation.md)
  - Docs state plugins are custom (not on Meltano Hub or PyPI); install via `meltano.yml` and `pip_url` with `#subdirectory=`, variant **petcircle** in examples.
  - Root README, docs/monorepo, docs/README, AI_CONTEXT (quick reference, repository), and tap README updated; tap README has "Install from this monorepo" subsection.
- **glossary-terminology-repo** — Details: [glossary-terminology-repo.md](_archive/glossary-terminology-repo/glossary-terminology-repo.md)
  - Align root README and CHANGELOG to glossary terminology (tap, target, extractor, loader, source, destination, stream, catalog, config file, state file).
  - Align scripts: comments and docstrings in `scripts/list_packages.py` and `scripts/tests/*.py` to glossary (tap, target, extractor, loader); no logic or path changes.
  - Align GitHub workflows: job names, comments, and step descriptions in `.github/workflows/*.yml` to glossary (tap, target, plugin); no run/paths/matrix or logic changes.
  - Align Cursor commands: `.cursor/commands/update_context.md` updated so AI context docs describe extractors as taps and loaders as targets per glossary; prose only, no behaviour or path changes.
  - Align Cursor agents: `.cursor/agents/*.md` use glossary terms (tap, target, config file, state file, catalog, stream); added Resources bullet to architect, archivist, debug-specialist, implementer, researcher, task-decomposer; ai-context-writer already referenced glossary.
  - Align Cursor commands: `.cursor/commands/*.md` use glossary (extractor as tap, loader as target); update_context already compliant; audit only.
  - Align Cursor workflows: `.cursor/workflows/*.md` use glossary terminology (tap, target, stream, catalog, config file, state file, SCHEMA/RECORD/STATE) where describing Singer/Meltano pipelines or plugins; pipeline state preserved for scratchpad/workflow state.
  - Align Cursor agents: `.cursor/agents/*.md` use glossary (tap, target, config file, state file, catalog, stream) in Resources; all seven agents already compliant.
- **Target filenames and glossary alignment** — Details: [target-filenames-and-glossary-alignment.md](_archive/target-filenames-and-glossary-alignment/target-filenames-and-glossary-alignment.md)
  - Rename Python package `gcs_loader` → `gcs_target` and CLI/plugin `gcs-loader` → `target-gcs` under `loaders/gcs-loader/` (pyproject.toml, meltano.yml, install.sh, source, tests; top-level dir unchanged until task 02).
  - Top-level directory renamed `loaders/gcs-loader/` → `loaders/target-gcs/`; repo-wide path and plugin references updated.
  - Package README and sample config updated to use `target-gcs` and `gcs_target`; root CHANGELOG documents migration.
  - **User migration:** Plugin name is `target-gcs`, path is `loaders/target-gcs/`, package is `gcs_target`. Update `meltano.yml` to use `target-gcs` and re-run `meltano install`.
- **Glossary terminology (target)** — Details: [glossary-terminology-target.md](_archive/glossary-terminology-target/glossary-terminology-target.md)
  - Rename class and entry point: `GCSLoader` → `GCSTarget` in `loaders/gcs-loader`; CLI entry point set to `GCSTarget.cli`; module/class docstrings updated per glossary (target, destination, config file).
  - Terminology in source: align docstrings and comments in `target.py` and `sinks.py` with glossary (target, sink, destination, config file, state file, SCHEMA, RECORD, STATE, RecordSink, sink drain, stream, record).
  - Terminology in tests: align docstrings and comments in `test_core.py` and `test_sinks.py` with glossary (target, sink, config file); no assertion or behavioural changes.
  - In-package docs: README aligned with glossary (target, loader, config file, destination); CLI name and config schema unchanged.
- **Plugin class name alignment** — Details: [plugin-class-name-alignment.md](_archive/plugin-class-name-alignment/plugin-class-name-alignment.md)
  - GCS loader (target): class renamed TargetGCS → GCSLoader, name set to "gcs-loader"; tests, pyproject.toml, meltano.yml, README updated.
  - Restful API tap: class renamed TapRestApiMsdk → RestfulApiTap, name set to "restful-api-tap"; script restful-api-tap.sh, pyproject.toml, meltano.yml, tests, README and AI_CONTEXT docs updated.
  - Repo docs: root README and docs/monorepo updated to use gcs-loader and restful-api-tap in plugins table, installation YAML, directory layout, and pipeline examples.
- **Cursor workflows and commands** — Normalized `{task_file}` to mean filename without `.md`; paths use `{task_file}.md`; applied across `5-plan-task-bug.md`, `5-plan-task-feature.md`, `implement-task-fix.md`, `implement-task-feature.md`, `bug-pipeline.md`, `feature-pipeline.md`, and `architect.md`.

### Fixed

- **install.sh** — Use fail-early throughout: exit on package discovery failure, on first package install failure, and on pre-commit (pip or hook) failure; remove SUCCEEDED/FAILED arrays and summary section.
- **target-gcs tests** — Annotate `StandardTargetTests` with `cast(type[BaseTestClass], ...)` and import `BaseTestClass` from `singer_sdk.testing.factory` so the test base is explicitly typed; add targeted `# type: ignore[valid-type,misc]` on `TestGCSTarget` because mypy does not accept variables as base classes.
- **install.sh** — Run package discovery (`list_packages.py`) once into a temp file; check its exit status and exit non-zero on failure before the install loop, so discovery errors are propagated instead of the loop silently seeing no packages.
- **install.sh** — Record failures when `pip3 install pre-commit` or `pip install pre-commit` fails: check exit status after each pip command, append to FAILED and set PRECOMMIT_FAILED=1 so the summary and script exit code reflect the failure; set PRECOMMIT_FAILED=1 in the no-pip branch for consistency.
- **run_plugin_checks.sh** — Run `list_packages.py` once before the loop; capture stdout and exit status, exit script on non-zero; feed captured output to the loop via here-string so the Python command's exit code is not hidden.
- **fix-mypy-standard-target-tests-base-class** — Details: [fix-mypy-standard-target-tests-base-class.md](_archive/fix-mypy-standard-target-tests-base-class/fix-mypy-standard-target-tests-base-class.md)
  - In Plugin unit tests workflow, run mypy on the derived source package only (from `matrix.path`: last component, hyphens → underscores) instead of `.`, so test code is not type-checked and CI no longer fails on `StandardTargetTests` base class.
- **fix-target-gcs-template-tests-config-validation** — Details: [fix-target-gcs-template-tests-config-validation.md](_archive/fix-target-gcs-template-tests-config-validation/fix-target-gcs-template-tests-config-validation.md)
  - Set `SAMPLE_CONFIG` in `loaders/target-gcs/tests/test_core.py` to `{"bucket_name": "test-bucket"}` so SDK template tests pass config validation.
- **fix-github-output-eof-delimiter** — Details: [fix-github-output-eof-delimiter.md](_archive/fix-github-output-eof-delimiter/fix-github-output-eof-delimiter.md)
  - Add regression test that JSON output from `list_packages.py --json` ends with newline (heredoc/GITHUB_OUTPUT compatibility).
  - Emit trailing newline from `list_packages.py` when outputting JSON so GitHub Actions discover step no longer fails with "Matching delimiter not found 'EOF'".

### Added

- **root-pre-commit-and-install** — Details: [root-pre-commit-and-install.md](_archive/root-pre-commit-and-install/root-pre-commit-and-install.md)
  - Add `scripts/run_plugin_checks.sh`: discover plugins via `list_packages.py`, run ruff (check + format --check) and mypy per plugin using each plugin's `.venv`; optional pytest when `RUN_PYTEST=1`; exit on first failure; mypy package name from path with fallback map.
  - Add root `install.sh`: discover plugins via `list_packages.py`, run each plugin's `./install.sh` for all plugins (do not stop on first failure), print succeeded/failed summary, exit non-zero if any failed; install pre-commit via pip if missing; run `pre-commit install` from repo root.
  - Add root `.pre-commit-config.yaml`: single local hook (plugin-checks) invoking `scripts/run_plugin_checks.sh`; language system, pass_filenames false; runs when files under `taps/` or `loaders/` change.
  - Documentation: README Development section (root `./install.sh`, pre-commit install, `pre-commit run --all-files`); docs/monorepo root-level tooling (install.sh and pre-commit discovery via list_packages.py); AI_CONTEXT_QUICK_REFERENCE Repo root commands and removal of "No repo-wide install.sh".
- **target-gcs-handle-decimal-in-records** — Details: [target-gcs-handle-decimal-in-records.md](_archive/target-gcs-handle-decimal-in-records/target-gcs-handle-decimal-in-records.md)
  - Add regression test for record with Decimal: test_record_with_decimal_serializes_to_valid_json (captures GCS writes, asserts JSONL decodes and numeric value correct; xfail until orjson default in task 03–04).
  - Add test that non-Decimal non-serializable value in record raises TypeError (test_non_serializable_non_decimal_type_raises_type_error; black-box, documents contract).
  - Add _json_default helper and decimal import in sinks.py (module-private; returns float for Decimal, raises TypeError otherwise; not yet wired at orjson call sites).
  - Wire default=_json_default at both orjson.dumps call sites in sinks.py (_process_record_single_or_chunked and _process_record_partition_by_field); remove xfail from Decimal regression test.
  - Verify full test suite and lint/type checks: pytest, ruff check, ruff format --check, mypy gcs_target all pass.
- **target-gcs hive partitioning by field** — Details: [target-gcs-hive-partitioning-by-field.md](_archive/target-gcs-hive-partitioning-by-field/target-gcs-hive-partitioning-by-field.md)
  - Add partition_date_field and partition_date_format to config schema (optional strings); schema and validation tests in test_sinks.py.
  - Add unit tests for get_partition_path_from_record (valid ISO date/datetime, fallback format, missing field, invalid value, custom format); stub in sinks.py until task 03.
  - Implement get_partition_path_from_record: parse record field (ISO date/datetime, fallback %Y-%m-%d); use fallback_date when missing or unparseable; add DEFAULT_PARTITION_DATE_FORMAT (Hive-style); remove xfail from partition resolution tests.
  - Add optional date_fn to GCSSink.__init__ and _current_partition_path when partition_date_field is set; extend build_sink in tests to accept and pass date_fn (task 04).
  - Add _build_key_for_record(record, partition_path) and partition_date in key when partition_date_field set; key_name returns current key or empty when partition-by-field on; tests for key differs by partition, Hive path in key, fallback path, unset leaves behaviour unchanged (task 05).
  - Integrate partition-by-field into process_record and handle lifecycle: resolve partition path per record; on partition change close handle and clear state, reset chunk index; chunk rotation within partition; build key via _build_key_for_record; when partition returns use new key (no reopen). Tests: chunking with same partition yields two keys; partition A→B→A yields three distinct keys (task 06).
  - Regression and backward compatibility: full test suite passes; add explicit test that when partition_date_field is unset, key_name uses run date and single-key-per-stream behaviour is unchanged; use date_fn in key_name when unset for deterministic tests (task 07).
  - Documentation and sample config: README config table for partition_date_field and partition_date_format; subsection on Hive partitioning by record date field ({partition_date} token, fallback, example, chunking); sample.config.json and meltano.yml with partition options and key_naming_convention using {partition_date} (task 08).
  - AI context and docstrings: update docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md (config, {partition_date} token, partition-by-field behaviour, extension points); verify/add docstrings in sinks.py for get_partition_path_from_record, GCSSink, _build_key_for_record; verify target.py property descriptions (task 09).
- **target-gcs file chunking by record count** — Details: [target-gcs-file-chunking-by-record-count.md](_archive/target-gcs-file-chunking-by-record-count/target-gcs-file-chunking-by-record-count.md)
  - Add optional `max_records_per_file` to target config schema; schema and validation tests in test_sinks.py.
  - Add tests for chunking disabled: one key and one handle, key without chunk_index (backward compatibility).
  - Add per-stream state (_records_written_in_current_file, _chunk_index) and optional time_fn in GCSSink; key_name uses injectable time for deterministic tests.
  - Add tests for rotation at threshold, key format with chunk_index, and record integrity (marked xfail until tasks 05 and 06).
  - Key computation with chunk index: GCSSink.key_name reads max_records_per_file from config and adds chunk_index to format map when chunking enabled so key_naming_convention may use {chunk_index}; no rotation logic (task 06).
  - Rotation and process_record: before write, rotate when _records_written_in_current_file >= max_records_per_file (close handle with flush if supported, clear key, increment chunk_index, reset counter); write record; increment counter when chunking enabled. Task 04 rotation/key/record-integrity tests enabled and passing.
  - Handle flush on close: in _rotate_to_new_chunk, flush GCS write handle before close when it supports flush (hasattr guard); docstring notes behaviour so handles without flush do not raise.
  - Documentation and sample config: README (max_records_per_file, {chunk_index}, chunking behaviour), sinks.py docstrings/comments, sample.config.json and meltano.yml, AI_CONTEXT.
- **restful-api-tap is_sorted stream config** — Details: [restful-api-tap-is-sorted-stream-config.md](_archive/restful-api-tap-is-sorted-stream-config/restful-api-tap-is-sorted-stream-config.md)
  - Add black-box tests for stream-level `is_sorted` (true, omitted, false, multi-stream); tests marked xfail until tasks 02–05 wire config.
  - Add `is_sorted` stream setting (boolean) to plugin schema in meltano.yml.
  - Wire `is_sorted` in discover_streams: resolve from stream config (default False), pass to DynamicStream; enable all four is_sorted tests.
  - Add `is_sorted` to common_properties in tap.py (BooleanType, default False) so config validation accepts the key.
  - Add `is_sorted` param to DynamicStream (streams.py); set instance attribute and override property for SDK compatibility.
  - Document stream-level `is_sorted` in README (when to use, effect); verify DynamicStream.__init__ Args; add discover_streams() docstring line.
- **Plugin source folder naming** — Details: [plugin-source-folder-naming.md](_archive/plugin-source-folder-naming/plugin-source-folder-naming.md)
  - Source directories and package names aligned with plugin directory names (dashes → underscores): `taps/restful-api-tap` uses `restful_api_tap` (formerly `tap_rest_api_msdk`); `loaders/gcs-loader` uses `gcs_loader` (formerly `target_gcs`).
  - pyproject.toml, imports, scripts (install.sh, tox.ini, meltano.yml), and docs updated per plugin; provenance notes added in READMEs and AI_CONTEXT.
- **Plugin standards and CI matrix** — Details: [plugin-standards-and-ci-matrix.md](_archive/plugin-standards-and-ci-matrix/plugin-standards-and-ci-matrix.md)
  - Discovery script tests (TDD): `scripts/tests/` with black-box tests for `list_packages.py`; run via `pytest scripts/tests` from repo root.
  - Discovery script implementation: `scripts/list_packages.py` (stdlib only, pathlib); optional ROOT, exclude .git/.venv/_archive/node_modules; sorted one path per line, exit 0.
  - gcs-loader tests moved to package root: `loaders/gcs-loader/tests/` (from `target_gcs/tests/`); README updated; pytest discovers from package root.
  - gcs-loader install.sh: add ruff (check + format --check) and mypy target_gcs; order ruff → mypy → pytest; exit code = pytest.
  - restful-api-tap install.sh: run uv run pytest, ruff check/format --check, mypy tap_rest_api_msdk; exit code = pytest; tox removed from primary contract.
  - GitHub workflow: `.github/workflows/plugin-matrix.yml` — discover job runs `scripts/list_packages.py`, converts stdout to JSON matrix, runs script tests; test job matrix over packages, runs `bash install.sh` per package. Triggers on push/PR to main or master with path filters (scripts/, taps/, loaders/, .github/).
  - Documentation: `docs/monorepo/README.md` — added "CI and plugin standards" (matrix over pyproject.toml dirs, install.sh runs uv/pytest/ruff/mypy, tests in package root `tests/`). Plugin READMEs (gcs-loader, restful-api-tap) updated to state install.sh runs pytest, ruff, mypy; CI relies on install.sh.
