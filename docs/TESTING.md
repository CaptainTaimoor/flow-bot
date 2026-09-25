# Testing Strategy & Test Suite Guide

## Overview
The testing architecture is split into three disciplined tiers to guarantee fast regression feedback, safe UI testing without credit consumption, and verified end-to-end Flow execution.

---

## 1. Unit Tests (`tests/unit/`)
Unit tests run entirely in-memory with zero network or browser overhead. They validate core logic, schema invariants, policy enforcement, and media validation safety.

### Test Modules:
- `test_domain_and_normalization.py`: Validates 28 explicit lifecycle states, aspect ratio normalizers (`16:9`, `9:16`, `1:1`), duration normalizers, and truthful default capabilities.
- `test_credit_policy.py`: Verifies `STRICT`, `WARN`, and `ALLOW_UNKNOWN` modes, daily generation caps, and balance gating.
- `test_media_validation.py`: Tests FFprobe metadata extraction, codec/resolution/fps validation, path traversal safety, and thumbnail generation.
- `test_queue.py`: Validates atomic job claiming, concurrency gating, and status state machine progression.
- `test_api.py`: Validates FastAPI endpoints (`/health`, `/status`, `/capabilities`, `/jobs`, `/settings`, `/diagnostics`).

### Execution:
```powershell
.\venv\Scripts\python.exe -m pytest tests/unit -v
```

---

## 2. Safe Browser Tests (`tests/browser/`)
These tests launch the Playwright browser and attach to the persistent profile, but **DO NOT submit generation prompts** and **DO NOT consume Google Flow credits**.

### Test Modules:
- `test_ui_safe.py`: Opens Google Flow, verifies Google Account authentication status (`AUTHENTICATED`), checks prompt input visibility, and closes cleanly.
- `test_frontend_dashboard.py`: Verifies the React V2 web UI across all 8 navigation views:
  1. Dashboard (`/`)
  2. Create Video (`/create`)
  3. Jobs Queue (`/jobs`)
  4. Media Library (`/library`)
  5. Flow Studio Live (`/studio`)
  6. Diagnostics & System Health (`/diagnostics`)
  7. Activity Audit Logs (`/audit`)
  8. Bot Settings (`/settings`)
- `test_video_player_qa.py`: Opens the Media Library, clicks a completed video card, and verifies the full video player modal (video playback controls, resolution badge, duration badge, FFprobe metadata, and download button).

### Execution:
```powershell
.\venv\Scripts\python.exe -m pytest tests/browser/test_ui_safe.py -s -v
.\venv\Scripts\python.exe -m pytest tests/browser/test_frontend_dashboard.py -s -v
.\venv\Scripts\python.exe -m pytest tests/browser/test_video_player_qa.py -s -v
```

---

## 3. Real Flow End-to-End Test (`test_real_generation.py`)
This test performs a complete real generation run on Google Flow. **Note: This test consumes account credits.**

### Step-by-Step Flow Verified:
1. Opens Google Flow and dismisses announcement banners.
2. Checks Google authentication status (`AUTHENTICATED`).
3. Discovers live prompt bar capabilities and models.
4. Records baseline asset fingerprint snapshot.
5. Configures model, aspect ratio (`16:9`), duration (`5s`), and output count (`1`).
6. Submits prompt:
   *"A cinematic landscape of a peaceful mountain lake at sunrise, realistic lighting, gentle camera movement."*
7. Detects generated tile using Deterministic Layered Asset Correlation (`HIGH`/`MEDIUM` confidence).
8. Monitors canvas rendering until completed (`100%` or `play_circle` icon).
9. Downloads generated video asset via `More options` -> `Download` -> `720p`.
10. Validates video container, codec (`h264`), resolution (`1280x720`), duration, and fps using deep FFprobe inspection.
11. Generates thumbnail via FFmpeg.

### Execution:
```powershell
.\venv\Scripts\python.exe -m pytest tests/browser/test_real_generation.py -s -v
```
