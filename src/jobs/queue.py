import sqlite3
from src.database.db import get_connection
from src.models.domain import JobCreate, JobStatus, JobDB

class JobQueue:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add_job(self, job_data: JobCreate) -> JobDB:
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO jobs (prompt, model, orientation, duration, outputs, project, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (job_data.prompt, job_data.model, job_data.orientation, job_data.duration, 
             job_data.outputs, job_data.project, JobStatus.QUEUED.value)
        )
        job_id = cursor.lastrowid
        self.conn.commit()
        return self.get_job(job_id)

    def get_next_job(self) -> JobDB | None:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE status = ? LIMIT 1", (JobStatus.QUEUED.value,))
        row = cursor.fetchone()
        return self._row_to_job(row) if row else None
        
    def update_job_status(self, job_id: int, status: JobStatus, error_message: str = None, output_path: str = None) -> JobDB:
        cursor = self.conn.cursor()
        cursor.execute("UPDATE jobs SET status = ?, error_message = ?, output_path = ? WHERE id = ?",
                       (status.value, error_message, output_path, job_id))
        self.conn.commit()
        return self.get_job(job_id)

    def get_job(self, job_id: int) -> JobDB | None:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        return self._row_to_job(row) if row else None
        
    def get_all_jobs(self, limit: int = 100) -> list[JobDB]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [self._row_to_job(row) for row in rows]

    def add_generation(self, job_id: int, state: str):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO generations (job_id, state) VALUES (?, ?)", (job_id, state))
        self.conn.commit()
        return cursor.lastrowid

    def update_generation_state(self, gen_id: int, state: str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE generations SET state = ? WHERE id = ?", (state, gen_id))
        self.conn.commit()

    def _row_to_job(self, row) -> JobDB:
        return JobDB(
            id=row[0], prompt=row[1], status=row[2], model=row[3], orientation=row[4],
            duration=row[5], outputs=row[6], project=row[7], created_at=row[8],
            error_message=row[9], output_path=row[10], retry_count=row[11]
        )
