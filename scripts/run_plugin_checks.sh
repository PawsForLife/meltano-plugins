#!/usr/bin/env bash
# Run ruff (check + format --check) and mypy per plugin using each plugin's .venv.
# Discovery via scripts/list_packages.py; optional pytest when RUN_PYTEST=1.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Derive mypy package name from last path component (e.g. taps/restful-api-tap -> restful-api-tap).
# Fallback map for known exceptions; default: target-* -> *_target, else replace - with _.
get_mypy_package() {
  local path="$1"
  local comp="${path##*/}"
  case "$comp" in
    restful-api-tap) echo "restful_api_tap" ;;
    target-gcs) echo "gcs_target" ;;
    target-*)
      local suffix="${comp#target-}"
      suffix="${suffix//-/_}"
      echo "${suffix}_target"
      ;;
    *)
      echo "${comp//-/_}"
      ;;
  esac
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
    if [[ -n "${RUN_PYTEST:-}" && "${RUN_PYTEST}" != "0" ]]; then
      .venv/bin/pytest
    fi
  }
  run_plugin
  rc=$?
  if [[ $rc -ne 0 ]]; then
    exit $rc
  fi
done < <(python "$ROOT/scripts/list_packages.py" "$ROOT")
