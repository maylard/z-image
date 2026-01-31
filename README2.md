# Z-Image Quick Start Guide

This guide explains how to use the simplified `createImage.sh` script for generating images with custom prompts.

## ⚡ TL;DR - Instant Examples

```bash
# Basic usage (1024x1024, default)
echo "A mountain landscape at sunset" > prompt.md
./createImage.sh

# High resolution (1536x1536)
ZIMAGE_HEIGHT=1536 ZIMAGE_WIDTH=1536 ./createImage.sh

# Portrait mode (768x1024)
ZIMAGE_HEIGHT=1024 ZIMAGE_WIDTH=768 ./createImage.sh

# Custom filename
ZIMAGE_OUTPUT=my_epic_art.png ./createImage.sh

# Everything combined
ZIMAGE_OUTPUT=sunset.png ZIMAGE_HEIGHT=1536 ZIMAGE_WIDTH=1536 ZIMAGE_STEPS=12 ./createImage.sh
```

## Quick Start

### 1. Setup (One-time)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install torch>=2.5.0 transformers>=4.51.0 safetensors loguru pillow accelerate huggingface_hub>=0.25.0
```

### 2. Create Your Prompt

Edit `prompt.md` with your desired image description:

```bash
# Example prompt.md content:
A serene mountain landscape at sunset, snow-capped peaks, 
golden hour lighting, photorealistic, 8k quality
```

### 3. Generate Image

```bash
./createImage.sh
```

Output will be saved to `prompt.png` by default.

## Changing Image Size

**Quick Answer:**
```bash
# Generate 1536x1536 image
ZIMAGE_HEIGHT=1536 ZIMAGE_WIDTH=1536 ./createImage.sh

# Generate portrait (768x1024)
ZIMAGE_HEIGHT=1024 ZIMAGE_WIDTH=768 ./createImage.sh

# Generate landscape (1024x768)  
ZIMAGE_HEIGHT=768 ZIMAGE_WIDTH=1024 ./createImage.sh

# Ultra-wide (2048x1024)
ZIMAGE_HEIGHT=1024 ZIMAGE_WIDTH=2048 ./createImage.sh
```

**Default:** 1024x1024 pixels

**Recommended sizes:**
- 512x512 (fast, lower quality)
- 768x768 (good balance)
- 1024x1024 (default, best quality)
- 1536x1536 (high quality, slower)
- 2048x2048 (very high quality, much slower, needs more VRAM)

**Note:** Larger images require more GPU memory. If you get out-of-memory errors, reduce the size.

## Customization with Environment Variables

You can customize generation parameters using environment variables:

```bash
# Custom output filename
ZIMAGE_OUTPUT=my_artwork.png ./createImage.sh

# Custom dimensions (default: 1024x1024)
ZIMAGE_HEIGHT=1536 ZIMAGE_WIDTH=1536 ./createImage.sh

# Adjust inference steps (default: 8)
ZIMAGE_STEPS=12 ./createImage.sh

# Change guidance scale (default: 0.0 for Turbo model)
ZIMAGE_GUIDANCE=3.5 ./createImage.sh

# Set random seed for reproducibility (default: 42)
ZIMAGE_SEED=12345 ./createImage.sh

# Choose attention backend (default: _native_flash)
# Options: _flash_3, _native_flash, flash
ZIMAGE_ATTENTION=_flash_3 ./createImage.sh
```

### Combine Multiple Parameters

```bash
ZIMAGE_OUTPUT=epic_sunset.png \
ZIMAGE_HEIGHT=1536 \
ZIMAGE_WIDTH=1536 \
ZIMAGE_STEPS=12 \
ZIMAGE_SEED=999 \
./createImage.sh
```

## Model Weights Management

### Default Model Location

The script uses `ckpts/Z-Image-Turbo` by default.

### Downloading Different Models

Models are automatically downloaded from Hugging Face Hub. To use a different model:

1. **Edit `createImage.py`** (line 44):
   ```python
   model_path = ensure_model_weights("ckpts/YOUR-MODEL-NAME", verify=False)
   ```

2. The model will be automatically downloaded to `ckpts/YOUR-MODEL-NAME/` on first run.

### Available Models

- `Z-Image-Turbo` - Fast generation (8 steps, guidance=0.0)
- `Z-Image` - Standard model (may require more steps and guidance)

Check the main README.md for the latest model zoo.

### Verifying Model Integrity

To verify downloaded model files against checksums:

```python
# In createImage.py, change line 44:
model_path = ensure_model_weights("ckpts/Z-Image-Turbo", verify=True)
```

This will check MD5 hashes against manifests in `src/config/manifests/`.

### Manual Model Download

If you prefer to download models manually:

```bash
# Using huggingface-cli (install: pip install huggingface_hub)
huggingface-cli download MODEL_NAME --local-dir ckpts/MODEL_NAME
```

### Clearing Model Cache

```bash
# Remove specific model
rm -rf ckpts/Z-Image-Turbo

