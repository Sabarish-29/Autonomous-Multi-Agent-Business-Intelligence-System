#!/usr/bin/env bash
set -euo pipefail

# Recreate a clean venv and install DataGenie with dependency groups via uv.
# Usage:
#   ./scripts/setup_prod_env.sh               # core install
#   ./scripts/setup_prod_env.sh analytics     # add analytics deps
#   ./scripts/setup_prod_env.sh reporting     # add reporting deps
#   ./scripts/setup_prod_env.sh test          # add test deps
#   ./scripts/setup_prod_env.sh all           # add analytics+reporting+test

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

EXTRA="${1:-}"  # optional: analytics|reporting|test|all

cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi

rm -rf "$VENV_DIR"
uv venv --python 3.11 "$VENV_DIR"

case "$EXTRA" in
  "")
    uv pip install -e .
    ;;
  analytics|reporting|test)
    uv pip install -e ".[${EXTRA}]"
    ;;
  all)
    uv pip install -e ".[analytics,reporting,test]"
    ;;
  *)
    echo "Unknown extra group: $EXTRA" >&2
    echo "Valid: analytics | reporting | test | all" >&2
    exit 2
    ;;
esac

# Quick health checks
uv pip check
