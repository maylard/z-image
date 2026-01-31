"""Persistent Model Manager for Z-Image.

Loads the model once at startup and keeps it in memory for fast inference.
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Optional

import torch
from loguru import logger

# Add src to path for Z-Image imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from utils import (
    AttentionBackend,
    ensure_model_weights,
    load_from_local_dir,
    set_attention_backend,
)


class ModelManager:
    """Singleton manager for Z-Image model components."""

    _instance: Optional["ModelManager"] = None
    _components: Optional[dict] = None
    _device: str = ""
    _dtype = torch.bfloat16
    _status_message: str = "Initializing..."
    _generation_lock: threading.Lock = threading.Lock()  # Prevent concurrent MPS ops

    def __new__(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ModelManager":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _select_device(self) -> str:
        """Select optimal device: cuda -> mps -> cpu."""
        if torch.cuda.is_available():
            logger.info("Selected device: cuda")
            return "cuda"
        if torch.backends.mps.is_available():
            logger.info("Selected device: mps")
            # MPS optimizations
            torch.mps.set_per_process_memory_fraction(0.0)  # No limit
            return "mps"
        logger.warning("No GPU available, falling back to CPU")
        return "cpu"

    def load(self) -> None:
        """Load the model into memory. Safe to call multiple times."""
        if self._components is not None:
            self._status_message = "Ready"
            logger.info("Model already loaded, skipping")
            return

        try:
            self._status_message = "Verifying model weights..."
            logger.info("Loading Z-Image-Turbo model...")
            model_path = ensure_model_weights(
                str(PROJECT_ROOT / "ckpts" / "Z-Image-Turbo"), verify=False
            )

            self._status_message = "Loading components into memory..."
            self._device = self._select_device()
            attn_backend = os.environ.get("ZIMAGE_ATTENTION", "_native_flash")

            # Set matmul precision for better performance
            torch.set_float32_matmul_precision("medium")

            self._components = load_from_local_dir(
                model_path,
                device=self._device,
                dtype=self._dtype,
                compile=False,  # Not optimal on MPS
            )

            # Convert VAE to bfloat16 for faster decoding (24GB RAM is plenty)
            if "vae" in self._components:
                self._components["vae"] = self._components["vae"].to(self._dtype)
                logger.info("VAE converted to bfloat16 for faster decoding")

            AttentionBackend.print_available_backends()
            set_attention_backend(attn_backend)

            # Warmup: run a tiny forward pass to trigger MPS compilation
            self._status_message = "Warming up model..."
            self._warmup()

            self._status_message = "Ready"
            logger.info(f"Model loaded successfully on {self._device}")
        except Exception as e:
            self._status_message = f"Error: {str(e)}"
            logger.error(f"Failed to load model: {e}")

    def _warmup(self) -> None:
        """Run warmup passes to trigger PyTorch/MPS compilation for common sizes."""
        try:
            from zimage import generate

            # Warmup sizes matching quality presets (Fast, Draft)
            warmup_sizes = [
                (288, 512, "Fast 16:9"),     # Fast - prioritize this
                (368, 640, "Draft 16:9"),    # Draft
            ]

            for height, width, name in warmup_sizes:
                logger.info(f"Warming up {name} ({width}x{height})...")
                # Acquire lock to prevent concurrent generation during warmup
                with self._generation_lock:
                    with torch.inference_mode():
                        _ = generate(
                            prompt="test",
                            **self._components,
                            height=height,
                            width=width,
                            num_inference_steps=1,
                            max_sequence_length=256,  # Must match server.py
                            guidance_scale=0.0,
                            generator=torch.Generator(self._device).manual_seed(0),
                        )

            # Clear cached tensors
            if self._device == "mps":
                torch.mps.empty_cache()
            elif self._device == "cuda":
                torch.cuda.empty_cache()
            logger.info("Warmup complete - common sizes pre-compiled")
        except Exception as e:
            logger.warning(f"Warmup failed (non-critical): {e}")

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._components is not None

    def is_ready(self) -> bool:
        """Check if model is fully loaded and warmed up."""
        return self._components is not None and self._status_message == "Ready"

    @property
    def status_message(self) -> str:
        """Get current status message."""
        return self._status_message

    @property
    def components(self) -> dict:
        """Get model components. Raises if not loaded."""
        if self._components is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        return self._components

    @property
    def device(self) -> str:
        """Get current device."""
        return self._device

    @property
    def dtype(self):
        """Get current dtype."""
        return self._dtype

    @property
    def generation_lock(self) -> threading.Lock:
        """Get generation lock to prevent concurrent MPS operations."""
        return self._generation_lock


def get_model_manager() -> ModelManager:
    """Get the global ModelManager instance."""
    return ModelManager.get_instance()
