# Z-Image Webapp Presentation

A modern web interface for the Z-Image 6B text-to-image model, optimized for Apple Silicon.

---

## What is Z-Image?

Z-Image is a **6 billion parameter** text-to-image generation model. Given a text prompt like *"a golden retriever playing in autumn leaves"*, it creates a matching image from scratch.

### Why a Webapp?

Traditional image generation requires:
1. Opening a terminal
2. Typing a command
3. Waiting for the model to load (~30 seconds)
4. Running generation
5. Repeating steps 3-4 for each image

**The webapp solves this** by keeping the model loaded in memory. After the initial startup, generating new images is much faster since the model is already "warmed up" and ready to go.

### Hardware Context

This webapp is optimized for:
- **Apple M4 Pro** with 24GB unified memory
- Uses Metal Performance Shaders (MPS) for GPU acceleration
- The 6B model fits comfortably in 24GB RAM

---

## Architecture Overview

```
                    Z-Image Webapp Architecture

  +------------------+         +------------------+         +------------------+
  |                  |  HTTP   |                  |  PyTorch |                  |
  |    Frontend      | ------> |    Backend       | -------> |    Z-Image       |
  |    (Browser)     | <------ |    (FastAPI)     | <------- |    Model         |
  |                  |   JSON  |                  |  Images  |                  |
  +------------------+         +------------------+         +------------------+
         |                            |
         |                            v
         |                     +------------------+
         |   WebSocket         |   Image Store    |
         +-------------------> |   (generated/)   |
              Progress         +------------------+
              Updates
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | **SvelteKit** | Modern reactive UI framework |
| Backend | **FastAPI** | High-performance Python API server |
| Model | **PyTorch** | Deep learning framework |
| Hardware | **MPS** | Apple's Metal GPU acceleration |

---

## Key Components

### 1. Model Manager - The "Kitchen Chef"

Think of the Model Manager like a chef in a restaurant kitchen. Instead of hiring a new chef for every order (loading the model each time), we keep one chef on staff who stays in the kitchen all day.

**What it does:**
- Loads the 6B parameter model into memory once at startup
- Keeps all model components (transformer, VAE, text encoder) ready
- Handles "warmup" - pre-cooking common dish sizes so orders come out faster

```
webapp/backend/model_manager.py

Key features:
- Singleton pattern (only one instance)
- Automatic device selection (CUDA > MPS > CPU)
- Warmup for Fast and Draft quality presets
- Thread-safe generation lock
```

### 2. Backend API - The "Waiter"

The backend acts as a waiter between you (the browser) and the chef (the model). It:
- Takes your order (prompt, style, quality)
- Communicates with the kitchen
- Brings back the finished dish (generated image)

**Endpoints:**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/generate` | POST | Generate new image(s) |
| `/api/status` | GET | Check if model is ready |
| `/api/images/{id}` | GET | Retrieve generated image |
| `/api/history` | GET | List past generations |
| `/ws/generate` | WebSocket | Real-time progress updates |

### 3. Frontend - The "Dining Room"

The user interface where you:
- Type your prompt
- Choose style (realistic or anime)
- Select quality (Fast to Ultra)
- Watch generation progress
- View and download results

**Features:**
- Three color themes (Studio, Midnight, Nordic)
- Sound notification when generation completes
- Live progress bar with timer
- Image history gallery

---

## How It Works: End-to-End Flow

### Step-by-Step Process

