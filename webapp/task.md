# Z-Image Web Application - Task Breakdown

## Phase 1: Backend (FastAPI + Persistent Model Server)
- [x] Create FastAPI server with startup model loading
- [x] Implement WebSocket endpoint for real-time generation progress
- [x] Build REST endpoints for image generation, history, and settings
- [ ] Add reference image upload and processing support (deferred - Z-Image-Edit not released)
- [x] Implement image history storage (last 20 images)
- [ ] Add model update checker endpoint

## Phase 2: Frontend (SvelteKit)
- [x] Initialize SvelteKit project with custom design system
- [x] Create main layout with centered prompt input at bottom
- [x] Build image gallery component (right sidebar, last 20 images)
- [x] Implement fullscreen image viewer with download
- [x] Add style selector (anime/realistic) and aspect ratio controls
- [ ] Build reference image uploader component (deferred - Z-Image-Edit not released)
- [x] Add "enhance from this image" workflow
- [ ] Create model update check UI

## Phase 3: Integration & Polish
- [x] Connect frontend to backend via HTTP/WebSocket
- [x] Add real-time generation progress display
- [x] Implement batch generation (1, 2, 4 images)
- [ ] Implement image-to-image workflow (enhance existing image) (deferred - Z-Image-Edit not released)
- [x] Polish UI animations and transitions
- [x] Implement image deletion from history
- [x] Add multiple color themes (Dark/Modern/Nordic)
- [x] Add visible generation timers
- [x] Test on M4 Pro with MPS backend (Partial: OOM fixed, quality issue found)
- [ ] DEBUG: Fix "Fuzzy Mess" tiled artifacts in VAE decoding
- [ ] OPTIMIZE: Fix 30-min generation time regression on M4 Pro
- [ ] Final verification and performance tuning
