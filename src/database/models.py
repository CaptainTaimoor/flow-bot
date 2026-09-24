from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class JobDB(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    status = Column(String, default="QUEUED")
    
    model = Column(String, nullable=True)
    orientation = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    outputs = Column(Integer, default=1)
    project = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    error_message = Column(Text, nullable=True)
    output_path = Column(String, nullable=True)
    
    retry_count = Column(Integer, default=0)
    
    generations = relationship("GenerationDB", back_populates="job", cascade="all, delete-orphan")

class GenerationDB(Base):
    __tablename__ = "generations"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    state = Column(String, default="CREATED")
    
    flow_project_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    job = relationship("JobDB", back_populates="generations")
