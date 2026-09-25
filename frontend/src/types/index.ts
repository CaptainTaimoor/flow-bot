export type JobStatus = 'QUEUED' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'RETRY_PENDING' | 'CANCELLED';

export type GenerationState =
  | 'CREATED'
  | 'QUEUED'
  | 'OPENING_BROWSER'
  | 'CHECKING_AUTH'
  | 'OPENING_FLOW'
  | 'OPENING_PROJECT'
  | 'DISCOVERING_CAPABILITIES'
  | 'CHECKING_CREDIT_POLICY'
  | 'PREPARING'
  | 'SUBMITTING'
  | 'SUBMISSION_CONFIRMED'
  | 'SUBMISSION_UNKNOWN'
  | 'GENERATION_STARTED'
  | 'GENERATING'
  | 'WAITING_FOR_ASSET'
  | 'ASSET_IDENTIFICATION'
  | 'LOCATING_ASSET'
  | 'DOWNLOADING'
  | 'VALIDATING'
  | 'THUMBNAIL_GENERATING'
  | 'READY'
  | 'SUCCESS'
  | 'COMPLETED'
  | 'RETRY_RECONCILIATION_REQUIRED'
  | 'RETRYING'
  | 'CANCELLATION_UNCONFIRMED'
  | 'AUTH_REQUIRED'
  | 'MANUAL_ACTION_REQUIRED'
  | 'FAILED'
  | 'CANCELLED';

export type CorrelationConfidence = 'HIGH' | 'MEDIUM' | 'LOW' | 'FAILED';
export type CreditSafetyMode = 'STRICT' | 'WARN' | 'ALLOW_UNKNOWN';

export interface Asset {
  id: number;
  job_id: number;
  generation_id?: number;
  flow_asset_id?: string;
  filename: string;
  file_path: string;
  thumbnail_path?: string;
  mime_type: string;
  file_size: number;
  duration?: number;
  width?: number;
  height?: number;
  video_codec?: string;
  audio_codec?: string;
  fps?: number;
  correlation_confidence?: CorrelationConfidence;
  correlation_evidence?: Record<string, any>;
  ffprobe_metadata?: Record<string, any>;
  created_at: string;
}

export interface Generation {
  id: number;
  job_id: number;
  state: GenerationState;
  flow_project_id?: string;
  flow_asset_id?: string;
  model?: string;
  credit_cost?: number;
  submission_confirmed?: boolean;
  submission_proof?: Record<string, any>;
  correlation_confidence?: CorrelationConfidence;
  correlation_evidence?: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface Job {
  id: number;
  prompt: string;
  status: JobStatus;
  model?: string;
  requested_model?: string;
  effective_model?: string;
  orientation?: string;
  requested_orientation?: string;
  effective_orientation?: string;
  duration?: string;
  requested_duration?: string;
  effective_duration?: string;
  output_count: number;
  requested_output_count?: number;
  effective_output_count?: number;
  project?: string;
  generation_mode: string;
  submission_confirmed?: boolean;
  credit_status?: string;
  verified_credit_cost?: number;
  retry_count: number;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  latest_state?: GenerationState;
  assets?: Asset[];
  generations?: Generation[];
}

export interface FlowCapabilities {
  flow_available: boolean;
  authenticated: boolean;
  auth_state?: string;
  agent_available: boolean;
  standard_generation: boolean;
  models_available: string[];
  active_model?: string;
  model_source?: string;
  orientations: string[];
  durations: string[];
  output_counts?: number[];
  max_outputs: number;
  credit_balance?: number;
  credit_status?: string;
  credit_info_text?: string;
  cost_per_job?: number;
  cost_status?: string;
  current_project?: string;
  last_checked?: string;
}

export interface SystemStatus {
  status: string;
  app_env: string;
  headless: boolean;
  credit_safety_mode?: CreditSafetyMode;
  browser?: {
    running: boolean;
    headless: boolean;
    page_count: number;
    profile_dir: string;
  };
  stats: {
    active: number;
    queued: number;
    completed_today: number;
    failed_today: number;
    total_videos: number;
  };
  network?: {
    local: string;
    network: string[];
    tailscale: string[];
    hostname?: string;
  };
}

export interface DiagnosticItem {
  name: string;
  status: 'PASS' | 'WARN' | 'FAIL';
  message: string;
  details?: string;
}

export interface DiagnosticsReport {
  timestamp: string;
  overall_status: 'PASS' | 'WARN' | 'FAIL';
  items: DiagnosticItem[];
}

export interface AppSettings {
  FLOW_URL: string;
  FLOW_GENERATION_MODE: string;
  FLOW_PROJECT_MODE: string;
  AUTO_CONFIRM_GENERATION: boolean;
  DEFAULT_MODEL: string;
  DEFAULT_ORIENTATION: string;
  DEFAULT_DURATION: string;
  DEFAULT_OUTPUTS: number;
  MAX_GENERATIONS_PER_JOB: number;
  MAX_GENERATIONS_PER_SESSION: number;
  MAX_DAILY_GENERATIONS: number;
  CONCURRENCY: number;
  CREDIT_SAFETY_MODE: CreditSafetyMode;
  MAX_DAILY_CREDITS?: number;
  MAX_SESSION_CREDITS?: number;
  MAX_JOB_COST?: number;
  BLOCK_ON_UNVERIFIED_BALANCE: boolean;
  BLOCK_ON_UNVERIFIED_COST: boolean;
  HEADLESS: boolean;
  GENERATION_TIMEOUT: number;
  RETRY_COUNT: number;
}
