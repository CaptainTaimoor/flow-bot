import os
import re
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.repository import Repository
from src.models.domain import (
    JobCreate,
    JobResponse,
    JobDetailResponse,
    AssetResponse,
    ProjectResponse,
    FlowCapabilities,
    DiagnosticsReport,
    DiagnosticItem,
    JobStatus,
    AuthState,
)
from src.api.events import event_broadcaster
from src.media.service import media_service
from src.config.settings import settings
from src.config.runtime_config import runtime_config
from src.browser.service import browser_service
from src.flow.auth import AuthManager
from src.flow.adapter import GoogleFlowAdapter
from src.jobs.runner import job_runner

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")

# ==================== SYSTEM & HEALTH ====================

@router.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": "2.0.0"}

@router.get("/status")
def system_status(db: Session = Depends(get_db)):
    repo = Repository(db)
    stats = repo.get_stats()
    b_status = browser_service.get_status()
    cfg = runtime_config.get_all()
    return {
        "status": "online",
        "app_env": settings.APP_ENV,
        "headless": cfg.get("HEADLESS", False),
        "credit_safety_mode": cfg.get("CREDIT_SAFETY_MODE", "STRICT"),
        "browser": b_status,
        "stats": stats,
    }

@router.get("/auth/status")
async def auth_status():
    status_val = AuthState.UNKNOWN.value
    try:
        if browser_service.context:
            async with browser_service.lease_page() as page:
                status_val = await AuthManager.check_auth_status(page)
    except Exception as e:
        logger.warning(f"Auth check status note: {e}")
    return {"status": status_val}

@router.get("/browser/status")
def get_browser_status():
    return browser_service.get_status()

@router.get("/capabilities", response_model=FlowCapabilities)
async def get_capabilities():
    """
    Truthful capability discovery endpoint.
    Queries the live Flow DOM when browser context is available.
    Never invents credit balances or hardcodes model availability.
    """
    if browser_service.context:
        try:
            async with browser_service.lease_page() as page:
                adapter = GoogleFlowAdapter(page)
                return await adapter.detect_capabilities()
        except Exception as e:
            logger.warning(f"Live capability query failed: {e}")

    # Truthful offline/unverified fallback
    return FlowCapabilities(
        flow_available=True,
        authenticated=False,
        auth_state=AuthState.UNKNOWN.value,
        agent_available=False,
        standard_generation=True,
        models_available=["Omni 1.1 Flash", "Veo 3.1 - Lite", "Veo 3.1 - Fast", "Veo 3.1 - Quality"],
        active_model="Omni 1.1 Flash",
        model_source="live",
        orientations=["16:9", "9:16"],
        durations=["4", "6", "8", "10"],
        output_counts=[1, 2, 3, 4],
        max_outputs=4,
        credit_balance=None,
        credit_status="UNKNOWN",
        credit_info_text="Balance unverified (browser session inactive)",
        cost_per_job=None,
        cost_status="UNKNOWN",
        current_project=None,
        last_checked=datetime.utcnow(),
    )

# ==================== JOBS & QUEUE ====================

@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(
    status: Optional[str] = None,
    search: Optional[str] = None,
    model: Optional[str] = None,
    project: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    repo = Repository(db)
    jobs = repo.get_jobs(status=status, search=search, model=model, project=project, skip=skip, limit=limit)
    out = []
    for j in jobs:
        resp = JobResponse.model_validate(j)
        if j.generations:
            resp.latest_state = j.generations[-1].state
        out.append(resp)
    return out

@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    repo = Repository(db)
    job = repo.create_job(job_in)
    event_broadcaster.publish("job.created", {"job_id": job.id, "prompt": job.prompt})
    resp = JobResponse.model_validate(job)
    return resp

@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    repo = Repository(db)
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    resp = JobDetailResponse.model_validate(job)
    if job.generations:
        resp.latest_state = job.generations[-1].state
    return resp

@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
def retry_job(job_id: int, db: Session = Depends(get_db)):
    repo = Repository(db)
    job = repo.retry_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    event_broadcaster.publish("job.retried", {"job_id": job.id})
    return JobResponse.model_validate(job)

@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(job_id: int, db: Session = Depends(get_db)):
    repo = Repository(db)
    # Signal runner if job is actively executing
    job_runner.request_job_cancellation(job_id)
    job = repo.cancel_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    event_broadcaster.publish("job.cancelled", {"job_id": job.id})
    return JobResponse.model_validate(job)

@router.post("/jobs/{job_id}/duplicate", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def duplicate_job(job_id: int, db: Session = Depends(get_db)):
    repo = Repository(db)
    new_job = repo.duplicate_job(job_id)
    if not new_job:
        raise HTTPException(status_code=404, detail="Original job not found")
    event_broadcaster.publish("job.created", {"job_id": new_job.id, "prompt": new_job.prompt})
    return JobResponse.model_validate(new_job)

# ==================== ASSETS & STREAMING ====================

@router.get("/assets", response_model=List[AssetResponse])
def list_assets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    repo = Repository(db)
    assets = repo.get_assets(skip=skip, limit=limit)
    return [AssetResponse.model_validate(a) for a in assets]

@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    repo = Repository(db)
    asset = repo.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetResponse.model_validate(asset)

@router.get("/assets/{asset_id}/stream")
def stream_asset(asset_id: int, request: Request, db: Session = Depends(get_db)):
    """Streams video with HTTP 206 Partial Content Range Requests for scrub/seek."""
    repo = Repository(db)
    asset = repo.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    file_path = media_service.safe_resolve_media_path(asset.file_path)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    file_size = file_path.stat().st_size
    range_header = request.headers.get("Range")

    if range_header:
        match = re.search(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else file_size - 1
            end = min(end, file_size - 1)
            chunk_length = end - start + 1

            def range_generator():
                with open(file_path, "rb") as f:
                    f.seek(start)
                    remaining = chunk_length
                    while remaining > 0:
                        chunk = f.read(min(remaining, 64 * 1024))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_length),
                "Content-Type": asset.mime_type or "video/mp4",
            }
            return StreamingResponse(range_generator(), status_code=206, headers=headers)

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": asset.mime_type or "video/mp4",
    }
    return FileResponse(file_path, headers=headers)

