"""FastAPI server for Z-Image web application.

Provides REST and WebSocket endpoints for image generation.
"""

from __future__ import annotations

import asyncio
import os
import random
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import torch
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel, Field

from .model_manager import get_model_manager
from .image_store import ImageStore


# Configuration
STORAGE_DIR = Path(__file__).parent.parent / "generated"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Resolution presets (multiplier applied to base aspect ratio dimensions)
# Optimized for Apple Silicon M4 with 24GB RAM
# Higher resolutions increase generation time exponentially
QUALITY_MAPPING = {
    "Fast": 0.4,     # e.g. 512x288 for 16:9 (~30-35s on M4)
    "Draft": 0.5,    # e.g. 640x368 for 16:9 (~45-55s on M4)
    "Standard": 0.8, # e.g. 1024x576 for 16:9 (~60-80s on M4)
    "High": 1.0,     # e.g. 1280x720 for 16:9 (~90-120s on M4)
    "Ultra": 1.2,    # e.g. 1536x864 for 16:9 (~150-180s on M4)
}

# Optimal steps per quality level (fewer steps for lower quality = faster)
QUALITY_STEPS = {
    "Fast": 2,       # Fastest preview
    "Draft": 4,      # Quick preview
    "Standard": 6,   # Good balance
    "High": 8,       # Full quality
    "Ultra": 8,      # Full quality
}

ASPECT_RATIOS = {
    "16:9": {"width": 1280, "height": 720},
    "9:16": {"width": 720, "height": 1280},
    "1:1": {"width": 1024, "height": 1024},
    "4:3": {"width": 1024, "height": 768},
    "3:4": {"width": 768, "height": 1024},
}

# Style prefixes for prompt enhancement
STYLE_PREFIXES = {
    "realistic": "photorealistic, highly detailed, professional photography, ",
    "anime": "anime style, high quality anime art, vibrant colors, ",
}


# Pydantic models
class GenerateRequest(BaseModel):
    """Request body for image generation."""

    prompt: str = Field(..., min_length=1, max_length=2000)
    style: str = Field(default="realistic", pattern="^(realistic|anime)$")
    aspect_ratio: str = Field(default="16:9")
    quality: str = Field(default="Standard", pattern="^(Fast|Draft|Standard|High|Ultra)$")
    num_images: int = Field(default=1, ge=1, le=4)
    steps: int = Field(default=8, ge=2, le=16)
    seed: Optional[int] = Field(default=None)


class GenerateResponse(BaseModel):
    """Response from image generation."""

    images: list[GenerateResponseItem]
    total_time: float


class GenerateResponseItem(BaseModel):
    """Details for a single generated image."""

    id: str
    url: str
    prompt: str
    style: str
    width: int
    height: int
    steps: int
    seed: int
    generation_time: float


class HistoryItem(BaseModel):
    """Single image in history."""

    id: str
    url: str
    prompt: str
    style: str
    width: int
    height: int
    created_at: str
    generation_time: float


