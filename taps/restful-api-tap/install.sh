#!/bin/bash
# Bootstrap environment: ensure uv, clean caches and .venv, create venv, install deps (including dev),
# then run ruff (check + format --check), mypy, and pytest. Exit code is that of pytest.
# Usage: ./install.sh (from package root). Optionally run tox locally for full env matrix.

set -e  # Exit on any error

GREEN='\e[0;32m'
RED='\e[0;31m'
NC='\e[0m' # No Color

printf "\n${GREEN}Starting installation process...${NC}\n"

# Clean Python cache files
printf "\n${GREEN}Cleaning Python cache files...${NC}\n"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.py[cod]" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
rm -rf .venv 2>/dev/null || true
rm -rf dist 2>/dev/null || true
printf "\n${GREEN}Cache cleanup complete${NC}\n"

# Installing UV
printf "\n${GREEN}Checking UV installation...${NC}\n"
if ! command -v uv &> /dev/null; then
  printf "\n${GREEN}Installing UV via official installer...${NC}\n"
  UV_INSTALLER=$(mktemp -t uv-install.XXXXXX.sh)
  trap 'rm -f "$UV_INSTALLER"' EXIT
  curl -LsSf -o "$UV_INSTALLER" https://astral.sh/uv/install.sh || { printf "\n${RED}Failed to download UV installer${NC}\n"; exit 1; }
  printf "\n${GREEN}Installer saved to %s. Review with: cat %s${NC}\n" "$UV_INSTALLER" "$UV_INSTALLER"
  printf "${GREEN}Press Enter to run installer, or Ctrl+C to abort...${NC}\n"
  read -r
  sh "$UV_INSTALLER" || { printf "\n${RED}Failed to install UV${NC}\n"; exit 1; }
  trap - EXIT
  rm -f "$UV_INSTALLER"
  export PATH="$HOME/.local/bin:$PATH"
  if ! command -v uv &> /dev/null; then
    printf "\n${RED}UV installed but not on PATH. Add \$HOME/.local/bin to PATH and re-run.${NC}\n"
    exit 1
  fi
else
  printf "\n${GREEN}UV is already installed${NC}\n"
fi

# Create and activate virtual environment
printf "\n${GREEN}Creating virtual environment...${NC}\n"
uv venv --python 3.12 || { printf "\n${RED}Failed to create virtual environment${NC}\n"; exit 1; }
source .venv/bin/activate || { printf "\n${RED}Failed to activate virtual environment${NC}\n"; exit 1; }

# Verify virtual environment activation
if [[ -z "$VIRTUAL_ENV" ]]; then
    printf "\n${RED}Virtual environment activation failed${NC}\n"
    exit 1
fi

# Install project (editable, including dev dependencies)
printf "\n${GREEN}Installing project dependencies...${NC}\n"
uv sync --extra dev || { printf "\n${RED}Failed to install project dependencies${NC}\n"; exit 1; }

# Lint and type-check (order: ruff, mypy, then pytest)
printf "\n${GREEN}Running ruff check...${NC}\n"
uv run ruff check .
printf "\n${GREEN}Running ruff format --check...${NC}\n"
uv run ruff format --check .
printf "\n${GREEN}Running mypy...${NC}\n"
uv run mypy restful_api_tap

# Run tests; script exit code = pytest exit code
printf "\n${GREEN}Running pytest...${NC}\n"
uv run pytest
exit $?
