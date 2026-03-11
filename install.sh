#!/usr/bin/env bash
# Bootstrap all plugins by running each plugin's install.sh; discovery via list_packages.py.
# Then install pre-commit if missing and run pre-commit install at repo root.

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Discover plugin paths and run each plugin's install.sh; stop on first failure.
while IFS= read -r path || [[ -n "$path" ]]; do
  path="$(echo "$path" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$path" ]] && continue
  (cd "$ROOT/$path" && ./install.sh)
done < <(python "$ROOT/scripts/list_packages.py" "$ROOT")

# Ensure pre-commit is available; install via pip if missing.
if ! command -v pre-commit &>/dev/null; then
  if command -v pip3 &>/dev/null; then
    pip3 install pre-commit
  elif command -v pip &>/dev/null; then
    pip install pre-commit
  else
    echo "pre-commit not found and neither pip nor pip3 available." >&2
    exit 1
  fi
fi

# Install git hooks from repo root.
cd "$ROOT"
pre-commit install