# Global image store
image_store: Optional[ImageStore] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown."""
    global image_store

    logger.info("Starting Z-Image server...")

    # Initialize image store
    image_store = ImageStore(STORAGE_DIR)

    # Load model in background (non-blocking startup)
    logger.info("Scheduling model load in background...")
    loop = asyncio.get_event_loop()
    # Fire and forget - don't await so the server starts serving /api/status immediately
    loop.run_in_executor(None, get_model_manager().load)

    yield

    logger.info("Shutting down Z-Image server...")


# Create FastAPI app
app = FastAPI(
    title="Z-Image Web API",
    description="Generate images using Z-Image-Turbo",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Dev server
        "http://127.0.0.1:5173",  # Dev server
        "http://localhost:4173",  # Preview/production
        "http://127.0.0.1:4173",  # Preview/production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _generate_image(
    prompt: str,
    width: int,
    height: int,
    steps: int,
    num_images: int,
    seed: int,
    callback: Optional[callable] = None,
) -> tuple[list[Path], list[int], float]:
    """Generate multiple images sequentially. Returns (list of image_paths, list of seeds, total_time).

    Images are generated one at a time with unique seeds to avoid MPS batch issues
    and ensure each image is different.
    """
    # Import here to avoid circular imports
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from zimage import generate

    manager = get_model_manager()
    device = manager.device

    start_time = time.time()
    image_paths = []
    seeds_used = []

    # Acquire lock to prevent concurrent MPS operations (e.g., during warmup)
    with manager.generation_lock:
        # Generate images one at a time with unique seeds
        for i in range(num_images):
            current_seed = seed + i
            seeds_used.append(current_seed)

            # Create progress callback that adjusts for multi-image progress
            def make_callback(image_index):
                def adjusted_callback(step, total_steps, latents):
                    if callback:
                        # Calculate overall progress percentage (0-100)
                        image_progress = (step + 1) / total_steps  # 0 to 1 for this image
                        overall_progress = (image_index + image_progress) / num_images  # 0 to 1 overall
                        progress_pct = min(int(overall_progress * 100), 99)  # Cap at 99, completion sets 100
                        # Pass values so downstream (step+1)/total*100 gives progress_pct
                        callback(progress_pct - 1, 100, latents)
                return adjusted_callback

            logger.info(f"Generating image {i+1}/{num_images} with seed {current_seed}")

            images = generate(
                prompt=prompt,
                **manager.components,
                height=height,
                width=width,
                num_inference_steps=steps,
                num_images_per_prompt=1,  # Always generate one at a time
                guidance_scale=0.0,
                max_sequence_length=256,  # Faster text encoding (most prompts < 256 tokens)
                generator=torch.Generator(device).manual_seed(current_seed),
                callback=make_callback(i) if callback else None,
            )

            # Save the single image
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                output_path = Path(f.name)
                images[0].save(output_path)
                image_paths.append(output_path)

    total_time = time.time() - start_time
    logger.info(f"Generated {num_images} image(s) in {total_time:.2f}s")
    return image_paths, seeds_used, total_time


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_image(request: GenerateRequest):
    """Generate a new image from a prompt."""
    global image_store

    if image_store is None:
        raise HTTPException(status_code=503, detail="Server not ready")

    # Get dimensions from aspect ratio
    if request.aspect_ratio not in ASPECT_RATIOS:
        raise HTTPException(status_code=400, detail=f"Invalid aspect ratio: {request.aspect_ratio}")

    dimensions = ASPECT_RATIOS[request.aspect_ratio]
    multiplier = QUALITY_MAPPING.get(request.quality, 1.0)
    width = int(dimensions["width"] * multiplier) // 16 * 16
    height = int(dimensions["height"] * multiplier) // 16 * 16

    # Use quality-optimized steps (user can still override)
    optimal_steps = QUALITY_STEPS.get(request.quality, 8)
    steps = min(request.steps, optimal_steps) if request.steps == 8 else request.steps

    # Apply style prefix
    style_prefix = STYLE_PREFIXES.get(request.style, "")
    full_prompt = style_prefix + request.prompt

    # Generate seed if not provided
    seed = request.seed if request.seed is not None else random.randint(0, 2**32 - 1)

    # Generate images in thread pool
    loop = asyncio.get_event_loop()
    image_paths, seeds_used, total_time = await loop.run_in_executor(
        None,
        _generate_image,
        full_prompt,
        width,
        height,
        steps,
        request.num_images,
        seed,
    )

    # Store in history
    response_items = []
    for idx, path in enumerate(image_paths):
        record = image_store.add_image(
            image_path=path,
            prompt=request.prompt,
            style=request.style,
            width=width,
            height=height,
            steps=steps,
            seed=seeds_used[idx],
            generation_time=total_time / len(image_paths),
        )
        response_items.append(
            GenerateResponseItem(
                id=record.id,
                url=f"/api/images/{record.id}",
                prompt=record.prompt,
                style=record.style,
                width=record.width,
                height=record.height,
                steps=record.steps,
                seed=record.seed,
                generation_time=record.generation_time,
            )
        )
        if path.exists():
            path.unlink()

    return GenerateResponse(images=response_items, total_time=total_time)


@app.get("/api/history")
async def get_history() -> list[HistoryItem]:
    """Get recent image history."""
    global image_store

    if image_store is None:
        return []

    return [
        HistoryItem(
            id=record.id,
            url=f"/api/images/{record.id}",
            prompt=record.prompt,
            style=record.style,
            width=record.width,
            height=record.height,
            created_at=record.created_at,
            generation_time=record.generation_time,
        )
        for record in image_store.get_history()
    ]


@app.get("/api/images/{image_id}")
async def get_image(image_id: str):
    """Get a specific image by ID."""
    global image_store

    if image_store is None:
        raise HTTPException(status_code=503, detail="Server not ready")

    path = image_store.get_image_path(image_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(path, media_type="image/png")


@app.get("/api/images/{image_id}/download")
async def download_image(image_id: str):
    """Download an image with proper filename."""
    global image_store

    if image_store is None:
        raise HTTPException(status_code=503, detail="Server not ready")

    record = image_store.get_image(image_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Image not found")

    path = image_store.get_image_path(image_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    # Create a clean filename from the prompt
    clean_prompt = "".join(c if c.isalnum() or c in " -_" else "" for c in record.prompt[:50])
    filename = f"zimage_{clean_prompt}_{record.id}.png"

    return FileResponse(
        path,
        media_type="image/png",
        filename=filename,
    )


@app.delete("/api/images/{image_id}")
async def delete_image(image_id: str):
    """Delete an image from history."""
    global image_store

    if image_store is None:
        raise HTTPException(status_code=503, detail="Server not ready")

    success = image_store.delete_image(image_id)
    if not success:
        raise HTTPException(status_code=404, detail="Image not found")

    return {"status": "success", "message": "Image deleted"}


@app.get("/api/status")
async def get_status():
    """Get server status."""
    manager = get_model_manager()
    return {
        "ready": manager.is_ready(),  # Only true after warmup completes
        "status": manager.status_message,
        "device": manager.device if manager.is_loaded() else None,
        "aspect_ratios": list(ASPECT_RATIOS.keys()),
        "styles": list(STYLE_PREFIXES.keys()),
        "qualities": list(QUALITY_MAPPING.keys()),
    }


@app.get("/api/settings")
async def get_settings():
    """Get available settings and defaults."""
    return {
        "aspect_ratios": {
            name: {"width": dims["width"], "height": dims["height"]}
            for name, dims in ASPECT_RATIOS.items()
        },
        "styles": list(STYLE_PREFIXES.keys()),
        "qualities": list(QUALITY_MAPPING.keys()),
        "defaults": {
            "aspect_ratio": "16:9",
            "style": "realistic",
            "quality": "Standard",
            "num_images": 1,
            "steps": 8,
        },
        "limits": {
            "steps_min": 4,
            "steps_max": 16,
            "num_images_max": 4,
            "prompt_max_length": 2000,
        },
    }


# WebSocket for real-time progress (future enhancement)
@app.websocket("/ws/generate")
async def websocket_generate(websocket: WebSocket):
    """WebSocket endpoint for generation with progress updates."""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            # Parse request
            request = GenerateRequest(**data)

            # Send "started" status
            await websocket.send_json({"status": "started", "message": "Generation started"})

            # Get dimensions
            if request.aspect_ratio not in ASPECT_RATIOS:
                await websocket.send_json({"status": "error", "message": "Invalid aspect ratio"})
                continue

            dimensions = ASPECT_RATIOS[request.aspect_ratio]
            multiplier = QUALITY_MAPPING.get(request.quality, 1.0)
            width = int(dimensions["width"] * multiplier) // 16 * 16
            height = int(dimensions["height"] * multiplier) // 16 * 16

            # Use quality-optimized steps
            optimal_steps = QUALITY_STEPS.get(request.quality, 8)
            steps = min(request.steps, optimal_steps) if request.steps == 8 else request.steps

            style_prefix = STYLE_PREFIXES.get(request.style, "")
            full_prompt = style_prefix + request.prompt
            seed = request.seed if request.seed is not None else random.randint(0, 2**32 - 1)

            loop = asyncio.get_event_loop()

            # WebSocket Progress Callback
            def on_progress(step, total_steps, latents):
                progress = int((step + 1) / total_steps * 100)
                # We can't use await here because this is called from a thread
                # but FastAPI provides a way to run coro in loop
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json({
                        "status": "generating",
                        "progress": progress,
                        "message": f"Denoising: {progress}%"
                    }),
                    loop
                )

            # Generate in thread pool
            try:
                image_paths, seeds_used, total_time = await loop.run_in_executor(
                    None,
                    _generate_image,
                    full_prompt,
                    width,
                    height,
                    steps,
                    request.num_images,
                    seed,
                    on_progress,
                )

                # Store in history
                results = []
                for idx, path in enumerate(image_paths):
                    record = image_store.add_image(
                        image_path=path,
                        prompt=request.prompt,
                        style=request.style,
                        width=width,
                        height=height,
                        steps=steps,
                        seed=seeds_used[idx],
                        generation_time=total_time / len(image_paths),
                    )
                    results.append({
                        "id": record.id,
                        "url": f"/api/images/{record.id}",
                        "prompt": record.prompt,
                        "style": record.style,
                        "width": record.width,
                        "height": record.height,
                        "generation_time": record.generation_time,
                    })
                    if path.exists():
                        path.unlink()

                # Send success
                await websocket.send_json({
                    "status": "complete",
                    "images": results,
                    "total_time": total_time,
                })

            except Exception as e:
                logger.error(f"Generation failed: {e}")
                await websocket.send_json({"status": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
