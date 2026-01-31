<script lang="ts">
  import { onMount } from "svelte";
  import {
    history,
    selectedImage,
    generationState,
    settings,
    serverReady,
    serverStatusMessage,
    checkServerStatus,
    fetchHistory,
    generateImage,
    deleteImage,
    getDownloadUrl,
    playNotificationSound,
    type ImageRecord,
  } from "$lib/stores/generation";

  let prompt = "";
  let inputElement: HTMLTextAreaElement;

  // Poll for server status on mount
  onMount(() => {
    const checkStatus = async () => {
      await checkServerStatus();
      if ($serverReady) {
        await fetchHistory();
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  });

  async function handleSubmit() {
    if (!prompt.trim() || $generationState.isGenerating) return;
    const result = await generateImage(prompt.trim());
    if (result) {
      prompt = "";
      selectedImage.set(result);
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function selectImage(img: ImageRecord) {
    selectedImage.set(img);
  }

  function closeViewer() {
    selectedImage.set(null);
  }

  function enhanceFromImage(img: ImageRecord) {
    prompt = img.prompt;
    selectedImage.set(null);
    inputElement?.focus();
  }

  function downloadImage(img: ImageRecord) {
    const link = document.createElement("a");
    link.href = getDownloadUrl(img.id);
    link.download = `zimage_${img.id}.png`;
    link.click();
  }

  function formatTime(totalSeconds: number): string {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  }

  function toggleSound() {
    settings.update((s) => {
      const newEnabled = !s.soundEnabled;
      // Play sound when enabling to confirm it works
      if (newEnabled) {
        playNotificationSound();
      }
      return { ...s, soundEnabled: newEnabled };
    });
  }

  async function handleDelete(img: ImageRecord) {
    if (confirm("Delete this image?")) {
      await deleteImage(img.id);
    }
  }
</script>

<div class="app" data-theme={$settings.theme}>
  <!-- Main content area -->
  <main class="main-area">
    {#if $selectedImage}
      <!-- Fullscreen viewer -->
      <div
        class="viewer-overlay"
        on:click={closeViewer}
        on:keydown={(e) => e.key === "Escape" && closeViewer()}
        role="dialog"
        tabindex="-1"
      >
        <div class="viewer-content" on:click|stopPropagation role="document">
          <button
            class="viewer-close"
            on:click={closeViewer}
            aria-label="Close viewer">×</button
          >
          <img
            src={$selectedImage.url}
            alt={$selectedImage.prompt}
            class="viewer-image"
          />
          <div class="viewer-info">
            <p class="viewer-prompt">{$selectedImage.prompt}</p>
            <div class="viewer-meta">
              <span class="meta-item">{$selectedImage.style}</span>
              <span class="meta-item"
                >{$selectedImage.width}×{$selectedImage.height}</span
              >
              <span class="meta-item"
                >{$selectedImage.generation_time.toFixed(1)}s</span
              >
            </div>
            <div class="viewer-actions">
              <button
                class="btn btn-primary"
                on:click={() => downloadImage($selectedImage!)}
              >
                Download
              </button>
              <button
                class="btn btn-secondary"
                on:click={() => enhanceFromImage($selectedImage!)}
              >
                Enhance from this
              </button>
              <button
                class="btn btn-danger"
                on:click={() => handleDelete($selectedImage!)}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    {:else if $generationState.isGenerating}
      <!-- Generating state -->
      <div class="generating-state">
        <div class="progress-container">
          <div class="progress-bar-bg">
            <div
              class="progress-bar-fill"
              style="width: {$generationState.progress}%"
            ></div>
          </div>
          <p class="generating-text">
            {$generationState.message || "Generating..."}
          </p>
          <p class="generating-timer">{formatTime($generationState.elapsedSeconds)}</p>
        </div>
      </div>
    {:else if $generationState.error}
      <!-- Error state -->
      <div class="error-state">
        <p class="error-text">⚠️ {$generationState.error}</p>
      </div>
    {:else if !$serverReady}
      <!-- Waiting for server -->
      <div class="waiting-state">
        <div class="spinner"></div>
        <p class="waiting-text">{$serverStatusMessage}</p>
        <p class="waiting-hint">
          The model takes a few seconds to initialize on first run
        </p>
      </div>
    {:else if $generationState.currentImages.length > 0}
      <!-- Show results of recent batch -->
      <div
        class="results-grid results-count-{$generationState.currentImages
          .length}"
      >
        {#each $generationState.currentImages as img}
          <button class="result-item" on:click={() => selectImage(img)}>
            <img src={img.url} alt={img.prompt} />
          </button>
        {/each}
      </div>
    {:else}
      <!-- Empty state -->
      <div class="empty-state">
        <h1 class="empty-title">Z-Image Studio</h1>
        <p class="empty-subtitle">Describe what you'd like to create</p>
      </div>
    {/if}
  </main>

  <!-- Right sidebar: Image gallery -->
  <aside class="sidebar">
    <h2 class="sidebar-title">Recent</h2>
    {#if $history.length === 0}
      <p class="sidebar-empty">Generated images will appear here</p>
    {:else}
      <div class="gallery">
        {#each $history as img (img.id)}
          <div class="gallery-item-wrapper">
            <button
              class="gallery-item"
              on:click={() => selectImage(img)}
              aria-label="View {img.prompt}"
            >
              <img src={img.url} alt={img.prompt} loading="lazy" />
            </button>
            <button
              class="gallery-item-delete"
              on:click|stopPropagation={() => handleDelete(img)}
              aria-label="Delete image"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"
                />
              </svg>
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </aside>

  <!-- Bottom prompt input -->
  <footer class="prompt-bar">
    <div class="settings-row">
      <div class="setting-group">
        <label class="setting-label">Style</label>
        <div class="toggle-group">
          <button
            class="toggle-btn"
            class:active={$settings.style === "realistic"}
            on:click={() =>
              settings.update((s) => ({ ...s, style: "realistic" }))}
          >
            Realistic
          </button>
          <button
            class="toggle-btn"
            class:active={$settings.style === "anime"}
            on:click={() => settings.update((s) => ({ ...s, style: "anime" }))}
          >
            Anime
          </button>
        </div>
      </div>
      <div class="setting-group">
        <label class="setting-label">Aspect</label>
        <div class="toggle-group">
          {#each ["16:9", "1:1", "9:16", "4:3"] as ratio}
            <button
              class="toggle-btn toggle-btn-small"
              class:active={$settings.aspectRatio === ratio}
              on:click={() =>
                settings.update((s) => ({ ...s, aspectRatio: ratio }))}
            >
              {ratio}
            </button>
          {/each}
        </div>
      </div>
      <div class="setting-group">
        <label class="setting-label">Quality</label>
        <div class="toggle-group">
          {#each ["Fast", "Draft", "Standard", "High", "Ultra"] as quality}
            <button
              class="toggle-btn toggle-btn-small"
              class:active={$settings.quality === quality}
              on:click={() =>
                settings.update((s) => ({ ...s, quality: quality }))}
            >
              {quality}
            </button>
          {/each}
        </div>
      </div>
      <div class="setting-group">
        <label class="setting-label">Images</label>
        <div class="toggle-group">
          {#each [1, 2, 4] as count}
            <button
              class="toggle-btn toggle-btn-small"
              class:active={$settings.numImages === count}
              on:click={() =>
                settings.update((s) => ({ ...s, numImages: count }))}
            >
              {count}
            </button>
          {/each}
        </div>
      </div>
      <div class="setting-group">
        <label class="setting-label">Theme</label>
        <div class="toggle-group">
          {#each ["studio", "midnight", "nordic"] as theme}
            <button
              class="toggle-btn toggle-btn-small"
              class:active={$settings.theme === theme}
              on:click={() => settings.update((s) => ({ ...s, theme: theme }))}
            >
              {theme}
            </button>
          {/each}
        </div>
      </div>
      <div class="setting-group">
        <label class="setting-label">Sound</label>
        <button
          class="toggle-btn toggle-btn-icon"
          class:active={$settings.soundEnabled}
          on:click={toggleSound}
          aria-label={$settings.soundEnabled ? "Disable sound" : "Enable sound"}
        >
          {#if $settings.soundEnabled}
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 5L6 9H2v6h4l5 4V5z"/>
              <path d="M19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07"/>
            </svg>
          {:else}
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 5L6 9H2v6h4l5 4V5z"/>
              <line x1="23" y1="9" x2="17" y2="15"/>
              <line x1="17" y1="9" x2="23" y2="15"/>
            </svg>
          {/if}
        </button>
      </div>
    </div>
    <div class="prompt-input-container">
      <textarea
        bind:this={inputElement}
        bind:value={prompt}
        placeholder="A serene Japanese garden at sunset, with cherry blossoms..."
        class="prompt-input"
        on:keydown={handleKeydown}
        disabled={$generationState.isGenerating || !$serverReady}
        rows="1"
      ></textarea>
      <button
        class="generate-btn"
        on:click={handleSubmit}
        disabled={!prompt.trim() ||
          $generationState.isGenerating ||
          !$serverReady}
        aria-label="Generate image"
      >
        {#if $generationState.isGenerating}
          <span class="btn-spinner"></span>
        {:else}
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        {/if}
      </button>
    </div>
  </footer>
</div>

<style>
  .app {
    display: grid;
    grid-template-areas:
      "main sidebar"
      "footer sidebar";
    grid-template-columns: 1fr 280px;
    grid-template-rows: 1fr auto;
    min-height: 100vh;
    background: var(--color-bg);
  }

  /* Main area */
  .main-area {
    grid-area: main;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-2xl);
    position: relative;
  }

  /* Empty state */
  .empty-state {
    text-align: center;
    max-width: 480px;
  }

  .empty-title {
    font-family: var(--font-serif);
    font-size: 3rem;
    font-weight: 400;
    color: var(--color-text);
    margin-bottom: var(--space-md);
    letter-spacing: -0.03em;
  }

  .empty-subtitle {
    color: var(--color-text-muted);
    font-size: 1.125rem;
  }

  /* Waiting/Generating states */
  .waiting-state,
  .generating-state,
  .error-state {
    text-align: center;
  }

  .waiting-text,
  .generating-text {
    font-size: 1.125rem;
    color: var(--color-text-secondary);
    margin-top: var(--space-lg);
  }

  /* Progress Bar */
  .progress-container {
    width: 320px;
    margin: 0 auto;
  }

  .progress-bar-bg {
    width: 100%;
    height: 4px;
    background: var(--color-surface);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .progress-bar-fill {
    height: 100%;
    background: var(--color-accent);
    transition: width 0.3s ease;
  }

  /* Results Grid */
  .results-grid {
    display: grid;
    gap: var(--space-md);
    width: 100%;
    max-width: 1200px;
  }

  .results-count-1 {
    grid-template-columns: 1fr;
  }
  .results-count-2 {
    grid-template-columns: 1fr 1fr;
  }
  .results-count-4 {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
  }

  .result-item {
    display: block;
    width: 100%;
    aspect-ratio: 16/9;
    border-radius: var(--radius-md);
    overflow: hidden;
    cursor: pointer;
    border: none;
    padding: 0;
    box-shadow: var(--shadow-md);
    transition: transform var(--transition-fast);
  }

  .result-item:hover {
    transform: scale(1.02);
  }

  .result-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .waiting-hint {
    color: var(--color-text-muted);
    font-size: 0.875rem;
    margin-top: var(--space-sm);
  }

  .error-text {
    color: var(--color-error);
    font-size: 1rem;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--color-border);
    border-top-color: var(--color-accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* Viewer overlay */
  .viewer-overlay {
    position: fixed;
    inset: 0;
    background: rgba(26, 24, 22, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
    animation: fadeIn 0.2s ease;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .viewer-content {
    position: relative;
    max-width: 90vw;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .viewer-close {
    position: absolute;
    top: -40px;
    right: 0;
    width: 32px;
    height: 32px;
    font-size: 1.5rem;
    color: white;
    background: transparent;
    border: none;
    cursor: pointer;
    opacity: 0.7;
    transition: opacity var(--transition-fast);
  }

  .viewer-close:hover {
    opacity: 1;
  }

  .viewer-image {
    max-width: 100%;
    max-height: 70vh;
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
  }

  .viewer-info {
    margin-top: var(--space-lg);
    text-align: center;
    color: white;
    max-width: 600px;
  }

  .viewer-prompt {
    font-family: var(--font-serif);
    font-size: 1.125rem;
    line-height: 1.5;
    margin-bottom: var(--space-md);
    opacity: 0.9;
  }

  .viewer-meta {
    display: flex;
    gap: var(--space-md);
    justify-content: center;
    margin-bottom: var(--space-lg);
  }

  .meta-item {
    font-size: 0.875rem;
    opacity: 0.7;
    padding: var(--space-xs) var(--space-sm);
    background: rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-sm);
  }

  .viewer-actions {
    display: flex;
    gap: var(--space-md);
    justify-content: center;
  }

  /* Buttons */
  .btn {
    padding: var(--space-sm) var(--space-lg);
    border-radius: var(--radius-md);
    font-weight: 500;
    transition: all var(--transition-fast);
    cursor: pointer;
  }

  .btn-primary {
    background: var(--color-accent);
    color: white;
    border: none;
  }

  .btn-primary:hover {
    background: var(--color-accent-hover);
  }

  .btn-secondary {
    background: transparent;
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.3);
  }

  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  /* Sidebar */
  .sidebar {
    grid-area: sidebar;
    background: var(--color-bg-elevated);
    border-left: 1px solid var(--color-border-subtle);
    padding: var(--space-lg);
    overflow-y: auto;
    max-height: 100vh;
  }

  .sidebar-title {
    font-family: var(--font-sans);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--color-text-muted);
    margin-bottom: var(--space-md);
  }

  .sidebar-empty {
    color: var(--color-text-muted);
    font-size: 0.875rem;
    text-align: center;
    padding-top: var(--space-xl);
  }

  .gallery {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .gallery-item {
    display: block;
    width: 100%;
    aspect-ratio: 16/9;
    border-radius: var(--radius-md);
    overflow: hidden;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all var(--transition-fast);
    padding: 0;
    background: var(--color-surface);
  }

  .gallery-item:hover {
    border-color: var(--color-accent);
    transform: scale(1.02);
  }

  .gallery-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  /* Prompt bar */
  .prompt-bar {
    grid-area: footer;
    background: var(--color-bg-elevated);
    border-top: 1px solid var(--color-border-subtle);
    padding: var(--space-md) var(--space-xl);
  }

  .settings-row {
    display: flex;
    gap: var(--space-xl);
    margin-bottom: var(--space-md);
  }

  .setting-group {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }

  .setting-label {
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-muted);
  }

  .toggle-group {
    display: flex;
    gap: 2px;
    background: var(--color-surface);
    padding: 2px;
    border-radius: var(--radius-md);
  }

  .toggle-btn {
    padding: var(--space-xs) var(--space-md);
    font-size: 0.875rem;
    border-radius: calc(var(--radius-md) - 2px);
    color: var(--color-text-secondary);
    transition: all var(--transition-fast);
  }

  .toggle-btn:hover {
    color: var(--color-text);
  }

  .toggle-btn.active {
    background: var(--color-bg-elevated);
    color: var(--color-text);
    box-shadow: var(--shadow-sm);
  }

  .toggle-btn-small {
    padding: var(--space-xs) var(--space-sm);
    font-size: 0.75rem;
  }

  .toggle-btn-icon {
    padding: var(--space-xs) var(--space-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-surface);
    border-radius: var(--radius-md);
  }

  .toggle-btn-icon.active {
    background: var(--color-accent-subtle);
    color: var(--color-accent);
  }

  .prompt-input-container {
    display: flex;
    gap: var(--space-sm);
    align-items: flex-end;
  }

  .prompt-input {
    flex: 1;
    padding: var(--space-md);
    font-size: 1rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-bg);
    resize: none;
    min-height: 52px;
    max-height: 150px;
    transition: border-color var(--transition-fast);
  }

  .prompt-input:focus {
    outline: none;
    border-color: var(--color-accent);
  }

  .prompt-input::placeholder {
    color: var(--color-text-muted);
  }

  .prompt-input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .generate-btn {
    width: 52px;
    height: 52px;
    border-radius: var(--radius-full);
    background: var(--color-accent);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast);
    flex-shrink: 0;
  }

  .generate-btn:hover:not(:disabled) {
    background: var(--color-accent-hover);
    transform: scale(1.05);
  }

  .generate-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-danger {
    background: rgba(196, 92, 92, 0.1);
    color: #c45c5c;
    border: 1px solid rgba(196, 92, 92, 0.3);
  }

  .btn-danger:hover {
    background: #c45c5c;
    color: white;
  }

  .generating-timer {
    font-size: 0.875rem;
    color: var(--color-text-muted);
    margin-top: var(--space-xs);
  }

  .gallery-item-wrapper {
    position: relative;
  }

  .gallery-item-delete {
    position: absolute;
    top: var(--space-xs);
    right: var(--space-xs);
    width: 28px;
    height: 28px;
    border-radius: var(--radius-sm);
    background: rgba(0, 0, 0, 0.4);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity var(--transition-fast);
    backdrop-filter: blur(4px);
  }

  .gallery-item-wrapper:hover .gallery-item-delete {
    opacity: 1;
  }

  .gallery-item-delete:hover {
    background: var(--color-error);
  }

  .btn-spinner {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .app {
      grid-template-areas:
        "main"
        "footer";
      grid-template-columns: 1fr;
    }

    .sidebar {
      display: none;
    }
  }
</style>
