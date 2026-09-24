from typing import Optional, List
from sqlalchemy.orm import Session
from src.database.repository import Repository
from src.database.models import JobDB, GenerationDB
from src.models.domain import JobCreate, JobStatus, GenerationState

class JobQueue:
    """Service wrapper for queue operations backed by SQLAlchemy."""

    def __init__(self, db: Session):
        self.repo = Repository(db)

    def add_job(self, job_data: JobCreate) -> JobDB:
        return self.repo.create_job(job_data)

    def get_next_job(self) -> Optional[JobDB]:
        return self.repo.get_next_queued_job()

    def update_job_status(
        self, job_id: int, status: JobStatus, error_message: Optional[str] = None
    ) -> Optional[JobDB]:
        return self.repo.update_job_status(job_id, status, error_message=error_message)

    def get_job(self, job_id: int) -> Optional[JobDB]:
        return self.repo.get_job(job_id)

    def get_all_jobs(self, limit: int = 100) -> List[JobDB]:
        return self.repo.get_jobs(limit=limit)

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
        error_message: Optional[str] = None,
    ) -> Optional[GenerationDB]:
        return self.repo.update_generation_state(
            gen_id, state, flow_project_id, flow_asset_id, credit_cost, error_message
        )
