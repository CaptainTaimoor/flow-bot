# Google Flow Video Generation Automation Bot

A Windows-first, production-structured Google Flow video generation automation bot. 
This tool automates the process of entering prompts, generating videos via Google Flow, waiting for completion, and downloading the finalized assets locally.

## Features
- **Local Dashboard:** Monitor jobs, submit prompts, and review generated videos.
- **Persistent Sessions:** Uses Playwright to maintain an authenticated Google session securely in your `runtime/` directory.
- **Job Queue:** SQLite-backed queue ensures generations are retried on error and metadata is permanently stored.
- **Configurable Constraints:** Controls to limit daily generations, job concurrency, and timeouts.
- **REST API:** Easily integratable with future automated content pipelines (e.g. script generation).

## Quickstart

1. **Install Requirements:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Initialize Environment:**
   Copy `.env.example` to `.env` and adjust settings as needed.
   ```powershell
   python init_env.py
   ```

3. **Authentication:**
   Run the CLI auth command to open the browser and manually log in to Google Flow.
   ```powershell
   python -m src.cli.main auth
   ```

4. **Start the Bot & Dashboard:**
   ```powershell
   python -m src.cli.main start
   ```
   Open `http://localhost:8000` to access the dashboard.

## Tests
- Run unit tests: `pytest tests/unit`
- Run safe browser test (no generation): `pytest tests/browser/test_ui_safe.py`
- Run one real generation (consumes credit!): `pytest tests/browser/test_real_generation.py -s`

## Architecture
See `docs/ARCHITECTURE.md` for full design notes.
