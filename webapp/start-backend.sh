#!/usr/bin/env bash
# Start only the backend server (for development)
# Usage: ./start-backend.sh [--no-warmup]
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_DIR/../.venv"

# Parse arguments
SKIP_WARMUP=false
for arg in "$@"; do
    if [ "$arg" = "--no-warmup" ] || [ "$arg" = "--skip-warmup" ]; then
        SKIP_WARMUP=true
    fi
done

# Activate virtual environment
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
fi

echo "🚀 Starting Z-Image backend on http://localhost:8000..."
cd "$PROJECT_DIR/.."
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
if $SKIP_WARMUP; then
    export ZIMAGE_SKIP_WARMUP=1
    echo "⚡ Warmup disabled - faster startup, first generation may be slower"
fi
PYTHONPATH="$PROJECT_DIR/../src:$PROJECT_DIR" uvicorn webapp.backend.server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload
