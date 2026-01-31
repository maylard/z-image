#!/usr/bin/env bash
# Start only the backend server (for development)
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_DIR/../.venv"

# Activate virtual environment
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
fi

echo "🚀 Starting Z-Image backend on http://localhost:8000..."
cd "$PROJECT_DIR/.."
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
PYTHONPATH="$PROJECT_DIR/../src:$PROJECT_DIR" uvicorn webapp.backend.server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload
