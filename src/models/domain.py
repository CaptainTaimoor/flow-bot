from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
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
    CHECKING_CAPABILITIES = "CHECKING_CAPABILITIES"
    PREPARING = "PREPARING"
    SUBMITTING = "SUBMITTING"
    GENERATION_STARTED = "GENERATION_STARTED"
    GENERATING = "GENERATING"
    WAITING_FOR_ASSET = "WAITING_FOR_ASSET"
    LOCATING_ASSET = "LOCATING_ASSET"
    DOWNLOADING = "DOWNLOADING"
    VALIDATING = "VALIDATING"
    THUMBNAIL_GENERATING = "THUMBNAIL_GENERATING"
    READY = "READY"
    SUCCESS = "SUCCESS"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    MANUAL_ACTION_REQUIRED = "MANUAL_ACTION_REQUIRED"
    CANCELLED = "CANCELLED"

class FlowGenerationMode(str, Enum):
    STANDARD = "STANDARD"
    AGENT = "AGENT"

class JobCreate(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    model: Optional[str] = "veo"
    orientation: Optional[str] = "16:9"
    duration: Optional[str] = "5"
    output_count: Optional[int] = 1
    project: Optional[str] = None
    generation_mode: Optional[str] = "STANDARD"

class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    generation_id: Optional[int] = None
    flow_asset_id: Optional[str] = None
    filename: str
    file_path: str
    thumbnail_path: Optional[str] = None
    mime_type: str = "video/mp4"
    file_size: int = 0
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime

class GenerationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    state: str
    flow_project_id: Optional[str] = None
    flow_asset_id: Optional[str] = None
    model: Optional[str] = None
    credit_cost: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: Optional[int] = None
    event_type: str
    payload: Dict[str, Any]
    created_at: datetime

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    status: JobStatus
    model: Optional[str] = None
    orientation: Optional[str] = None
    duration: Optional[str] = None
    output_count: int = 1
    project: Optional[str] = None
    generation_mode: str = "STANDARD"
    retry_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    latest_state: Optional[str] = None
    assets: List[AssetResponse] = []

class JobDetailResponse(JobResponse):
    generations: List[GenerationResponse] = []
    events: List[EventResponse] = []

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    flow_project_id: str
    name: str
    created_at: datetime
    last_used_at: datetime

class FlowCapabilities(BaseModel):
    flow_available: bool = False
    authenticated: bool = False
    agent_available: bool = False
    standard_generation: bool = True
    models_available: List[str] = ["veo", "veo-2"]
    orientations: List[str] = ["16:9", "9:16"]
    durations: List[str] = ["5", "8"]
    max_outputs: int = 4
    credit_balance: Optional[int] = None
    credit_info_text: Optional[str] = None
    current_project: Optional[str] = None
    last_checked: datetime = Field(default_factory=datetime.utcnow)

class DiagnosticItem(BaseModel):
    name: str
    status: str # PASS, WARN, FAIL
    message: str
    details: Optional[str] = None

class DiagnosticsReport(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    overall_status: str
    items: List[DiagnosticItem]
