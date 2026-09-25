import os
import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.config.settings import settings
from src.database.models import Base

logger = logging.getLogger(__name__)

# Engine configuration with check_same_thread=False for SQLite
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

def _migrate_columns():
    """Ensures newly added columns are safely added to existing SQLite database tables."""
    try:
        with engine.connect() as conn:
            # Check jobs table
            res = conn.execute(text("PRAGMA table_info(jobs)")).fetchall()
            existing_job_cols = {row[1] for row in res}
            
            job_col_defs = {
                "requested_model": "VARCHAR(64)",
                "effective_model": "VARCHAR(64)",
                "requested_orientation": "VARCHAR(32)",
                "effective_orientation": "VARCHAR(32)",
                "requested_duration": "VARCHAR(32)",
                "effective_duration": "VARCHAR(32)",
                "requested_output_count": "INTEGER DEFAULT 1",
                "effective_output_count": "INTEGER DEFAULT 1",
                "submission_confirmed": "BOOLEAN",
                "credit_status": "VARCHAR(32) DEFAULT 'UNKNOWN'",
                "verified_credit_cost": "INTEGER",
            }
            for col, col_type in job_col_defs.items():
                if col not in existing_job_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col} {col_type}"))
                        conn.commit()
                        logger.info(f"Added missing column '{col}' to 'jobs' table.")
                    except Exception as e:
                        logger.debug(f"Column migration notice (jobs.{col}): {e}")

            # Check generations table
            res_gen = conn.execute(text("PRAGMA table_info(generations)")).fetchall()
            existing_gen_cols = {row[1] for row in res_gen}
            gen_col_defs = {
                "submission_confirmed": "BOOLEAN",
                "submission_proof": "JSON",
                "correlation_confidence": "VARCHAR(32)",
                "correlation_evidence": "JSON",
            }
            for col, col_type in gen_col_defs.items():
                if col not in existing_gen_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE generations ADD COLUMN {col} {col_type}"))
                        conn.commit()
                        logger.info(f"Added missing column '{col}' to 'generations' table.")
                    except Exception as e:
                        logger.debug(f"Column migration notice (generations.{col}): {e}")

            # Check assets table
            res_asset = conn.execute(text("PRAGMA table_info(assets)")).fetchall()
            existing_asset_cols = {row[1] for row in res_asset}
            asset_col_defs = {
                "video_codec": "VARCHAR(32)",
                "audio_codec": "VARCHAR(32)",
                "fps": "FLOAT",
                "correlation_confidence": "VARCHAR(32)",
                "correlation_evidence": "JSON",
                "ffprobe_metadata": "JSON",
            }
            for col, col_type in asset_col_defs.items():
                if col not in existing_asset_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE assets ADD COLUMN {col} {col_type}"))
                        conn.commit()
                        logger.info(f"Added missing column '{col}' to 'assets' table.")
                    except Exception as e:
                        logger.debug(f"Column migration notice (assets.{col}): {e}")

    except Exception as e:
        logger.warning(f"Database migration check completed with notice: {e}")

def init_db():
    """Initializes the database schema, runs auto-migration, and verifies directories."""
    settings.ensure_directories()
    Base.metadata.create_all(bind=engine)
    _migrate_columns()

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for background workers and CLI tasks."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
