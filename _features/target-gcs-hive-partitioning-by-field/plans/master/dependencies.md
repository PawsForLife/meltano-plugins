# Master Plan — Dependencies: Hive partitioning by record date field

**Feature:** target-gcs-hive-partitioning-by-field  
**See:** [overview.md](overview.md), [implementation.md](implementation.md)

---

## External dependencies

- **No new packages.** Date parsing uses stdlib only: `datetime.fromisoformat`, `datetime.strptime` with one or two formats (e.g. `%Y-%m-%d`). No `dateutil`, `pendulum`, or other third-party date libraries.
- **Existing:** `singer-sdk`, `google-cloud-storage`, `smart_open[gcs]`, `orjson`, etc. Unchanged.

---

## Internal dependencies

- **GCSTarget → GCSSink:** Unchanged. Target instantiates sink with config; sink reads `partition_date_field`, `partition_date_format` from `self.config`.
- **Partition resolution:** Used by GCSSink in `process_record` and by key building. No dependency on other custom modules.
- **Config file:** Target config (config file or Meltano-injected) supplies the new optional keys. No change to state file or Catalog usage.

---

## System and environment

- **Python:** Same as target-gcs (e.g. ≥3.8,<4.0 per pyproject.toml). No new runtime requirements.
- **GCS:** Same as today (ADC or `GOOGLE_APPLICATION_CREDENTIALS`). No new auth or bucket layout requirements beyond key path format.

---

## Configuration

- **Config file (Singer):** Optional keys:
  - `partition_date_field` (string): Record property name.
  - `partition_date_format` (string): strftime format; default in code `year=%Y/month=%m/day=%d` when omitted.
- **State file:** No change. Target does not read or write partition state in state file for this feature.
- **Catalog:** No change. Stream selection and schema flow unchanged.
- **Meltano:** If `meltano.yml` is updated, add settings for the two new options so users can set them via Meltano UI/env.

---

## Dependency injection (runtime)

- **time_fn:** Already present on GCSSink; used for `{timestamp}`. Kept for key building when partition-by-field is on.
- **date_fn:** New optional constructor argument. Used for partition fallback (and optionally for run-date in key when partition-by-field is off). Default `None` → use `datetime.today`. Tests pass a fixed `date_fn` for deterministic assertions.

---

## Build and test

- **Install:** `./install.sh` or `uv sync` in `loaders/target-gcs/`. No new steps.
- **Lint/type:** `ruff check .`, `ruff format --check`, `mypy gcs_target`. New code must pass.
- **Tests:** `uv run pytest` from plugin root. All new tests must pass; existing tests must remain green.
