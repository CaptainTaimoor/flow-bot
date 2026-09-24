import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base
from src.jobs.queue import JobQueue
from src.models.domain import JobCreate, JobStatus

@pytest.fixture
def db_session():
    # In-memory SQLite engine for fast, isolated unit tests
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_add_job(db_session):
    queue = JobQueue(db_session)
    job = queue.add_job(JobCreate(prompt="Test prompt"))
    assert job.id is not None
    assert job.status == JobStatus.QUEUED.value
    assert job.prompt == "Test prompt"

def test_get_next_job(db_session):
    queue = JobQueue(db_session)
    queue.add_job(JobCreate(prompt="Job 1"))
    queue.add_job(JobCreate(prompt="Job 2"))

    next_job = queue.get_next_job()
    assert next_job is not None
    assert next_job.prompt == "Job 1"

def test_update_status(db_session):
    queue = JobQueue(db_session)
    job = queue.add_job(JobCreate(prompt="Job 1"))

    updated = queue.update_job_status(job.id, JobStatus.RUNNING)
    assert updated.status == JobStatus.RUNNING.value
