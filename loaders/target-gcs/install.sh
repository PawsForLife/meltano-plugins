#!/bin/bash
# Bootstrap environment: ensure uv, clean caches and .venv, create venv, install deps (including dev), run pytest, ruff, and mypy.
# Usage: ./install.sh (from package root). Exit code is that of pytest (runs ruff, mypy, then pytest).

set -e

GREEN='\e[0;32m'
RED='\e[0;31m'
NC='\e[0m'

printf "\n${GREEN}Starting installation...${NC}\n"

# Ensure uv on PATH; install if missing
if ! command -v uv &> /dev/null; then
  printf "\n${GREEN}Installing uv via official installer...${NC}\n"
  UV_INSTALLER=$(mktemp -t uv-install.XXXXXX.sh)
  trap 'rm -f "$UV_INSTALLER"' EXIT
  curl -LsSf -o "$UV_INSTALLER" https://astral.sh/uv/install.sh || { printf "\n${RED}Failed to download uv installer${NC}\n"; exit 1; }
  sh "$UV_INSTALLER" || { printf "\n${RED}Failed to install uv${NC}\n"; exit 1; }
  trap - EXIT
  rm -f "$UV_INSTALLER"
  export PATH="${HOME}/.local/bin:${PATH}"
  if ! command -v uv &> /dev/null; then
    printf "\n${RED}uv installed but not on PATH. Add \$HOME/.local/bin to PATH and re-run.${NC}\n"
    exit 1
  fi
else
  printf "\n${GREEN}uv is already installed${NC}\n"
fi

# Clean existing venv and Python caches
printf "\n${GREEN}Cleaning environment...${NC}\n"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.py[cod]" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
rm -rf .venv 2>/dev/null || true
printf "\n${GREEN}Cleanup complete${NC}\n"

# Create venv and install project (editable, including dev dependencies)
printf "\n${GREEN}Creating virtual environment...${NC}\n"
uv venv || { printf "\n${RED}Failed to create virtual environment${NC}\n"; exit 1; }
source .venv/bin/activate || { printf "\n${RED}Failed to activate virtual environment${NC}\n"; exit 1; }
if [[ -z "${VIRTUAL_ENV}" ]]; then
  printf "\n${RED}Virtual environment activation failed${NC}\n"
  exit 1
fi

printf "\n${GREEN}Installing project dependencies...${NC}\n"
uv sync --extra dev || { printf "\n${RED}Failed to install dependencies${NC}\n"; exit 1; }

# Lint and type-check
printf "\n${GREEN}Running ruff check...${NC}\n"
uv run ruff check .
printf "\n${GREEN}Running ruff format --check...${NC}\n"
uv run ruff format --check .
printf "\n${GREEN}Running mypy...${NC}\n"
uv run mypy gcs_target

# Run tests; script exit code = pytest exit code
printf "\n${GREEN}Running pytest...${NC}\n"
uv run pytest
exit $?