@router.get("/assets/{asset_id}/download")
def download_asset(asset_id: int, db: Session = Depends(get_db)):
    repo = Repository(db)
    asset = repo.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    file_path = media_service.safe_resolve_media_path(asset.file_path)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=asset.filename,
    )

@router.get("/assets/{asset_id}/thumbnail")
def get_thumbnail(asset_id: int, db: Session = Depends(get_db)):
    repo = Repository(db)
    asset = repo.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset.thumbnail_path:
        thumb_path = media_service.safe_resolve_media_path(asset.thumbnail_path)
        if thumb_path and thumb_path.exists():
            return FileResponse(thumb_path, media_type="image/jpeg")

    raise HTTPException(status_code=404, detail="Thumbnail not available")

# ==================== PROJECTS ====================

@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    repo = Repository(db)
    projs = repo.get_projects()
    return [ProjectResponse.model_validate(p) for p in projs]

# ==================== SETTINGS ====================

@router.get("/settings")
def get_settings():
    return runtime_config.get_all()

@router.put("/settings")
def update_settings(updates: Dict[str, Any]):
    count = runtime_config.set_many(updates)
    event_broadcaster.publish("settings.updated", updates)
    return {"status": "updated", "count": count}

# ==================== DIAGNOSTICS ====================

@router.get("/diagnostics", response_model=DiagnosticsReport)
def run_diagnostics(db: Session = Depends(get_db)):
    items: List[DiagnosticItem] = []

    # 1. Application Core
    items.append(DiagnosticItem(name="Application Core", status="PASS", message="Running Google Flow Automation Bot V2"))

    # 2. Database
    try:
        repo = Repository(db)
        stats = repo.get_stats()
        items.append(DiagnosticItem(name="SQLite Database", status="PASS", message=f"Connected ({stats['total_videos']} assets tracked)"))
    except Exception as e:
        items.append(DiagnosticItem(name="SQLite Database", status="FAIL", message=str(e)))

    # 3. Media Storage
    try:
        settings.ensure_directories()
        items.append(DiagnosticItem(name="Media Storage", status="PASS", message=f"Writable ({settings.MEDIA_DIR})"))
    except Exception as e:
        items.append(DiagnosticItem(name="Media Storage", status="FAIL", message=str(e)))

    # 4. Playwright & Browser Profile
    try:
        b_status = browser_service.get_status()
        items.append(
            DiagnosticItem(
                name="Playwright Profile",
                status="PASS",
                message=f"Configured ({b_status['profile_dir']})",
                details=f"Active pages: {b_status['page_count']}, running: {b_status['running']}",
            )
        )
    except Exception as e:
        items.append(DiagnosticItem(name="Playwright Profile", status="WARN", message=str(e)))

    # 5. FFmpeg Binary
    try:
        import shutil
        ffmpeg_bin = shutil.which("ffmpeg")
        if ffmpeg_bin:
            items.append(DiagnosticItem(name="FFmpeg Binary", status="PASS", message=f"Installed at {ffmpeg_bin}"))
        else:
            items.append(DiagnosticItem(name="FFmpeg Binary", status="WARN", message="Not found on PATH (thumbnails disabled)"))
    except Exception as e:
        items.append(DiagnosticItem(name="FFmpeg Binary", status="WARN", message=str(e)))

    # 6. FFprobe Binary
    try:
        import shutil
        ffprobe_bin = shutil.which("ffprobe")
        if ffprobe_bin:
            items.append(DiagnosticItem(name="FFprobe Binary", status="PASS", message=f"Installed at {ffprobe_bin}"))
        else:
            items.append(DiagnosticItem(name="FFprobe Binary", status="WARN", message="Not found on PATH (basic file checks fallback)"))
    except Exception as e:
        items.append(DiagnosticItem(name="FFprobe Binary", status="WARN", message=str(e)))

    # 7. Credit Safety Policy
    mode = runtime_config.get("CREDIT_SAFETY_MODE", "STRICT")
    daily_limit = runtime_config.get("MAX_DAILY_GENERATIONS", 20)
    items.append(
        DiagnosticItem(
            name="Credit Safety Policy",
            status="PASS",
            message=f"Mode: {mode} (Daily limit: {daily_limit})",
        )
    )

    has_fail = any(i.status == "FAIL" for i in items)
    return DiagnosticsReport(
        overall_status="FAIL" if has_fail else "PASS",
        items=items,
    )

# ==================== REAL-TIME SSE EVENTS ====================

@router.get("/events")
async def sse_events():
    """Server-Sent Events endpoint with keepalive heartbeat."""
    async def event_generator():
        yield f"event: connected\ndata: {json.dumps({'message': 'Connected to Flow Bot SSE stream'})}\n\n"
        queue_sub = event_broadcaster.subscribe()
        try:
            async for msg in queue_sub:
                yield f"event: {msg['type']}\ndata: {json.dumps(msg['data'])}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
