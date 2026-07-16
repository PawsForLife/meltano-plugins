#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy tap_talon_one
uv run pytest
