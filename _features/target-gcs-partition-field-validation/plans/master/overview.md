# Implementation Plan — Overview

## Executive Summary

This feature adds **partition-date-field schema validation** to target-gcs. When `partition_date_field` is set in config, the sink validates at initialization that (1) the field exists in the stream schema and (2) the property type is date-parseable (not null-only, not integer/boolean/etc.). Validation runs once per stream in the sink’s `__init__` after the Singer SDK has set `self.schema`. On failure, a clear `ValueError` is raised with stream name, field name, and reason.

## Purpose

- **Fail fast**: Misconfiguration (typo in field name, or field that is null-only or non–date-parseable) is caught before any records are processed.
- **Clear errors**: Users see stream name, field name, and reason (missing from schema; null-only; type not date-parseable) instead of runtime KeyError or ParserError later.

## High-Level Objectives

| Objective | Success criteria |
|-----------|-------------------|
| Schema presence | If `partition_date_field` is set, the field must exist in `schema["properties"]`. |
| Date-parseable type | Property type must allow values parseable to a date: allow `string` (with or without `format` date/date-time); allow nullable string; reject null-only and non-string/non–date-like types. |
| Single validation point | Validation runs in sink `__init__` after `super().__init__`, using `self.schema`. |
| No API change | Config and Singer message contracts unchanged; validation is internal to the sink. |

## Key Requirements and Constraints

- **TDD**: Tests written first; implementation follows. See [testing.md](testing.md).
- **Models/interfaces first**: Helper signature and error contract defined before implementation. See [interfaces.md](interfaces.md).
- **Dependency injection**: No new non-deterministic deps inside validation; schema and config are already passed into the sink.
- **Black-box tests**: Assert raised exception or success; do not assert on call counts or log lines.

## Relationship to Existing Systems

- **target-gcs only**: No changes to taps, shared libs, or CI. See [architecture.md](architecture.md).
- **GCSSink**: Validation is invoked from `GCSSink.__init__` when `partition_date_field` is set; `process_record` and `get_partition_path_from_record` are unchanged.
- **Config**: `partition_date_field` remains optional in `GCSTarget.config_jsonschema`; no new required config.
