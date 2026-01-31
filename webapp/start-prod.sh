#!/usr/bin/env bash
# Start Z-Image webapp in production mode
# Usage: ./start-prod.sh [--no-warmup]

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_DIR/../.venv"

echo "🚀 Starting Z-Image Studio (Production Mode)..."

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
else
    echo "⚠️  No venv found at $VENV_PATH"
    echo "   Please run: python3 -m venv ../.venv && ../.venv/bin/pip install -e ..[dev]"
    exit 1
fi

# Build frontend
echo "📦 Building frontend..."
cd "$PROJECT_DIR/frontend"
npm run build

# Start backend in background
echo "🔧 Starting backend server on http://localhost:8000..."
cd "$PROJECT_DIR/.."
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
if $SKIP_WARMUP; then
    export ZIMAGE_SKIP_WARMUP=1
    echo "⚡ Warmup disabled - faster startup, first generation may be slower"
fi
PYTHONPATH="$PROJECT_DIR/../src:$PROJECT_DIR" uvicorn webapp.backend.server:app \
    --host 0.0.0.0 \
    --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for model to load (this may take a few minutes)..."
sleep 3

# Start frontend preview
echo "🎨 Starting frontend on http://localhost:4173..."
cd "$PROJECT_DIR/frontend"
npm run preview -- --port 4173 --open &
FRONTEND_PID=$!

echo ""
echo "✨ Z-Image Studio is running in production mode!"
echo "   Frontend: http://localhost:4173"
echo "   Backend:  http://localhost:8000"
echo ""
echo "   Press Ctrl+C to stop"

# Handle shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    wait
}
trap cleanup EXIT

# Wait for either process to exit
wait
