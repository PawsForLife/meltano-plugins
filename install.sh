#!/usr/bin/env bash
# Bootstrap all plugins by running each plugin's install.sh; discovery via list_packages.py.
# Runs every package install, then ensures pre-commit is available and installs only the pre-push hook (checks run on push, not on commit).
# Prints which package is being installed before each run and a final summary of succeeded/failed.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUCCEEDED=()
FAILED=()

# Discover packages once; capture output and exit status so discovery failures are propagated.
PACKAGES_FILE=$(mktemp)
trap 'rm -f "$PACKAGES_FILE"' EXIT
if ! python "$ROOT/scripts/list_packages.py" "$ROOT" > "$PACKAGES_FILE"; then
  echo "Package discovery failed (list_packages.py)." >&2
  exit 1
fi

# Run each plugin's install.sh; record success/failure (do not stop on first failure).
while IFS= read -r path || [[ -n "$path" ]]; do
  path="$(echo "$path" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$path" ]] && continue
  echo "==> Installing package: $path"
  if (cd "$ROOT/$path" && ./install.sh); then
    SUCCEEDED+=("$path")
  else
    FAILED+=("$path")
  fi
done < "$PACKAGES_FILE"

# Ensure pre-commit is available; install via pip if missing.
PRECOMMIT_FAILED=0
if ! command -v pre-commit &>/dev/null; then
  echo "==> Installing pre-commit..."
  if command -v pip3 &>/dev/null; then
    pip3 install pre-commit
    if [[ $? -ne 0 ]]; then
      FAILED+=("pre-commit (pip install)")
      PRECOMMIT_FAILED=1
    fi
  elif command -v pip &>/dev/null; then
    pip install pre-commit
    if [[ $? -ne 0 ]]; then
      FAILED+=("pre-commit (pip install)")
      PRECOMMIT_FAILED=1
    fi
  else
    echo "pre-commit not found and neither pip nor pip3 available." >&2
    FAILED+=("pre-commit (pip install)")
    PRECOMMIT_FAILED=1
  fi
fi

# Install only the pre-push hook (checks run on push, not on commit). Uninstall pre-commit hook if present.
if command -v pre-commit &>/dev/null; then
  PRECOMMIT_FAILED=0
  cd "$ROOT"
  pre-commit uninstall 2>/dev/null || true
  if ! pre-commit install --hook-type pre-push; then
    PRECOMMIT_FAILED=1
  fi
fi

# Final summary: one line for succeeded, one for failed (including pre-push hook when applicable).
echo ""
echo "--- Summary ---"
if [[ ${#SUCCEEDED[@]} -gt 0 ]] || { [[ $PRECOMMIT_FAILED -eq 0 ]] && command -v pre-commit &>/dev/null; }; then
  line="Succeeded: ${SUCCEEDED[*]}"
  [[ $PRECOMMIT_FAILED -eq 0 ]] && command -v pre-commit &>/dev/null && line="$line pre-push"
  echo "$line"
fi
if [[ ${#FAILED[@]} -gt 0 ]] || [[ $PRECOMMIT_FAILED -ne 0 ]]; then
  line="Failed: ${FAILED[*]}"
  [[ $PRECOMMIT_FAILED -ne 0 ]] && line="$line pre-push"
  echo "$line"
fi

if [[ ${#FAILED[@]} -gt 0 ]] || [[ $PRECOMMIT_FAILED -ne 0 ]]; then
  exit 1
fi
exit 0
