import os
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from src.config.settings import settings
from src.database.db import init_db
from src.api.routes import router as api_router
from src.jobs.runner import job_runner

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("flow_bot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database tables & directories exist
    logger.info("Initializing Google Flow Bot V2 backend...")
    init_db()

    # Start background JobRunner loop
    runner_task = asyncio.create_task(job_runner.start_loop())
    logger.info("JobRunner background task dispatched.")

    yield

    # Shutdown: gracefully stop runner
    logger.info("Shutting down Google Flow Bot V2 backend...")
    await job_runner.stop()
    runner_task.cancel()
    try:
        await runner_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="Production-structured Google Flow Video Automation Control Center",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router)

# Mount frontend static files if built
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    logger.info(f"Serving built React frontend from {FRONTEND_DIST}")
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/", include_in_schema=False)
    def index():
        return HTMLResponse(
            """<!DOCTYPE html>
            <html>
            <head><title>Google Flow Automation Bot V2</title></head>
            <body style="font-family:sans-serif;background:#0f172a;color:#f8fafc;padding:40px;text-align:center;">
                <h1 style="color:#38bdf8;">Google Flow Bot V2 Backend Active</h1>
                <p>FastAPI API is online at <code>/api/v1</code>.</p>
                <p><a style="color:#60a5fa;" href="/docs">Open Interactive API Docs (Swagger)</a></p>
            </body>
            </html>"""
        )

def main():
    logger.info(f"Starting server at http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
    )

if __name__ == "__main__":
    main()