```
   User                Frontend              Backend               Model
    |                    |                     |                     |
    | 1. Type prompt     |                     |                     |
    |------------------->|                     |                     |
    |                    | 2. WebSocket        |                     |
    |                    |    connect          |                     |
    |                    |------------------->|                     |
    |                    |                     | 3. Generate         |
    |                    |                     |    request          |
    |                    |                     |------------------->|
    |                    |                     |                     |
    |                    | 4. Progress: 10%    |                     |
    |                    |<--------------------|                     |
    |  "Generating..."   |                     |                     |
    |<-------------------|                     |                     |
    |                    | 5. Progress: 50%    |                     |
    |                    |<--------------------|                     |
    |                    |                     |                     |
    |                    | 6. Progress: 100%   |                     |
    |                    |<--------------------|                     |
    |                    |                     |                     |
    |                    | 7. Image URL        |<--------------------|
    |                    |<--------------------|                     |
    |  Display image     |                     |                     |
    |<-------------------|                     |                     |
```

### What Happens Inside the Model

1. **Text Encoding** (~4 seconds)
   - Your prompt is converted to numbers the model understands
   - Uses an 8GB Qwen3 language model as the text encoder

2. **Diffusion Process** (varies by quality)
   - Starts with random noise
   - Gradually "denoises" into a coherent image
   - More steps = higher quality but slower

3. **VAE Decoding** (~2 seconds)
   - Converts the model's internal representation to actual pixels
   - Uses bfloat16 for faster processing

---

## Performance Optimizations

### Why First Generation is Slow

Apple's MPS (Metal Performance Shaders) compiles GPU code on first use. Think of it like a chef learning a new recipe - the first time takes longer, but subsequent attempts are faster.

**Solution: Warmup**

At startup, the backend runs "dummy" generations for common sizes:
- Fast (512x288)
- Draft (640x368)

This pre-compiles the GPU code so your first real generation is fast.

### Quality Presets

| Quality | Resolution | Steps | Typical Time | Use Case |
|---------|------------|-------|--------------|----------|
| **Fast** | 512x288 | 2 | 30-35s | Quick previews |
| **Draft** | 640x368 | 4 | 45-55s | Exploring ideas |
| **Standard** | 1024x576 | 6 | 60-80s | Good balance |
| **High** | 1280x720 | 8 | 90-120s | Final output |
| **Ultra** | 1536x864 | 8 | 150-180s | Maximum detail |

### Other Optimizations

1. **VAE in bfloat16** - Faster image decoding
2. **max_sequence_length=256** - Faster text encoding (most prompts are short)
3. **Generation lock** - Prevents crashes from concurrent GPU operations
4. **Sequential multi-image** - Generates images one at a time with unique seeds

---

## Running the App

### Prerequisites

1. **Python 3.14** with virtual environment
2. **Node.js** for frontend
3. **Model weights** in `ckpts/Z-Image-Turbo/`

### Quick Start

```bash
# From the project root
./webapp/start.sh --dev
```

This single command:
1. Activates the Python virtual environment
2. Sets memory optimization flags
3. Starts the backend on port 8000
4. Starts the frontend on port 5173
5. Opens the browser automatically

### URLs

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

### Startup Sequence

1. **Server starts** (immediate) - API begins responding
2. **Model loading** (~30-60s) - Components load into RAM
3. **Warmup** (~2-3 min) - GPU code pre-compiles
4. **Ready** - Status changes to "Ready", generation available

You can watch the status at `/api/status`:
```json
{"ready": false, "status": "Loading components into memory..."}
{"ready": false, "status": "Warming up model..."}
{"ready": true, "status": "Ready"}
```

---

## Demo Screenshots

*[Add screenshots here showing:]*
1. Main generation interface
2. Quality preset selection
3. Generation in progress with timer
4. Completed image with download option
5. Theme switching (Studio/Midnight/Nordic)
6. Image history gallery

---

## Summary

The Z-Image webapp transforms a command-line tool into a user-friendly web application by:

- **Keeping the model loaded** - No repeated startup costs
- **Providing real-time feedback** - Progress updates via WebSocket
- **Optimizing for hardware** - Tuned for M4 Pro's 24GB RAM
- **Offering quality presets** - Trade speed for resolution as needed
- **Warmup at startup** - First generation is fast, not slow

It's designed to make AI image generation as simple as typing a prompt and clicking "Generate."
