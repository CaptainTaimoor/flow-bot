# Architecture

The system uses a highly decoupled architecture designed to accommodate future expansion into a full content automation pipeline.

- **FastAPI / Uvicorn:** Serves the backend API (`src/api`) and the simple dashboard (`src/api/dashboard.html`).
- **SQLAlchemy / SQLite:** Manages local persistence for Job Queues (`src/database`), keeping a firm record of metadata.
- **Playwright:** Drives a persistent Chromium instance to manage Google Session authentication without exposing credentials.
- **JobRunner:** A background asyncio loop (`src/jobs/runner.py`) that monitors the DB queue and routes prompts to the browser.
- **GoogleFlowAdapter:** Encapsulates the specific DOM selectors and workflow steps for Google Flow (`src/flow/adapter.py`).

## Future Scalability
The adapter pattern ensures that if Google Flow's UI changes, only `src/flow/adapter.py` needs an update. Future endpoints (like Gemini Veo APIs) can be implemented alongside it.
