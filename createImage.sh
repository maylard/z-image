#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_DIR/.venv"

# Create and activate venv if it exists, otherwise use system Python
if [ -d "$VENV_PATH" ]; then
  source "$VENV_PATH/bin/activate"
elif [ ! -d "$VENV_PATH" ] && command -v python3 >/dev/null; then
  echo "No venv found. Using system Python. Create one with: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
fi

# Run with src in PYTHONPATH (matches inference.py import pattern)
PYTHONPATH="$PROJECT_DIR/src:${PYTHONPATH:-}" python "$PROJECT_DIR/createImage.py"
