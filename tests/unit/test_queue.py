import pytest
import sqlite3
import os
from src.jobs.queue import JobQueue
from src.models.domain import JobCreate, JobStatus
from src.database.db import get_connection

@pytest.fixture
def db_conn(monkeypatch):
    # Use memory database for testing by mocking the property
    import src.config.settings
    monkeypatch.setattr(src.config.settings.Settings, "database_path", ":memory:")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            status TEXT DEFAULT 'QUEUED',
            model TEXT,
            orientation TEXT,
            duration TEXT,
            outputs INTEGER DEFAULT 1,
            project TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT,
            output_path TEXT,
            retry_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    yield conn
    conn.close()

def test_add_job(db_conn):
    queue = JobQueue(db_conn)
    job = queue.add_job(JobCreate(prompt="Test prompt"))
    assert job.id is not None
    assert job.status == JobStatus.QUEUED.value
    assert job.prompt == "Test prompt"

def test_get_next_job(db_conn):
    queue = JobQueue(db_conn)
    queue.add_job(JobCreate(prompt="Job 1"))
    queue.add_job(JobCreate(prompt="Job 2"))
    
    next_job = queue.get_next_job()
    assert next_job is not None
    assert next_job.prompt == "Job 1"
    
def test_update_status(db_conn):
    queue = JobQueue(db_conn)
    job = queue.add_job(JobCreate(prompt="Job 1"))
    
    updated = queue.update_job_status(job.id, JobStatus.RUNNING)
    assert updated.status == JobStatus.RUNNING.value
