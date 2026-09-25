from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class JobDB(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    status = Column(String(32), default="QUEUED", index=True)

    # Requested vs Effective configuration
    model = Column(String(64), nullable=True)
    requested_model = Column(String(64), nullable=True)
    effective_model = Column(String(64), nullable=True)

    orientation = Column(String(32), nullable=True)
    requested_orientation = Column(String(32), nullable=True)
    effective_orientation = Column(String(32), nullable=True)

    duration = Column(String(32), nullable=True)
    requested_duration = Column(String(32), nullable=True)
    effective_duration = Column(String(32), nullable=True)

    output_count = Column(Integer, default=1)
    requested_output_count = Column(Integer, default=1)
    effective_output_count = Column(Integer, default=1)

    project = Column(String(128), nullable=True)
    generation_mode = Column(String(32), default="STANDARD")

    # Audit & Truthfulness
    submission_confirmed = Column(Boolean, nullable=True)
    credit_status = Column(String(32), default="UNKNOWN")
    verified_credit_cost = Column(Integer, nullable=True)

    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    generations = relationship(
        "GenerationDB", back_populates="job", cascade="all, delete-orphan", order_by="GenerationDB.id"
    )
    assets = relationship(
        "AssetDB", back_populates="job", cascade="all, delete-orphan", order_by="AssetDB.id"
    )
    events = relationship(
        "EventDB", back_populates="job", cascade="all, delete-orphan", order_by="EventDB.id"
    )

class GenerationDB(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    state = Column(String(64), default="CREATED", index=True)

    flow_project_id = Column(String(128), nullable=True)
    flow_asset_id = Column(String(128), nullable=True)
    model = Column(String(64), nullable=True)
    credit_cost = Column(Integer, nullable=True)

    # Submission & Correlation audit
    submission_confirmed = Column(Boolean, nullable=True)
    submission_proof = Column(JSON, nullable=True)
    correlation_confidence = Column(String(32), nullable=True)
    correlation_evidence = Column(JSON, nullable=True)

    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    job = relationship("JobDB", back_populates="generations")
    assets = relationship("AssetDB", back_populates="generation")

class AssetDB(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    generation_id = Column(Integer, ForeignKey("generations.id"), nullable=True, index=True)

    flow_asset_id = Column(String(128), nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    thumbnail_path = Column(String(512), nullable=True)

    mime_type = Column(String(64), default="video/mp4")
    file_size = Column(Integer, default=0)
    duration = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    video_codec = Column(String(32), nullable=True)
    audio_codec = Column(String(32), nullable=True)
    fps = Column(Float, nullable=True)

    correlation_confidence = Column(String(32), nullable=True)
    correlation_evidence = Column(JSON, nullable=True)
    ffprobe_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    job = relationship("JobDB", back_populates="assets")
    generation = relationship("GenerationDB", back_populates="assets")

class ProjectDB(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    flow_project_id = Column(String(128), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EventDB(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    job = relationship("JobDB", back_populates="events")

class SettingDB(Base):
    __tablename__ = "settings"

    key = Column(String(128), primary_key=True, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
