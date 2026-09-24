import sqlite3
import os
from src.config.settings import settings

def init_db():
    os.makedirs(os.path.dirname(settings.database_path), exist_ok=True)
    conn = sqlite3.connect(settings.database_path)
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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            state TEXT DEFAULT 'CREATED',
            flow_project_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
    """)
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(settings.database_path)
