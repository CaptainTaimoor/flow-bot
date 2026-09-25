from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import re

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
    DISCOVERING_CAPABILITIES = "DISCOVERING_CAPABILITIES"
    CHECKING_CREDIT_POLICY = "CHECKING_CREDIT_POLICY"
    PREPARING = "PREPARING"
    SUBMITTING = "SUBMITTING"
    SUBMISSION_CONFIRMED = "SUBMISSION_CONFIRMED"
    SUBMISSION_UNKNOWN = "SUBMISSION_UNKNOWN"
    GENERATION_STARTED = "GENERATION_STARTED"
    GENERATING = "GENERATING"
    WAITING_FOR_ASSET = "WAITING_FOR_ASSET"
    ASSET_IDENTIFICATION = "ASSET_IDENTIFICATION"
    LOCATING_ASSET = "LOCATING_ASSET"
    DOWNLOADING = "DOWNLOADING"
    VALIDATING = "VALIDATING"
    THUMBNAIL_GENERATING = "THUMBNAIL_GENERATING"
    READY = "READY"
    SUCCESS = "SUCCESS"
    COMPLETED = "COMPLETED"
    RETRY_RECONCILIATION_REQUIRED = "RETRY_RECONCILIATION_REQUIRED"
    RETRYING = "RETRYING"
    CANCELLATION_UNCONFIRMED = "CANCELLATION_UNCONFIRMED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    MANUAL_ACTION_REQUIRED = "MANUAL_ACTION_REQUIRED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class FlowGenerationMode(str, Enum):
    STANDARD = "STANDARD"
    AGENT = "AGENT"

class CreditSafetyMode(str, Enum):
    STRICT = "STRICT"
    WARN = "WARN"
    ALLOW_UNKNOWN = "ALLOW_UNKNOWN"

class CorrelationConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    FAILED = "FAILED"

class AuthState(str, Enum):
    AUTHENTICATED = "AUTHENTICATED"
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    SECURITY_VERIFICATION_REQUIRED = "SECURITY_VERIFICATION_REQUIRED"
    UNKNOWN = "UNKNOWN"

def normalize_model_name(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    val = val.strip()
    return val

def normalize_aspect_ratio(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    cleaned = val.strip().lower().replace(" ", "")
    mapping = {
        "16:9": "16:9",
        "landscape": "16:9",
        "horizontal": "16:9",
        "9:16": "9:16",
        "portrait": "9:16",
        "vertical": "9:16",
        "1:1": "1:1",
        "square": "1:1",
        "4:3": "4:3",
        "3:4": "3:4",
    }
    return mapping.get(cleaned, val.strip())

def normalize_duration(val: Optional[Union[str, int]]) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip().lower().rstrip("s")
    return s

class JobCreate(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    model: Optional[str] = None
    orientation: Optional[str] = "16:9"
    duration: Optional[str] = "5"
    output_count: Optional[int] = 1
    project: Optional[str] = None
    generation_mode: Optional[str] = "STANDARD"
    allow_unverified_credits: Optional[bool] = False

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
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    fps: Optional[float] = None
    correlation_confidence: Optional[str] = None
    correlation_evidence: Optional[Dict[str, Any]] = None
    ffprobe_metadata: Optional[Dict[str, Any]] = None
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
    submission_confirmed: Optional[bool] = None
    submission_proof: Optional[Dict[str, Any]] = None
    correlation_confidence: Optional[str] = None
    correlation_evidence: Optional[Dict[str, Any]] = None
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
    requested_model: Optional[str] = None
    effective_model: Optional[str] = None
    orientation: Optional[str] = None
    requested_orientation: Optional[str] = None
    effective_orientation: Optional[str] = None
    duration: Optional[str] = None
    requested_duration: Optional[str] = None
    effective_duration: Optional[str] = None
    output_count: int = 1
    requested_output_count: Optional[int] = 1
    effective_output_count: Optional[int] = 1
    project: Optional[str] = None
    generation_mode: str = "STANDARD"
    submission_confirmed: Optional[bool] = None
    credit_status: Optional[str] = "UNKNOWN"
    verified_credit_cost: Optional[int] = None
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
    auth_state: str = AuthState.UNKNOWN.value
    agent_available: bool = False
    standard_generation: bool = True
    models_available: List[str] = []
    active_model: Optional[str] = None
    model_source: str = "unknown" # "live", "fallback", "unknown"
    orientations: List[str] = []
    durations: List[str] = []
    output_counts: List[int] = [1]
    max_outputs: int = 1
    credit_balance: Optional[int] = None
    credit_status: str = "UNKNOWN" # "VERIFIED", "UNKNOWN", "UNAVAILABLE"
    credit_info_text: Optional[str] = None
    cost_per_job: Optional[int] = None
    cost_status: str = "UNKNOWN" # "VERIFIED", "UNKNOWN"
    current_project: Optional[str] = None
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    discovery_evidence: Optional[Dict[str, Any]] = None

class CreditPolicyConfig(BaseModel):
    mode: CreditSafetyMode = CreditSafetyMode.STRICT
    max_daily_credits: Optional[int] = None
    max_session_credits: Optional[int] = None
    max_job_cost: Optional[int] = None
    block_on_unverified_balance: bool = True
    block_on_unverified_cost: bool = True

class DiagnosticItem(BaseModel):
    name: str
    status: str # PASS, WARN, FAIL
    message: str
    details: Optional[str] = None

class DiagnosticsReport(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    overall_status: str
    items: List[DiagnosticItem]
