# Google Flow Video Automation Bot V2 (Production Grade)

A Windows-first, production-grade Google Flow browser automation and video orchestration system. It connects a modern React 19 single-page dashboard with an enterprise-grade FastAPI backend, deterministic browser automation, deep media validation, and strict credit safety policies.

![Sunrise Lake Landscape](data/media/thumbnails/thumb_1_1.jpg)
*Real 720p H.264 video generation on Google Flow verified by FFprobe and captured by the automation engine.*

---

## Key Features

- **Modern V2 Dashboard (React 19 + TypeScript + Tailwind CSS):**
  - **Dashboard (`/`):** Real-time cluster status, active generation monitor, throughput metrics, and quick prompt submission.
  - **Create Video (`/create`):** Rich studio parameter configuration (aspect ratios `16:9`, `9:16`, `1:1`, durations, output count, live prompt character count).
  - **Job Queue (`/jobs`):** Real-time monitoring across 28 lifecycle states, progress bars, cancellation, and retry triggers.
  - **Media Library (`/library`):** Filterable gallery with responsive video player modal, playback controls, resolution/codec inspection, and direct MP4 downloads.
  - **Flow Studio Live (`/studio`):** Live snapshot preview of the Google Flow canvas and prompt bar.
  - **Diagnostics & Health (`/diagnostics`):** Complete system status, browser engine state, profile directory health, and active limits.
  - **Activity Audit Logs (`/audit`):** Immutable log of prompt submissions, correlation evidence, and state transitions.
  - **Settings (`/settings`):** Live configuration editor updating DB-backed runtime parameters without server restarts.

- **Truthful Capability & Credit Discovery:**
  - **Zero Hallucination Guarantee:** Never invents model names, token costs, or balances.
  - Live DOM discovery from `flow-model-select button` and Material menu options.
  - Explicit `UNKNOWN` / `fallback` annotations when parameters are unverified.

- **Credit Safety Policy Engine:**
  - Configurable safety modes: `STRICT`, `WARN`, `ALLOW_UNKNOWN`.
  - Daily generation caps (`MAX_DAILY_GENERATIONS`) verified atomically in SQLite.
  - Auto-confirmation and audit trail recording.

- **Deterministic Layered Asset Correlation:**
  - 4-layer correlation engine: Snapshot Diff, Keyword Overlap, Active Progress Bar style inspection, and DOM Recency.
  - Returns correlated tile with scored confidence (`HIGH`, `MEDIUM`, `LOW`, `FAILED`) and candidate evidence audit JSON.

- **Strict Media Processing & FFprobe Validation:**
  - Validates container format, video stream presence, codec (`h264`, `vp9`, `av1`), dimensions, duration, and frame rate.
  - High-quality thumbnail generation via FFmpeg.
  - Comprehensive path traversal security guards.

- **Singleton Browser Management:**
  - Exclusive application-level `asyncio.Lock()` around `lease_page()` to prevent Chromium profile lock contention on Windows.

---

## Directory Structure

```
├── frontend/                # React 19 + Vite + Tailwind CSS Single-Page Application
│   ├── src/                 # TypeScript source (components, pages, types, api)
│   └── dist/                # Production-compiled static bundle (served by FastAPI)
├── src/
│   ├── api/                 # FastAPI REST routes and keepalive SSE endpoints
│   ├── browser/             # Singleton browser manager and profile leasing
│   ├── config/              # Runtime dynamic config resolver and settings
│   ├── database/            # SQLAlchemy models, SQLite WAL database, migrations
│   ├── flow/                # Modular Google Flow engine (selectors, adapter, etc.)
│   ├── jobs/                # Job queue and 28-state runner state machine
│   └── media/               # Media service, FFprobe validator, FFmpeg thumbnailer
├── data/                    # Persistent SQLite database and media storage
│   ├── media/videos/        # Downloaded MP4 video assets
│   └── media/thumbnails/    # Generated JPEG video thumbnails
├── docs/                    # Architectural and operational documentation
│   ├── ARCHITECTURE.md      # Detailed system design and state machine specification
│   ├── FLOW_CAPABILITIES.md # DOM capability detection and model truthfulness
│   ├── CREDIT_POLICY.md     # Safety modes and daily generation caps
│   ├── TESTING.md           # Test suite architecture and execution guide
│   └── TROUBLESHOOTING.md   # Runbook for operational edge cases
└── tests/
    ├── unit/                # 20 fast in-memory unit tests
    └── browser/             # Safe UI tests and real Flow generation E2E test
```

---

## Quickstart

### 1. Prerequisites
- Windows 10/11 or modern Linux / macOS
- Python 3.11+
- Node.js 18+ (for frontend development)
- FFmpeg and FFprobe installed and available on system PATH

### 2. Setup Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

### 3. Google Account Authentication
Authenticate your Google Account into the local persistent profile (`runtime/profile`):
```powershell
python -m src.cli.main auth
```
*A browser window opens to `https://flow.google.com/`. Complete Google sign-in. The CLI detects login and saves the persistent profile session.*

### 4. Build Frontend Bundle (Optional / Prebuilt)
```powershell
cd frontend
npm install
npm run build
cd ..
```

### 5. Launch Application
```powershell
python -m src.cli.main start
```
Open **`http://localhost:8000`** in your browser to access the dashboard.

---

## Running Tests

### Unit Tests (Fast, 20 test cases, zero browser overhead)
```powershell
pytest tests/unit -v
```

### Safe Browser Tests (Verifies Flow & Dashboard without spending credits)
```powershell
pytest tests/browser/test_ui_safe.py -s -v
pytest tests/browser/test_frontend_dashboard.py -s -v
pytest tests/browser/test_video_player_qa.py -s -v
```

### Controlled Real Flow Generation Test (Consumes Google Flow credits)
```powershell
pytest tests/browser/test_real_generation.py -s -v
```

---

## Documentation
- [System Architecture](docs/ARCHITECTURE.md)
- [Flow Capability Truthfulness](docs/FLOW_CAPABILITIES.md)
- [Credit Safety Policies](docs/CREDIT_POLICY.md)
- [Testing Suite Guide](docs/TESTING.md)
- [Troubleshooting Runbook](docs/TROUBLESHOOTING.md)
