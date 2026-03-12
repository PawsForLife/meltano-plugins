#!/usr/bin/env bash
# Bootstrap all plugins by running each plugin's install.sh; discovery via list_packages.py.
# Ensures pre-commit is available and installs only the pre-push hook (checks run on push, not on commit).
# Exits on first failure: discovery, any package install, or pre-commit setup.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Discover packages; exit on failure.
PACKAGES_FILE=$(mktemp)
trap 'rm -f "$PACKAGES_FILE"' EXIT
python "$ROOT/scripts/list_packages.py" "$ROOT" > "$PACKAGES_FILE" || {
  echo "Package discovery failed (list_packages.py)." >&2
  exit 1
}

# Run each plugin's install.sh; exit on first failure.
while IFS= read -r path || [[ -n "$path" ]]; do
  path="$(echo "$path" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$path" ]] && continue
  echo "==> Installing package: $path"
  (cd "$ROOT/$path" && ./install.sh) || {
    echo "Install failed for package: $path" >&2
    exit 1
  }
done < "$PACKAGES_FILE"

# Ensure pre-commit is available; install via pip if missing. Exit on failure.
if ! command -v pre-commit &>/dev/null; then
  echo "==> Installing pre-commit..."
  if command -v pip3 &>/dev/null; then
    pip3 install pre-commit || { echo "pip3 install pre-commit failed." >&2; exit 1; }
  elif command -v pip &>/dev/null; then
    pip install pre-commit || { echo "pip install pre-commit failed." >&2; exit 1; }
  else
    echo "pre-commit not found and neither pip nor pip3 available." >&2
    exit 1
  fi
fi

# Install only the pre-push hook (checks run on push, not on commit). Uninstall pre-commit hook if present.
cd "$ROOT"
pre-commit uninstall 2>/dev/null || true
pre-commit install --hook-type pre-push || {
  echo "pre-commit install --hook-type pre-push failed." >&2
  exit 1
}

exit 0
