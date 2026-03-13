# target-gcs

`target-gcs` is a Singer **target** that loads data into the **destination** (Google Cloud Storage). The Python package is `target_gcs`. In Meltano, this target runs as a **loader**.

Build with the [Meltano Target SDK](https://sdk.meltano.com).

## Installation

**Use from a Meltano project (recommended):** This is a custom plugin (not on the Meltano Hub or PyPI). Add the loader to your project's `meltano.yml` with `pip_url` and `namespace: target_gcs`; do not set `variant`. Then run `meltano install`.

```yaml
plugins:
  loaders:
    - name: target-gcs
      namespace: target_gcs
      pip_url: git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=loaders/target-gcs
```

See the [repo root README](../../README.md) for full instructions and troubleshooting.

**Local development:** From the repo root, clone and run:

```bash
cd loaders/target-gcs
./install.sh
```

Or install [uv](https://docs.astral.sh/uv/getting-started/installation/) and run `uv sync --extra dev` in this directory.

## Supported formats

JSONL is the only supported output format

## Configuration

The target is configured via [Meltano](https://meltano.com/): settings and `config` are defined in `meltano.yml`, with optional overrides via environment variables (see table below). For an example structure, see `meltano.yml` in this directory.

### Accepted Config Options

| Property              | Env variable                         | Type    | Required | Default       | Description                                                                                                                                                                                                                                                                                      |
| --------------------- | ------------------------------------ | ------- | -------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| bucket_name           | TARGET_GCS_BUCKET_NAME               | string  | yes      | n/a           | The name of the GCS bucket                                                                                                                                                                                                                                                                       |
| date_format           | TARGET_GCS_DATE_FORMAT               | string  | no       | %Y-%m-%d      | If `{date}` token is used in key_naming_convention, the date will be formatted with this format string                                                                                                                                                                                           |
| key_prefix            | TARGET_GCS_KEY_PREFIX                | string  | no       | None          | A static prefix before the generated key names. If this and `key_naming_convention` are both provided, they will be combined.                                                                                                                                                                    |
| key_naming_convention | TARGET_GCS_KEY_NAMING_CONVENTION     | string  | no       | Conditional: when `hive_partitioned` is true and omitted → `{stream}/{partition_date}/{timestamp}.jsonl`; when false/omitted and omitted → `{stream}_{timestamp}.jsonl` | Template for object keys. When omitted: if `hive_partitioned` is true, default is `{stream}/{partition_date}/{timestamp}.jsonl` (hive-style); if false or omitted, default is `{stream}_{timestamp}.jsonl`. Tokens: `date`, `stream`, `timestamp`. When `hive_partitioned` is true, `{partition_date}` and `{hive}` (alias for `{partition_date}`) are available. When chunking is enabled (`max_records_per_file` > 0), `{chunk_index}` (0-based) is also available and `{timestamp}` is recomputed at the start of each new chunk. Date format uses [python date format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). |
| max_records_per_file  | TARGET_GCS_MAX_RECORDS_PER_FILE      | integer | no       | 0             | When set and greater than 0, the target rotates to a new GCS object after that many records per stream; when 0 or omitted, one file per stream per run (unchanged).                                                                                                                              |
| hive_partitioned      | TARGET_GCS_HIVE_PARTITIONED          | boolean | no       | false         | When true, Hive-style partitioning from stream schema (`x-partition-fields`) or current date; path built per record; `{partition_date}` and `{hive}` available in key template.                                                                                                                |

**File chunking (optional):** When `max_records_per_file` is set and greater than 0, the target writes multiple files per stream; each file contains at most that many records, and the last file for a stream may have fewer. When 0 or omitted, one file per stream per run is written (no chunking).

**Naming with chunking:** You can keep keys unique across chunks in two ways. (1) **Timestamp-based:** Use `{timestamp}` (and optionally `{date}`, `{stream}`). The timestamp is recomputed at the start of each new chunk, so keys differ unless consecutive chunks start within the same timestamp granularity window (e.g. two chunks starting at 12:00:00.500 and 12:00:00.999 get identical `{timestamp}` values). `{chunk_index}` is not required. (2) **Chunk-index-based:** Include `{chunk_index}` in the pattern, so each chunk has a distinct key regardless of timing—useful when many chunks can start within the same second, or when you want a fixed or run-level name with only the index varying.

See `meltano.yml` in this directory for an example `config` block; it may include `max_records_per_file` to demonstrate chunking.

### Hive partitioning (schema-driven)

The sink uses three extraction patterns (simple, dated, partitioned) selected by config and stream schema; behaviour and key shapes are unchanged. When `hive_partitioned` is **true**, the target builds a Hive-style partition path per record and exposes it as the `{partition_date}` token in `key_naming_convention`. With no custom key template, object keys follow `{stream}/{partition_date}/{timestamp}.jsonl`. `{hive}` is an alias for `{partition_date}`.

**Path from stream schema:** If the stream schema defines `x-partition-fields` (array of property names at the top level), the path is built from those fields in **array order**. Each field must be in `properties`, in `required`, and non-nullable; the target validates this at sink init and raises `ValueError` if invalid. Every partition segment is `key=value`: literal segments are always emitted as `field_name=value` (e.g. `region=eu`); date segments are `year=YYYY/month=MM/day=DD` (Hive-style). For each field: **Date-parseable** values (e.g. ISO date/datetime strings) → one segment `year=.../month=.../day=...`. **Other values** → literal segment `field_name=value`; path-unsafe characters (e.g. `/`) are replaced (e.g. with `_`). **Fallback when no x-partition-fields:** If the stream has no `x-partition-fields` or it is empty, the target uses the **current date** (run date) for the partition path. **Removal of old settings:** `partition_date_field` and `partition_date_format` are no longer supported; use `hive_partitioned: true` and define partition fields on the stream schema via `x-partition-fields`.

**Example:** Stream schema with `x-partition-fields` (e.g. `["region", "created_at"]`); set the loader `config` in `meltano.yml`:

```yaml
plugins:
  loaders:
    - name: target-gcs
      namespace: target_gcs
      pip_url: git+https://github.com/PawsForLife/meltano-plugins.git#subdirectory=loaders/target-gcs
      config:
        bucket_name: my-bucket
        hive_partitioned: true
        key_naming_convention: "{stream}/{partition_date}/{timestamp}.jsonl"
```

Resulting path order: first segment from `region` (literal, e.g. `region=eu`), then `year=.../month=.../day=...` from `created_at`. For `x-partition-fields: ["country", "event_date"]`, paths look like `country=UK/year=2024/month=03/day=13/` (literal then date).

**Chunking:** When both `max_records_per_file` and `hive_partitioned` are set, the target rotates to a new file after that many records **within the current partition**. The partition path stays the same; the new file uses a new timestamp (and optionally `{chunk_index}`) in the key.

A full list of supported settings and capabilities for this
target is available by running:

```bash
target-gcs --about
```

### Authentication

Authentication uses [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials). No credentials path is accepted in the target config file. To use a service account key file, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of the JSON key file; the target always uses the default client and does not read a credentials path from the config file.

### Configure using environment variables

Configuration is recommended via Meltano (`meltano.yml`) or environment variables rather than JSON config files. This Singer target will automatically import any environment variables within the working directory's `.env` if `--config=ENV` is provided, so that config can be supplemented or overridden by matching environment variables set in the terminal context or in the `.env` file.

### Source Authentication and Authorization

This target writes to GCS only; it does not require source-specific authentication. GCS access uses [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) or `GOOGLE_APPLICATION_CREDENTIALS` as described in the Authentication section above.

## Usage

You can easily run `target-gcs` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Target Directly

```bash
target-gcs --version
target-gcs --help
# With Meltano (config from meltano.yml; recommended):
meltano run tap-carbon-intensity target-gcs
```

For non-Meltano use, supply config via environment variables: `tap-carbon-intensity | target-gcs --config=ENV` (with `TARGET_GCS_*` vars or a `.env` file in the working directory).

## Developer Resources

Requires **Python 3.12+**. The project uses **uv** for dependency management and **Ruff** and **mypy** for linting, formatting, and type checking. The lockfile is `uv.lock`.

### Initialize your Development Environment

**Option A (recommended):** Run the install script to ensure uv is available, create a clean virtual environment, install dependencies (including dev), and run pytest, ruff, and mypy:

```bash
./install.sh
```

**Option B:** Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and then:

```bash
uv sync --extra dev
```

### Lint, format, and type check

```bash
uv run ruff check .
uv run ruff format .          # format in place; CI runs ruff format --check
uv run mypy target_gcs
```

### Create and Run Tests

Create tests in the package-root `tests/` directory and run:

```bash
uv run pytest
```

You can also run the `target-gcs` CLI directly:

```bash
uv run target-gcs --help
```

### Testing with [Meltano](https://meltano.com/)

_**Note:** This target will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any _"TODO"_ items listed in
the file.

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install Meltano with uv (if needed)
uv tool install meltano
# From this directory, install plugins
cd loaders/target-gcs
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke target-gcs --version
# OR run a test `elt` pipeline with the Carbon Intensity sample tap:
meltano elt tap-carbon-intensity target-gcs
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the Meltano SDK to
develop your own Singer taps and targets.
