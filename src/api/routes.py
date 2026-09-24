from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from src.database.db import get_db
from src.jobs.queue import JobQueue
from src.models.domain import JobCreate, JobResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")

@router.post("/jobs", response_model=JobResponse)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating job with prompt: {job_in.prompt}")
    queue = JobQueue(db)
    job = queue.add_job(job_in)
    return JobResponse(
        id=job.id,
        prompt=job.prompt,
        status=job.status,
        created_at=job.created_at,
        error_message=job.error_message,
        output_path=job.output_path
    )

@router.get("/jobs", response_model=list[JobResponse])
def list_jobs(limit: int = 100, db: Session = Depends(get_db)):
    queue = JobQueue(db)
    jobs = queue.get_all_jobs(limit)
    return [
        JobResponse(
            id=job.id,
            prompt=job.prompt,
            status=job.status,
            created_at=job.created_at,
            error_message=job.error_message,
            output_path=job.output_path
        ) for job in jobs
    ]

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    queue = JobQueue(db)
    job = queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(
        id=job.id,
        prompt=job.prompt,
        status=job.status,
        created_at=job.created_at,
        error_message=job.error_message,
        output_path=job.output_path
    )

@router.get("/health")
def health_check():
    return {"status": "ok"}
