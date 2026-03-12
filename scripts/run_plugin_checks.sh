#!/usr/bin/env bash
# Run ruff (check + format --check), mypy, and pytest per plugin using each plugin's .venv.
# Discovery via scripts/list_packages.py.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Derive mypy package name: last path component with hyphens replaced by underscores
# (e.g. loaders/target-gcs -> target_gcs).
get_mypy_package() {
  local path="$1"
  local comp="${path##*/}"
  echo "${comp//-/_}"
}

while IFS= read -r line || [[ -n "$line" ]]; do
  path="$(echo "$line" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$path" ]] && continue

  run_plugin() {
    cd "$ROOT/$path" || return 1
    if [[ ! -d .venv ]]; then
      echo "Missing .venv in $path; run root install.sh first." >&2
      return 1
    fi
    .venv/bin/ruff check .
    .venv/bin/ruff format --check .
    pkg="$(get_mypy_package "$path")"
    .venv/bin/mypy "$pkg"
    .venv/bin/pytest
  }
  run_plugin
  rc=$?
  if [[ $rc -ne 0 ]]; then
    exit $rc
  fi
done < <(python "$ROOT/scripts/list_packages.py" "$ROOT")
