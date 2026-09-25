# Google Flow Automation Bot V2 — Production Architecture

## System Overview
The Google Flow Automation Bot V2 is a production-grade, asynchronous web automation and workflow orchestration system designed to reliably drive Google Flow (`https://flow.google.com/`). It combines a modern single-page dashboard with an enterprise-grade backend, deterministic browser automation, deep media validation, and strict credit safety policies.

```
                      +---------------------------------------+
                      |   React 19 + Vite Dashboard (SPA)     |
                      |   8 Views: Queue, Media, Studio, etc. |
                      +-------------------+-------------------+
                                          | HTTP REST / SSE Stream
                                          v
                      +---------------------------------------+
                      |       FastAPI Backend Service         |
                      |  Routes: /jobs, /status, /settings    |
                      +---------+-------------------+---------+
                                |                   |
                 Job Queue Loop |                   | Real-Time Diagnostics
                                v                   v
+-----------------------------------+     +-----------------------------------+
|      JobRunner State Machine      |     |     FlowCapabilityDetector        |
|  28 Lifecycle States, Auto-Retry  |     |  Truthful DOM Model & Token Audit |
+-----------------+-----------------+     +-----------------+-----------------+
                  |                                         |
                  +--------------------+--------------------+
                                       |
                                       v
                      +---------------------------------------+
                      |       SingletonBrowserService         |
                      | Exclusive Profile Lock (asyncio.Lock) |
                      |    Chromium Persistent Context        |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |        GoogleFlowAdapter Facade       |
                      |  - FlowProjectManager (Canvas/Gallery)|
                      |  - FlowGenerationExecutor (Submit/Wait|
                      |  - FlowAssetTracker (Correlation/DL)  |
                      |  - FlowReconciliationManager (Retry)  |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |             MediaService              |
                      |  - Deep FFprobe Stream Inspection     |
                      |  - FFmpeg Dynamic Thumbnail Gen       |
                      |  - Path Traversal Security Guards     |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |    SQLite Persistent Store (WAL)      |
                      |  Jobs, Generations, Settings, Audit   |
                      +---------------------------------------+
```

---

## 1. Domain & Lifecycle State Machine (`src/models/domain.py`)
The system manages generation jobs across **28 explicit lifecycle states** to eliminate ambiguous failure modes:

| Phase | States |
|---|---|
| **Intake & Queue** | `QUEUED`, `CLAIMED`, `PENDING_AUTHENTICATION`, `AUTHENTICATED` |
| **Preflight** | `DISCOVERING_CAPABILITIES`, `CHECKING_CREDITS`, `SELECTING_PROJECT`, `CONFIGURING_PARAMETERS` |
| **Snapshotting** | `TAKING_BASELINE_SNAPSHOT` |
| **Submission** | `ENTERING_PROMPT`, `SUBMITTING`, `WAITING_FOR_CONFIRMATION`, `CONFIRMED` |
| **Correlation** | `LOCATING_ASSET_TILE` |
| **Generation** | `GENERATING`, `UPDATING_PROGRESS` |
| **Post-Render** | `RENDER_COMPLETE`, `INITIATING_DOWNLOAD`, `DOWNLOADING_MEDIA`, `DOWNLOAD_COMPLETE` |
| **Validation** | `VALIDATING_MEDIA`, `GENERATING_THUMBNAIL`, `CORRELATION_AUDIT` |
| **Terminal** | `COMPLETED`, `FAILED`, `CANCELLED`, `RECONCILED` |

---

## 2. Dynamic Runtime Configuration (`src/config/runtime_config.py`)
- Provides live configuration parameter resolution (`RuntimeConfigResolver`).
- Overlays file-based `.env` defaults with database-persisted overrides from SQLite `settings` table.
- Enables changing `CREDIT_SAFETY_MODE`, `AUTO_CONFIRM_GENERATION`, `FLOW_PROJECT_MODE`, or timeouts via the Settings UI **without restarting the application**.

---

## 3. Concurrency & Browser Profile Isolation (`src/browser/service.py`)
- Persistent Chromium user data directories (`runtime/profile`) contain session cookies and authentication tokens.
- Chromium strictly forbids concurrent processes sharing a single profile directory on Windows.
- `SingletonBrowserService` enforces an application-level `asyncio.Lock()` inside `lease_page()`:
  - Exactly one automation worker or diagnostic check can lease the page at any given instant.
  - Ensures clean teardown, page recycling, and zero profile corruption.

---

## 4. Truthful Capability & Credit Discovery (`src/flow/capability_detection.py`)
- **Zero Hallucination Guarantee:** The system never invents model names, token costs, or limits.
- **DOM Inspection:** Model identifiers are extracted live from `flow-model-select button` and its Material menu options.
- **Credit Discovery:** Credit balances are parsed from the header tier chip (`.flow-user-tier-chip`). If omitted or obscured by Flow, balance is set to `None` and status to `UNKNOWN`.
- **Annotation:** If live extraction fails, fallback defaults are explicitly annotated with `model_source="fallback"`.

---

## 5. Credit Safety Engine (`src/flow/credit_policy.py`)
Three operational safety modes:
- **`STRICT`**: Requires verified credit cost and sufficient balance before submission unless explicitly confirmed by the user.
- **`WARN`**: Logs unverified status but permits execution within daily caps.
- **`ALLOW_UNKNOWN`**: Executes based on daily generation quotas.

**Daily Quotas:** Atomically verified against SQLite (`MAX_DAILY_GENERATIONS`).

---

## 6. Modular Flow Automation Facade (`src/flow/`)
- `FlowProjectManager`: Handles gallery views, hero announcement modals (`Start Creating`), recent project card resumption, and project workspace entrance.
- `FlowGenerationExecutor`: Fills prompt inputs (`.ProseMirror`), handles auto-confirmation dialogues, and monitors tile rendering with live progress callbacks and completion detection (`play_circle`).
- `FlowAssetTracker`: Employs a **4-Layer Deterministic Correlation Engine** (Snapshot Diff, Keyword Overlap, Active Progress Bar, Recency) to score and isolate the newly generated tile, followed by a two-tier download interaction (`More options` -> `Download` -> `720p`).
- `FlowReconciliationManager`: Detects prior in-flight renders to prevent duplicate billing during retries.

---

## 7. Media Processing & Strict FFprobe Validation (`src/media/service.py`)
- **FFprobe Inspection:** Validates container integrity, video stream existence, codec (`h264`, `vp9`, `av1`), dimensions (`width`, `height`), duration, and frame rate.
- **Thumbnail Creation:** Extracts a representative frame at 15% duration using FFmpeg.
- **Path Traversal Security:** Resolves media files with `Path.resolve()` against `data/media/` and rejects paths with `..` or traversal escapes.

---

## 8. Persistence & Schema Migration (`src/database/`)
- SQLite database (`data/flow_bot.db`) with WAL mode enabled.
- Auto-migrating columns in `init_db()` ensure backward compatibility without dropping tables.
- Full tracking of requested configuration vs effective configuration, correlation confidence, and audit proof JSON.
