from enum import Enum
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRY_PENDING = "RETRY_PENDING"
    CANCELLED = "CANCELLED"

class GenerationState(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    OPENING_BROWSER = "OPENING_BROWSER"
    CHECKING_AUTH = "CHECKING_AUTH"
    OPENING_FLOW = "OPENING_FLOW"
    OPENING_PROJECT = "OPENING_PROJECT"
    PREPARING_PROMPT = "PREPARING_PROMPT"
    SUBMITTING = "SUBMITTING"
    GENERATION_STARTED = "GENERATION_STARTED"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    LOCATING_ASSET = "LOCATING_ASSET"
    DOWNLOADING = "DOWNLOADING"
    VERIFYING_FILE = "VERIFYING_FILE"
    SUCCESS = "SUCCESS"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    MANUAL_ACTION_REQUIRED = "MANUAL_ACTION_REQUIRED"
    CANCELLED = "CANCELLED"

@dataclass
class JobCreate:
    prompt: str
    model: Optional[str] = None
    orientation: Optional[str] = None
    duration: Optional[str] = None
    outputs: Optional[int] = None
    project: Optional[str] = None
    download: bool = True

@dataclass
class JobDB:
    id: int
    prompt: str
    status: str
    created_at: str
    model: Optional[str] = None
    orientation: Optional[str] = None
    duration: Optional[str] = None
    outputs: int = 1
    project: Optional[str] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    retry_count: int = 0
