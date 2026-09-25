import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from src.database.repository import Repository
from src.database.models import JobDB, GenerationDB
from src.models.domain import JobCreate, JobStatus, GenerationState
from src.config.runtime_config import runtime_config

logger = logging.getLogger(__name__)

class JobQueue:
    """Service wrapper for queue operations backed by SQLAlchemy with atomic gating."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = Repository(db)

    def add_job(self, job_data: JobCreate) -> JobDB:
        return self.repo.create_job(job_data)

    def can_pick_next_job(self) -> Tuple[bool, str]:
        """Checks concurrency and daily limits before claiming the next job."""
        concurrency = runtime_config.get("CONCURRENCY", 1)
        active_count = self.repo.count_active_jobs()
        if active_count >= concurrency:
            return False, f"Concurrency limit reached ({active_count}/{concurrency})"

        max_daily = runtime_config.get("MAX_DAILY_GENERATIONS", 20)
        if max_daily and max_daily > 0:
            daily_count = self.repo.get_daily_generation_count()
            if daily_count >= max_daily:
                return False, f"Daily generation limit reached ({daily_count}/{max_daily})"

        return True, "Ready"

    def claim_next_job(self) -> Optional[JobDB]:
        """Atomically claims the next queued job if limits permit."""
        can_pick, _ = self.can_pick_next_job()
        if not can_pick:
            return None

        job = self.repo.get_next_queued_job()
        if job:
            job.status = JobStatus.RUNNING.value
            self.db.commit()
            self.db.refresh(job)
            return job
        return None

    def get_next_job(self) -> Optional[JobDB]:
        return self.repo.get_next_queued_job()

    def get_job(self, job_id: int) -> Optional[JobDB]:
        return self.repo.get_job(job_id)

    def get_all_jobs(self, limit: int = 100) -> List[JobDB]:
        return self.repo.get_jobs(limit=limit)

    def update_job_status(
        self, job_id: int, status: JobStatus, error_message: Optional[str] = None
    ) -> Optional[JobDB]:
        return self.repo.update_job_status(job_id, status, error_message=error_message)

    def add_generation(self, job_id: int, state: GenerationState = GenerationState.CREATED) -> int:
        gen = self.repo.create_generation(job_id, state)
        return gen.id

    def update_generation_state(
        self,
        gen_id: int,
        state: GenerationState,
        flow_project_id: Optional[str] = None,
        flow_asset_id: Optional[str] = None,
        credit_cost: Optional[int] = None,
        submission_confirmed: Optional[bool] = None,
        submission_proof: Optional[dict] = None,
        correlation_confidence: Optional[str] = None,
        correlation_evidence: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> Optional[GenerationDB]:
        return self.repo.update_generation_state(
            gen_id=gen_id,
            state=state,
            flow_project_id=flow_project_id,
            flow_asset_id=flow_asset_id,
            credit_cost=credit_cost,
            submission_confirmed=submission_confirmed,
            submission_proof=submission_proof,
            correlation_confidence=correlation_confidence,
            correlation_evidence=correlation_evidence,
            error_message=error_message,
        )
