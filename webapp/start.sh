#!/usr/bin/env bash
# Start the Z-Image web application
# Usage: ./start.sh [--dev]

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_DIR/../.venv"

echo "🚀 Starting Z-Image Studio..."

# Activate virtual environment
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
else
    echo "⚠️  No venv found at $VENV_PATH"
    echo "   Please run: python3 -m venv ../.venv && ../.venv/bin/pip install -e ..[dev]"
    exit 1
fi

# Check if this is dev mode
DEV_MODE=false
if [ "${1:-}" = "--dev" ]; then
    DEV_MODE=true
fi

# Start backend in background
echo "📦 Starting backend server on http://localhost:8000..."
cd "$PROJECT_DIR/.."
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
PYTHONPATH="$PROJECT_DIR/../src:$PROJECT_DIR" uvicorn webapp.backend.server:app \
    --host 0.0.0.0 \
    --port 8000 \
    $(if $DEV_MODE; then echo "--reload"; fi) &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for model to load (this may take a few seconds on first run)..."
sleep 3

# Start frontend
echo "🎨 Starting frontend on http://localhost:5173..."
cd "$PROJECT_DIR/frontend"
if $DEV_MODE; then
    npm run dev &
else
    npm run build && npm run preview &
fi
FRONTEND_PID=$!

echo ""
echo "✨ Z-Image Studio is starting!"
echo "   Frontend: http://localhost:5173"
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
