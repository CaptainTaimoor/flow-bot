from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.database.models import JobDB, GenerationDB, AssetDB, ProjectDB, EventDB, SettingDB
from src.models.domain import JobCreate, JobStatus, GenerationState

class Repository:
    def __init__(self, db: Session):
        self.db = db

    # ==================== JOBS ====================

    def create_job(self, job_data: JobCreate) -> JobDB:
        job = JobDB(
            prompt=job_data.prompt,
            status=JobStatus.QUEUED.value,
            model=job_data.model,
            orientation=job_data.orientation,
            duration=job_data.duration,
            output_count=job_data.output_count or 1,
            project=job_data.project,
            generation_mode=job_data.generation_mode or "STANDARD",
            created_at=datetime.utcnow(),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        self.record_event(job.id, "job.created", {"status": job.status, "prompt": job.prompt})
        return job

    def get_job(self, job_id: int) -> Optional[JobDB]:
        return self.db.query(JobDB).filter(JobDB.id == job_id).first()

    def get_jobs(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        model: Optional[str] = None,
        project: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[JobDB]:
        q = self.db.query(JobDB)
        if status:
            q = q.filter(JobDB.status == status)
        if model:
            q = q.filter(JobDB.model == model)
        if project:
            q = q.filter(JobDB.project == project)
        if search:
            q = q.filter(JobDB.prompt.ilike(f"%{search}%"))
        return q.order_by(desc(JobDB.created_at)).offset(skip).limit(limit).all()

    def get_next_queued_job(self) -> Optional[JobDB]:
        return (
            self.db.query(JobDB)
            .filter(JobDB.status == JobStatus.QUEUED.value)
            .order_by(JobDB.created_at.asc())
            .first()
        )

    def count_active_jobs(self) -> int:
        return self.db.query(JobDB).filter(JobDB.status == JobStatus.RUNNING.value).count()

    def update_job_status(
        self,
        job_id: int,
        status: JobStatus,
        error_message: Optional[str] = None,
    ) -> Optional[JobDB]:
        job = self.get_job(job_id)
        if not job:
            return None

        job.status = status.value
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.utcnow()
        elif status in (JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED):
            job.completed_at = datetime.utcnow()

        if error_message is not None:
            job.error_message = error_message

        self.db.commit()
        self.db.refresh(job)
        self.record_event(job_id, "job.status_changed", {"status": job.status, "error": error_message})
        return job

    def retry_job(self, job_id: int) -> Optional[JobDB]:
        job = self.get_job(job_id)
        if not job:
            return None
        job.status = JobStatus.QUEUED.value
        job.retry_count += 1
        job.error_message = None
        job.started_at = None
        job.completed_at = None
        self.db.commit()
        self.db.refresh(job)
        self.record_event(job_id, "job.retried", {"retry_count": job.retry_count})
        return job

    def cancel_job(self, job_id: int) -> Optional[JobDB]:
        job = self.get_job(job_id)
        if not job:
            return None
        job.status = JobStatus.CANCELLED.value
        job.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        self.record_event(job_id, "job.cancelled", {})
        return job

    def duplicate_job(self, job_id: int) -> Optional[JobDB]:
        orig = self.get_job(job_id)
        if not orig:
            return None
        new_job = JobCreate(
            prompt=orig.prompt,
            model=orig.model,
            orientation=orig.orientation,
            duration=orig.duration,
            output_count=orig.output_count,
            project=orig.project,
            generation_mode=orig.generation_mode,
        )
        return self.create_job(new_job)

    # ==================== GENERATIONS ====================

    def create_generation(self, job_id: int, state: GenerationState = GenerationState.CREATED) -> GenerationDB:
        gen = GenerationDB(
            job_id=job_id,
            state=state.value,
            started_at=datetime.utcnow(),
        )
        self.db.add(gen)
        self.db.commit()
        self.db.refresh(gen)
        self.record_event(job_id, "generation.created", {"generation_id": gen.id, "state": gen.state})
        return gen

    def update_generation_state(
        self,
        gen_id: int,
        state: GenerationState,
        flow_project_id: Optional[str] = None,
        flow_asset_id: Optional[str] = None,
        credit_cost: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[GenerationDB]:
        gen = self.db.query(GenerationDB).filter(GenerationDB.id == gen_id).first()
        if not gen:
            return None

        gen.state = state.value
        if flow_project_id:
            gen.flow_project_id = flow_project_id
        if flow_asset_id:
            gen.flow_asset_id = flow_asset_id
        if credit_cost is not None:
            gen.credit_cost = credit_cost
        if error_message:
            gen.error_message = error_message
        if state in (GenerationState.SUCCESS, GenerationState.FAILED, GenerationState.CANCELLED):
            gen.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(gen)
        self.record_event(gen.job_id, "generation.state_changed", {
            "generation_id": gen.id,
            "state": gen.state,
            "flow_asset_id": flow_asset_id,
            "error": error_message,
        })
        return gen

    # ==================== ASSETS ====================

    def create_asset(
        self,
        job_id: int,
        generation_id: Optional[int],
        filename: str,
        file_path: str,
        thumbnail_path: Optional[str] = None,
        flow_asset_id: Optional[str] = None,
        mime_type: str = "video/mp4",
        file_size: int = 0,
        duration: Optional[float] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> AssetDB:
        asset = AssetDB(
            job_id=job_id,
            generation_id=generation_id,
            filename=filename,
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            flow_asset_id=flow_asset_id,
            mime_type=mime_type,
            file_size=file_size,
            duration=duration,
            width=width,
            height=height,
            created_at=datetime.utcnow(),
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        self.record_event(job_id, "asset.created", {"asset_id": asset.id, "filename": filename})
        return asset

    def get_asset(self, asset_id: int) -> Optional[AssetDB]:
        return self.db.query(AssetDB).filter(AssetDB.id == asset_id).first()

    def get_assets(self, skip: int = 0, limit: int = 100) -> List[AssetDB]:
        return self.db.query(AssetDB).order_by(desc(AssetDB.created_at)).offset(skip).limit(limit).all()

    def delete_asset(self, asset_id: int) -> bool:
        asset = self.get_asset(asset_id)
        if not asset:
            return False
        self.db.delete(asset)
        self.db.commit()
        return True

    # ==================== PROJECTS ====================

    def record_project(self, flow_project_id: str, name: str) -> ProjectDB:
        proj = self.db.query(ProjectDB).filter(ProjectDB.flow_project_id == flow_project_id).first()
        if proj:
            proj.name = name
            proj.last_used_at = datetime.utcnow()
        else:
            proj = ProjectDB(
                flow_project_id=flow_project_id,
                name=name,
                created_at=datetime.utcnow(),
                last_used_at=datetime.utcnow(),
            )
            self.db.add(proj)
        self.db.commit()
        self.db.refresh(proj)
        return proj

    def get_projects(self) -> List[ProjectDB]:
        return self.db.query(ProjectDB).order_by(desc(ProjectDB.last_used_at)).all()

    # ==================== EVENTS ====================

    def record_event(self, job_id: Optional[int], event_type: str, payload: Dict[str, Any]) -> EventDB:
        event = EventDB(
            job_id=job_id,
            event_type=event_type,
            payload=payload,
            created_at=datetime.utcnow(),
        )
        self.db.add(event)
        self.db.commit()
        return event

    def get_events(self, job_id: Optional[int] = None, limit: int = 100) -> List[EventDB]:
        q = self.db.query(EventDB)
        if job_id:
            q = q.filter(EventDB.job_id == job_id)
        return q.order_by(desc(EventDB.created_at)).limit(limit).all()

    # ==================== STATS ====================

    def get_stats(self) -> Dict[str, int]:
        today_start = datetime.combine(date.today(), datetime.min.time())
        active = self.db.query(JobDB).filter(JobDB.status == JobStatus.RUNNING.value).count()
        queued = self.db.query(JobDB).filter(JobDB.status == JobStatus.QUEUED.value).count()
        completed_today = (
            self.db.query(JobDB)
            .filter(JobDB.status == JobStatus.SUCCESS.value, JobDB.completed_at >= today_start)
            .count()
        )
        failed_today = (
            self.db.query(JobDB)
            .filter(JobDB.status == JobStatus.FAILED.value, JobDB.completed_at >= today_start)
            .count()
        )
        total_videos = self.db.query(AssetDB).count()
        return {
            "active": active,
            "queued": queued,
            "completed_today": completed_today,
            "failed_today": failed_today,
            "total_videos": total_videos,
        }

    # ==================== SETTINGS ====================

    def get_settings(self) -> Dict[str, str]:
        rows = self.db.query(SettingDB).all()
        return {r.key: r.value for r in rows}

    def set_setting(self, key: str, value: str):
        row = self.db.query(SettingDB).filter(SettingDB.key == key).first()
        if row:
            row.value = value
            row.updated_at = datetime.utcnow()
        else:
            row = SettingDB(key=key, value=value, updated_at=datetime.utcnow())
            self.db.add(row)
        self.db.commit()