# Model will be re-downloaded on next run
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'utils'`:

- The script sets `PYTHONPATH` automatically
- Ensure you're running `./createImage.sh`, not `python createImage.py` directly
- If running Python directly, use: `PYTHONPATH=src python createImage.py`

### Virtual Environment Not Found

The script will use system Python if no `.venv` exists. To create one:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch>=2.5.0 transformers>=4.51.0 safetensors loguru pillow accelerate huggingface_hub>=0.25.0
```

### Out of Memory

If generation fails with OOM:

1. **Reduce dimensions:**
   ```bash
   ZIMAGE_HEIGHT=768 ZIMAGE_WIDTH=768 ./createImage.sh
   ```

2. **Use CPU (slower but more memory):**
   ```bash
   # Edit createImage.py to force CPU
   # Or ensure CUDA is not available
   ```

### Prompt File Not Found

```bash
# Create prompt.md if missing
echo "A beautiful landscape" > prompt.md
./createImage.sh
```

## Advanced Usage

### Using Original `inference.py`

For hardcoded prompts and full control:

```bash
# Edit inference.py to customize prompt and parameters
python inference.py
```

Output: `example.png`

### Batch Generation

For processing multiple prompts:

```bash
# Create prompt files in prompts/ directory
python batch_inference.py
```

### Performance Optimization

For fastest generation (requires Hopper GPU: H100/H200/H800):

1. **Edit `createImage.py` line 46:**
   ```python
   compile = True  # Enable torch.compile
   ```

2. **Use Flash Attention 3:**
   ```bash
   ZIMAGE_ATTENTION=_flash_3 ./createImage.sh
   ```

This achieves sub-second generation after warm-up.

## File Structure Reference

```
Z-Image/
├── createImage.sh          # Main script (use this)
├── createImage.py          # Python logic for script
├── prompt.md              # Your prompt file
├── prompt.png             # Generated output (default)
├── inference.py           # Original example script
├── batch_inference.py     # Batch processing script
├── ckpts/                 # Model weights directory
│   └── Z-Image-Turbo/     # Default model
├── src/                   # Source code (don't modify unless contributing)
│   ├── utils/             # Helper utilities
│   ├── zimage/            # Model implementations
│   └── config/            # Configuration and manifests
└── .venv/                 # Virtual environment (create manually)
```

## Important Notes

### Import Pattern
This codebase uses **absolute imports without `src.` prefix**. The modules are:
- `from utils import ...`
- `from zimage import ...`
- `from config import ...`

These work because `src/` is added to `PYTHONPATH` automatically by the script.

### Do NOT Use Relative Imports
When editing source files in `src/`, use absolute imports:
```python
# ✅ Correct
from config import BYTES_PER_GB
from zimage.autoencoder import AutoencoderKL

# ❌ Wrong (will break)
from ..config import BYTES_PER_GB
from ..zimage.autoencoder import AutoencoderKL
```

### Model Weights Are Gitignored
The `ckpts/` directory is in `.gitignore`. Models are downloaded automatically on first run.

## Mac-Specific Optimization

**Running on Apple Silicon?** See **`MAC_SETUP.md`** for:
- Optimal settings for M1/M2/M3/M4 chips
- Memory usage guidelines
- Performance benchmarks
- Mac-specific troubleshooting

## Questions?

- **Main README:** See `README.md` for comprehensive documentation
- **Mac Setup:** See `MAC_SETUP.md` for Apple Silicon optimization
- **Issues:** Report at https://github.com/Tongyi-MAI/Z-Image
- **Model Zoo:** Check main README for available models
- **Community:** See main README for community works and examples

---

**Last Updated:** January 2026
**Compatible With:** Z-Image v0.1.0+
