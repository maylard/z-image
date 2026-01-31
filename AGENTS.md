# AGENTS GUIDE FOR Z-IMAGE

This document is the canonical instruction set for any agentic assistant (Cursor, Copilot, Claude, etc.) operating in this repository. Place it in the repo root and keep it synchronized with any future `.cursor/rules/` or `.github/copilot-instructions.md` files—if those appear, excerpt their guidance here verbatim and call out where they live.

## 1. Repository Scope & Expectations
- Applies to every file under the repo root because no other scoped `AGENTS.md` exists.
- Assume cooperative development with humans; do not override user changes or force-push.
- Prefer minimal, well-explained diffs. Touch only the files required for the task.
- Never commit checkpoints, large assets, or secrets. Respect `.gitignore` (notably `ckpts/`, generated PNGs, `.env`, `.pdm-python`).
- If you discover additional process docs (README updates, issue templates, Cursor/Copilot rules), cross-link them here.

## 2. Environment & Tooling Quickstart
1. Python ≥ 3.10 is required (repo tested on 3.14.2 locally).
2. Install editable dependencies:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate  # optional but recommended
   pip install -e .[dev]
   ```
3. Core runtime deps: `torch>=2.5`, `transformers>=4.51`, `safetensors`, `loguru`, `accelerate`, `huggingface_hub`, `pillow`.
4. Dev tooling (`pip install -e .[dev]`) adds `black`, `isort`, and `ruff`.
5. CUDA optional but encouraged; the code automatically falls back to TPU/MPS/CPU.
6. Large checkpoints live under `ckpts/`; use `utils.ensure_model_weights` to fetch/verify.

## 3. Build, Run & Operational Commands
- **Installation (development):** `pip install -e .[dev]` for linting/dev tools.
- **Installation (basic):** `pip install torch>=2.5.0 transformers>=4.51.0 safetensors loguru pillow accelerate huggingface_hub>=0.25.0` for runtime only.
- **Custom prompt generation (recommended):** `./createImage.sh` (reads from `prompt.md`, outputs to `prompt.png`).
- **Single-image inference (default prompt):** `python inference.py`.
- **Batch prompts:** `python batch_inference.py` (expects prompt files under `prompts/`).
- **Manifest generation / refresh:** `python -m src.tools.generate_manifest ckpts/Z-Image-Turbo --verbose`.
- **Model file verification:** Use `ensure_model_weights("ckpts/Z-Image-Turbo", verify=True)` inside scripts instead of ad-hoc logic.
- **Attention backend control:** set `ZIMAGE_ATTENTION` env var (`_flash_3`, `_native_flash`, `flash`) before running inference.
- **Device selection:** scripts auto-select CUDA→TPU→MPS→CPU; avoid duplicating this logic elsewhere.

## 4. Linting, Formatting & Static Analysis
- **Ruff (fast lint):** `ruff check src tests`.
- **Ruff autofix (when safe):** `ruff check --fix src tests` (validate manually afterward).
- **Black formatting:** `black .` (120-column default; keep trailing commas where black inserts them).
- **Isort imports:** `isort .` (black-compatible profile).
- Run linters before submitting diffs; prefer targeted paths when possible for speed.

## 5. Testing Strategy (Current + Future)
- No automated tests ship today (no `tests/` folder). When adding tests, follow these conventions:
  - Place unit tests under `tests/` mirroring `src/` structure.
  - Use `pytest` as the default test runner. Examples:
    - Entire suite: `pytest`.
    - Module: `pytest tests/utils/test_loader.py`.
    - Single test: `pytest tests/utils/test_loader.py::TestLoader::test_load_from_local_dir`.
  - Keep GPU-heavy tests opt-in via markers (e.g., `@pytest.mark.gpu`).
  - Prefer deterministic seeds with `torch.Generator(device).manual_seed(seed)` in tests.
- Until tests exist, validate core flows manually (quick `python inference.py`).

## 6. Repository Map & Key Modules
- `src/zimage/transformer.py`, `scheduler.py`, `autoencoder.py`, `pipeline.py`: model core.
- `src/utils/`:
  - `loader.py`, `import_utils.py`: component loading, optional imports.
  - `helpers.py`: manifest utilities, memory stats, hashing.
  - `attention.py`: backend enumerations, registration helpers.
- `src/config/`:
  - `model.py`, `inference.py`: runtime defaults and hyperparameters.
  - `manifests/`: manifest README plus `{model}.txt` lists.
- `inference.py`: Original CLI entrypoint with hardcoded prompt.
- `batch_inference.py`: Batch processing from `prompts/` directory.
- `createImage.sh` + `createImage.py`: User-friendly wrapper that reads `prompt.md` and outputs `prompt.png`.
- `prompt.md`: User's prompt file for `createImage.sh` (create this with your desired prompt).
- `README2.md`: Quick start guide for `createImage.sh` usage, customization, and troubleshooting.
- `MAC_SETUP.md`: Apple Silicon (M1/M2/M3/M4) optimization guide with performance tuning.
- `assets/`: documentation imagery; do not modify unless updating docs.

## 7. Coding Style & Structure
### Imports (CRITICAL: Special Pattern)
- **This repo uses absolute imports WITHOUT the `src.` prefix**: `from utils import`, `from zimage import`, `from config import`.
- These work because scripts set `PYTHONPATH=src:$PYTHONPATH` at runtime (see `createImage.sh`).
- **NEVER use relative imports** (`from ..config import`) in `src/` modules—they break when imported as top-level.
- **NEVER change existing absolute imports to relative imports**—this breaks the module loading pattern.
- Order: standard library → third-party → local (`from config import ...`).
- Group related names; avoid wildcard imports entirely.

### Formatting & Layout
- Enforce `black` defaults (double quotes, trailing commas, blank lines between defs).
- Keep functions under ~80 lines when practical; factor helpers if logic grows.
- Use f-strings for string interpolation; avoid `%` formatting except in logging when beneficial.

### Typing & Interfaces
- Add type hints to all public functions, including return types.
- For forward declarations, use `from __future__ import annotations` if circular typing arises.
- Prefer `typing.Protocol` or `TypedDict` when describing structured objects passed around.
- Use `Optional[T]` instead of `Union[T, None]`; avoid `Any` unless strictly necessary.

### Naming Conventions
- snake_case for functions/variables, CapWords for classes, UPPER_SNAKE for constants.
- Suffix async helpers with `_async` if introduced later.
- Reflect device/precision semantics in variable names (`dtype`, `device`, `generator`).

### Error Handling & Logging
- Validate early; raise specific built-in exceptions (`ValueError`, `RuntimeError`, `FileNotFoundError`).
- Use `loguru.logger` for runtime logging; prefer `logger.info`/`warning`/`error` with contextual data.
- Avoid bare `except:`; catch concrete exceptions and re-raise with helpful messages.
- When verifying files, reuse `helpers.verify_file_integrity` instead of duplicating logic.

### Configuration & Constants
- Centralize defaults in `src/config`. Import those constants rather than redefining magic numbers.
- If you need new tunables, add them to `config/model.py` or `config/inference.py` with descriptive names.
- Keep CLI flags in scripts minimal; prefer environment variables (e.g., `ZIMAGE_ATTENTION`).

### Dependencies & Optional Imports
- Guard optional heavyweight imports (Flash Attention, XLA) with try/except and helpful errors.
- When adding new requirements, update `pyproject.toml` and mention them in README Quick Start.

### File & Data Handling
- Always use `Path` utilities for filesystem work; ensure directories exist before writing.
- For large downloads, rely on `huggingface_hub.snapshot_download` via helpers.
- Never hardcode user-specific paths; accept parameters or env vars.

### Performance & Device Usage
- Keep tensors on the device returned by `load_from_local_dir`; avoid mixing dtypes.
- Respect CFG truncation logic inside `pipeline.generate`; don’t regress behavior.
- Provide generator seeds for reproducibility; expose them via function args when adding APIs.

### Documentation & Comments
- Write concise docstrings (Google or NumPy style) for public APIs.
- Use Markdown tables/images only inside docs, not code.
- Inline comments should explain “why,” not “what.”

## 8. Contribution Workflow
1. Open a plan (Todo list) for multi-step changes; summarize before and after tool calls.
2. Read affected files before editing; use the `edit` tool rather than `write` unless creating new files.
3. Keep commits focused; do not commit unless explicitly asked. When requested, follow repo commit style (imperative, short summary + rationale).
4. Run relevant linters/tests locally before surfacing final output. Mention any checks you skipped and why.
5. If you modify CLI behavior, update `README.md` to match new flags or requirements.

## 9. Handling Cursor/Copilot Rules
- Currently, `.cursor/rules/` and `.github/copilot-instructions.md` do **not** exist.
- If they appear later:
  1. Read them entirely.
  2. Copy their constraints into a dedicated section here.
  3. Note their path and scope so future agents inherit them automatically.

## 10. Checklist Before Finishing Any Task
- [ ] Dependencies installed via `pip install -e .[dev]` (if linting/testing needed).
- [ ] Relevant commands executed (lint, format, tests, or inference smoke test).
- [ ] Changes align with style guidelines above.
- [ ] No large binaries or secrets added.
- [ ] README/docs updated when user-facing behavior changed.
- [ ] Final response summarizes changes, highlights validation steps, and suggests next actions if applicable.

Keep this file close to 150 lines; expand only when new tooling/process requirements surface. Update sections promptly whenever the build, lint, or test story evolves.