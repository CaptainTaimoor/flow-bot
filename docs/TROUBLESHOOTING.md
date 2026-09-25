# Troubleshooting & Operational Runbook

This guide provides actionable solutions for operational scenarios and Google Flow edge cases.

---

## 1. Browser Profile Lock Contention
**Symptoms:**
- `Error: Target closed`, `EBUSY`, or Playwright fails with `Process singleton lock held`.

**Root Cause:**
- Playwright Chromium persistent profile directories (`runtime/profile`) cannot be accessed by two concurrent browser processes on Windows.

**Solution:**
- The application uses `SingletonBrowserService` (`src/browser/service.py`) which manages an internal `asyncio.Lock()` around `lease_page()`.
- Ensure other terminal commands or external Chrome instances targeting `runtime/profile` are closed before running automation.
- If a stray Chrome process is orphaned:
  ```powershell
  Get-Process chrome | Stop-Process -Force
  ```

---

## 2. Authentication Status & Google Login
**Symptoms:**
- `AuthState.NOT_AUTHENTICATED` or `AuthState.CHALLENGE_REQUIRED`.
- Automation stops at login page or skips execution.

**Solution:**
- Run the dedicated interactive authentication CLI tool:
  ```powershell
  .\venv\Scripts\python.exe -m src.cli.main auth
  ```
- A visible browser window will launch. Log in to your Google Account.
- Once authenticated and Flow loads, the CLI detects the URL change, updates status to `AUTHENTICATED`, and cleanly saves the session cookies to `runtime/profile`.

---

## 3. Gallery Announcements & Hero Modals
**Symptoms:**
- Automation lands on `https://flow.google.com/` and sees a promotional banner (e.g. *"Your Google AI plan now comes with 50 additional Flow credits daily"*).

**Handling:**
- `FlowProjectManager.ensure_project_open()` detects this view and automatically:
  1. Closes the announcement banner via `FlowSelectors.HERO_CLOSE_BTN`.
  2. If `FLOW_PROJECT_MODE="REUSE_SINGLE_PROJECT"`, clicks the most recent project card (`a[href*='/project/']` or `flow-project-card`) to re-enter your existing canvas.
  3. If no project card exists, clicks `Start Creating` or `+ New project`.
  4. Waits up to 20s for the project URL (`/project/`) and prompt input (`.ProseMirror`) to stabilize.

---

## 4. Canvas Tile Rendering Detection
**Symptoms:**
- Generation wait loop times out even though the video finished rendering.

**Root Cause:**
- Google Flow resets the CSS style `--progress-percent: 0%;` on `.progress-bar` upon completion, rather than setting it to `100%` or removing the element from the DOM.

**Handling:**
- `FlowGenerationExecutor.wait_for_tile_completion()` checks multiple truth signals:
  1. `mat-icon:has-text('play_circle')`: Visibly rendered in the tile center when ready for playback.
  2. Thumbnail image (`img.thumbnail`) loaded with a valid `src` starting with `https://flow.google.com/asb/` or `blob:`.
  3. Options hotbar button (`button[aria-label*='More' i]`) active.
  4. Error text detection (`:text-matches('error|failed', 'i')`) to immediately fail instead of hanging.

---

## 5. Video Download Submenu
**Symptoms:**
- `expect_download` times out when clicking `Download`.

**Root Cause:**
- In Google Flow, clicking the tile menu's `Download` item does not directly trigger an HTTP download; it opens a secondary resolution submenu with items:
  - `720p` (`Original size`)
  - `1080p` (`Upscaled`)
  - `270p` (`Animated GIF`)

**Handling:**
- `FlowAssetTracker.download_tile_asset()` handles this two-tier interaction:
  1. Hovers over the target tile to reveal the hotbar.
  2. Clicks `More options`.
  3. Clicks `Download` in the opened menu.
  4. Explicitly waits for `DOWNLOAD_QUALITY_OPTIONS` (`:text-matches('720p', 'i')`).
  5. Clicks `720p` inside `page.expect_download(timeout=30000)` and saves the file.

---

## 6. Media Validation Failures
**Symptoms:**
- `FFprobe validation failed` or `is_valid is False`.

**Checks:**
1. Ensure FFmpeg / FFprobe is available on the system PATH.
2. Check downloaded file size: files under 1,000 bytes indicate network disconnection or HTML error pages.
3. Review video metadata in `data/media/videos/` using:
   ```powershell
   ffprobe -v error -show_format -show_streams data/media/videos/<file>.mp4
   ```
