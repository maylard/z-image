# Z-Image Webapp for Apple Silicon

A modern web interface for the Z-Image 6B text-to-image model, optimized for Apple M4 Pro.

## About This Project

This project is based on [**Z-Image**](https://github.com/Tongyi-MAI/Z-Image) by Tongyi-MAI (Alibaba), a powerful 6 billion parameter text-to-image generation model. We've added a FastAPI + SvelteKit webapp to make the model easier to use with persistent model loading and a modern UI.

**Original Project**: [Tongyi-MAI/Z-Image](https://github.com/Tongyi-MAI/Z-Image)
**Credit**: Z-Image Team at Alibaba's Tongyi Lab
**License**: See original repository

## What's Different?

Instead of running command-line generation that reloads the model each time, this webapp:

- **Loads the model once** at startup and keeps it in memory
- **Provides a web UI** - no terminal commands needed
- **Shows real-time progress** via WebSocket updates
- **Optimized for M4 Pro** with 24GB unified memory
- **Includes quality presets** (Fast, Draft, Standard, High, Ultra)
- **Image history** - view and download past generations

## Screenshots

*Coming soon*

## Quick Start

### Prerequisites

- **macOS** with Apple Silicon (tested on M4 Pro)
- **Python 3.14** (or 3.11+)
- **Node.js 18+**
- **24GB RAM** recommended (16GB minimum)
- **~20GB disk space** for model weights

### Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/maylard/z-image.git
   cd z-image
   ```

2. **Create Python virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -e .[dev]
   pip install -r webapp/backend/requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd webapp/frontend
   npm install
   cd ../..
   ```

5. **Download model weights**

   The model will auto-download on first run, or manually download:
   ```bash
   # From Hugging Face (requires git-lfs)
   git lfs install
   git clone https://huggingface.co/Tongyi-MAI/Z-Image-Turbo ckpts/Z-Image-Turbo
   ```

### Running the Webapp

**Development Mode** (recommended for testing):
```bash
./webapp/start.sh --dev
```
- Frontend runs on port **5173** with hot reload
- Changes to code appear instantly
- Browser opens automatically

**Production Mode**:
```bash
./webapp/start-prod.sh
```
- Frontend builds and runs on port **4173**
- Optimized/minified code
- Better performance
- Browser opens automatically

**First startup** takes 3-5 minutes:
1. Server starts immediately
2. Model loads (~30-60 seconds)
3. Warmup pre-compiles GPU code (~2-3 minutes)
4. Status changes to "Ready"

**Subsequent startups** are faster if you don't restart your computer (model stays cached).

### Stopping the App

Press `Ctrl+C` in the terminal where you started the webapp.

## Usage

1. **Type a prompt** - Describe the image you want
2. **Choose settings**:
   - **Style**: Realistic or Anime
   - **Quality**: Fast (30s) to Ultra (3min)
   - **Aspect Ratio**: 16:9, 1:1, etc.
3. **Click Generate** - Watch progress in real-time
4. **Download** - Right-click image or use download button

### Quality Presets (M4 Pro Performance)

| Quality | Resolution (16:9) | Steps | Time | Use Case |
|---------|-------------------|-------|------|----------|
| Fast | 512×288 | 2 | ~30-35s | Quick previews |
| Draft | 640×368 | 4 | ~45-55s | Exploring ideas |
| Standard | 1024×576 | 6 | ~60-80s | Good balance |
| High | 1280×720 | 8 | ~90-120s | Final output |
| Ultra | 1536×864 | 8 | ~150-180s | Maximum detail |

**Note**: First generation at a new size takes ~30s longer for GPU compilation.

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Frontend   │  HTTP   │   Backend   │ PyTorch │   Z-Image   │
│ (SvelteKit) │────────▶│  (FastAPI)  │────────▶│  Model 6B   │
│  Port 5173  │◀────────│  Port 8000  │◀────────│     MPS     │
└─────────────┘   JSON  └─────────────┘  Images └─────────────┘
       │                       │
       │    WebSocket          │
       └───────────────────────┘
            Progress
```

**Tech Stack**:
- **Frontend**: SvelteKit, Vite, TypeScript
- **Backend**: FastAPI, PyTorch, uvicorn
- **Model**: Z-Image-Turbo (6B parameters)
- **Hardware**: Metal Performance Shaders (MPS)

## File Structure

```
.
├── webapp/
│   ├── backend/
│   │   ├── server.py          # FastAPI REST + WebSocket API
│   │   ├── model_manager.py   # Singleton model loader
│   │   └── image_store.py     # Image persistence
│   ├── frontend/
│   │   └── src/               # SvelteKit UI
│   ├── generated/             # Saved images (gitignored)
│   ├── start.sh               # Start both frontend + backend
│   ├── start-backend.sh       # Backend only
│   ├── CLAUDE.md              # Development guide
│   └── PRESENTATION.md        # Technical deep-dive
├── src/                       # Original Z-Image code
├── ckpts/                     # Model weights (gitignored)
└── pyproject.toml             # Python package config
```

## API Endpoints

The backend provides REST and WebSocket APIs:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/status` | GET | Check if model is ready |
| `/api/generate` | POST | Generate image (REST) |
| `/ws/generate` | WebSocket | Generate with progress updates |
| `/api/history` | GET | List past generations |
| `/api/images/{id}` | GET | Retrieve specific image |

Full API docs available at `http://localhost:8000/docs` when running.

## Performance Optimizations

This webapp includes several optimizations for Apple Silicon:

1. **VAE in bfloat16** - Faster image decoding
2. **Warmup at startup** - Pre-compiles common sizes
3. **Quality-based steps** - Fewer steps for lower quality
4. **Sequential multi-image** - Avoids MPS crashes
5. **Generation lock** - Thread-safe GPU operations
6. **Memory optimization** - `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0`

See `webapp/PRESENTATION.md` for detailed explanations.

## Troubleshooting

### Model won't load
- Check you have ~20GB free disk space
- Verify `ckpts/Z-Image-Turbo/` contains model files
- Check console for error messages

### Out of memory
- Close other apps to free RAM
- Use "Fast" or "Draft" quality presets
- Reduce number of images per generation

### Slow first generation
- This is normal - MPS compiles GPU code on first use
- Warmup pre-compiles Fast and Draft sizes
- Subsequent generations are faster

### Port already in use
```bash
# Kill existing processes
pkill -f "uvicorn webapp.backend.server"
pkill -f "vite.*5173"
```

## Development

See `webapp/CLAUDE.md` for development guidelines, architecture details, and contribution instructions.

## Original Z-Image Features

This webapp uses Z-Image-Turbo, which includes:

- ⚡️ 8-step generation (vs 50+ for standard diffusion)
- 🌍 Bilingual text rendering (English & Chinese)
- 🎨 Photorealistic quality
- 🏆 #1 ranked open-source model on Artificial Analysis

For the original CLI inference, LoRA training, and other features, see:
- [Original Repository](https://github.com/Tongyi-MAI/Z-Image)
- [Model on Hugging Face](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
- [Technical Report](https://arxiv.org/abs/2511.22699)

## Citation

If you use this project or the original Z-Image, please cite:

```bibtex
@article{team2025zimage,
  title={Z-Image: An Efficient Image Generation Foundation Model with Single-Stream Diffusion Transformer},
  author={Z-Image Team},
  journal={arXiv preprint arXiv:2511.22699},
  year={2025}
}
```

## License

This webapp code is provided as-is. The original Z-Image model and code are subject to their original license terms. See the [original repository](https://github.com/Tongyi-MAI/Z-Image) for details.

## Acknowledgments

- **Z-Image Team** at Alibaba's Tongyi Lab for the incredible model
- **Hugging Face** for model hosting and diffusers integration
- **Apple** for Metal Performance Shaders (MPS) support in PyTorch
