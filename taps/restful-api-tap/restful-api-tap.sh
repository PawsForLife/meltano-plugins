#!/bin/sh
set -e

# Run the tap from any directory using the uv-managed virtual environment.

unset VIRTUAL_ENV

TOML_DIR=$(dirname "$0")
cd "$TOML_DIR" || exit
uv sync --extra dev 1>&2
uv run restful-api-tap "$@"
