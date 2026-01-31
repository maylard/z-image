"""Generate a Z-Image using the prompt inside prompt.md."""

from __future__ import annotations

import os
from pathlib import Path
import time

import torch

from utils import (
    AttentionBackend,
    ensure_model_weights,
    load_from_local_dir,
    set_attention_backend,
)
from zimage import generate

PROMPT_PATH = Path("prompt.md")
DEFAULT_OUTPUT = "prompt.png"


def read_prompt(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Prompt file {path} is empty")
    return text


def select_device() -> str:
    if torch.cuda.is_available():
        print("Chosen device: cuda")
        return "cuda"
    try:
        import torch_xla.core.xla_model as xm

        device = xm.xla_device()
        print("Chosen device: tpu")
        return device
    except (ImportError, RuntimeError):
        if torch.backends.mps.is_available():
            print("Chosen device: mps")
            return "mps"
        print("Chosen device: cpu")
        return "cpu"


def main() -> None:
    prompt = read_prompt(PROMPT_PATH)
    model_path = ensure_model_weights("ckpts/Z-Image-Turbo", verify=False)
    dtype = torch.bfloat16
    compile = False
    output_path = os.environ.get("ZIMAGE_OUTPUT", DEFAULT_OUTPUT)
    height = int(os.environ.get("ZIMAGE_HEIGHT", 1024))
    width = int(os.environ.get("ZIMAGE_WIDTH", 1024))
    num_inference_steps = int(os.environ.get("ZIMAGE_STEPS", 8))
    guidance_scale = float(os.environ.get("ZIMAGE_GUIDANCE", 0.0))
    seed = int(os.environ.get("ZIMAGE_SEED", 42))
    attn_backend = os.environ.get("ZIMAGE_ATTENTION", "_native_flash")

    device = select_device()
    components = load_from_local_dir(
        model_path, device=device, dtype=dtype, compile=compile
    )
    AttentionBackend.print_available_backends()
    set_attention_backend(attn_backend)
    print(f"Chosen attention backend: {attn_backend}")

    start_time = time.time()
    images = generate(
        prompt=prompt,
        **components,
        height=height,
        width=width,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale,
        generator=torch.Generator(device).manual_seed(seed),
    )
    elapsed = time.time() - start_time
    images[0].save(output_path)
    print(f"Saved image to {output_path} in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
