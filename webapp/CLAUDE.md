# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Z-Image webapp: FastAPI backend + SvelteKit frontend for the Z-Image 6B image generation model. The model loads once at startup and stays in memory for fast subsequent generations.

**Hardware target:** Apple M4 Pro with 24GB RAM (MPS backend)

## Common Commands

### Development
```bash
# Full stack (dev mode with hot reload)
./start.sh --dev

# Backend only (from webapp/)
./start-backend.sh

# Frontend only (from webapp/frontend/)
npm run dev
```

### Build & Check
```bash
# Frontend build
cd frontend && npm run build

# TypeScript check
cd frontend && npm run check

# Lint Python (from repo root)
ruff check src && black --check . && isort --check .
```

### Installation
```bash
# Python deps (from repo root)
pip install -e .[dev]

# Backend deps
pip install -r backend/requirements.txt

# Frontend deps
cd frontend && npm install
```

## Architecture

```
webapp/
├── backend/
│   ├── server.py          # FastAPI app: REST + WebSocket endpoints
│   ├── model_manager.py   # Singleton model loader with warmup
│   ├── image_store.py     # Image history persistence
│   └── requirements.txt
├── frontend/
│   ├── src/routes/        # SvelteKit pages (+page.svelte, +layout.svelte)
│   ├── src/lib/stores/    # Svelte stores including generation.ts (API client)
│   ├── src/app.css        # Theme definitions (studio, midnight, nordic)
│   └── package.json
├── generated/             # Image storage (gitignored)
├── start.sh               # Launches both backend + frontend
└── start-backend.sh       # Backend only launcher
```

### Key Integration Points

**Frontend → Backend:** HTTP REST (`localhost:8000`) + WebSocket for progress updates

**Backend → Model:** `ModelManager` singleton in `model_manager.py` loads Z-Image components once, runs warmup for common sizes, reuses for all requests

**Generation flow:** Prompt → FastAPI → ModelManager → Z-Image pipeline → Image saved to `generated/` → URL returned to frontend

## Quality Presets (M4 Pro Performance)

| Quality | Resolution (16:9) | Steps | Time |
|---------|-------------------|-------|------|
| Fast | 512x288 | 2 | ~30-35s |
| Draft | 640x368 | 4 | ~45-55s |
| Standard | 1024x576 | 6 | ~60-80s |
| High | 1280x720 | 8 | ~90-120s |
| Ultra | 1536x864 | 8 | ~150-180s |

**Note:** First generation per image size incurs ~30s MPS compilation overhead. Warmup pre-compiles Fast and Draft sizes.

## Performance Optimizations Applied

1. **VAE in bfloat16** - Faster decoding (model_manager.py:91-93)
2. **Warmup on startup** - Pre-compiles Fast/Draft sizes (model_manager.py:108-144)
3. **Quality-based steps** - Fewer steps for lower quality (server.py:44-51)
4. **Sequential multi-image** - Generates one at a time with unique seeds (server.py:158-226)
5. **max_sequence_length=256** - Faster text encoding (server.py:213)
6. **Generation lock** - Prevents concurrent MPS ops that cause SIGSEGV crashes (model_manager.py:37, server.py:184-185)

## Important Patterns

### Import Pattern (CRITICAL)
The repo uses absolute imports WITHOUT `src.` prefix:
```python
# Correct
from utils import load_from_local_dir
from zimage import generate

# Wrong - don't do this
from src.utils import ...
```
This works because scripts set `PYTHONPATH=src:$PYTHONPATH` (see start.sh).

### Ports
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

### Environment Variables
- `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0` - Apple Silicon memory optimization (set in start.sh)
- `ZIMAGE_ATTENTION` - Attention backend (`_native_flash` default for MPS)
- `ZIMAGE_HEIGHT`, `ZIMAGE_WIDTH` - Image dimensions (CLI only)
- `ZIMAGE_SKIP_WARMUP` - Set to `1`, `true`, or `yes` to skip warmup on startup

## UI Features

- **Sound notification** - Plays ding when generation completes (toggle in settings bar, default ON)
- **Timer** - Shows elapsed time in `Xm Ys` format during generation
- **Themes** - Studio (warm), Midnight (dark), Nordic (cool light)
- **Quality presets** - Fast/Draft/Standard/High/Ultra with optimized steps per level

## Known Issues & Bottlenecks

1. **MPS compilation overhead** - First generation per image size takes +30s
2. **Text encoder is 8GB Qwen3** - Takes ~4s per prompt encoding
3. **Multi-image uses same seed base** - Seeds are seed, seed+1, seed+2, etc.

## Canonical Guidelines

Refer to `../AGENTS.md` for comprehensive coding style, error handling, and contribution guidelines. Key points:
- Use `loguru.logger` for logging
- Type hints on all public functions
- Avoid bare `except:`
- Run linters before commits
