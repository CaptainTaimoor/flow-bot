export type JobStatus = 'QUEUED' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'RETRY_PENDING' | 'CANCELLED';

export type GenerationState =
  | 'CREATED'
  | 'QUEUED'
  | 'OPENING_BROWSER'
  | 'CHECKING_AUTH'
  | 'OPENING_FLOW'
  | 'OPENING_PROJECT'
  | 'CHECKING_CAPABILITIES'
  | 'PREPARING'
  | 'SUBMITTING'
  | 'GENERATION_STARTED'
  | 'GENERATING'
  | 'WAITING_FOR_ASSET'
  | 'LOCATING_ASSET'
  | 'DOWNLOADING'
  | 'VALIDATING'
  | 'THUMBNAIL_GENERATING'
  | 'READY'
  | 'SUCCESS'
  | 'RETRYING'
  | 'FAILED'
  | 'AUTH_REQUIRED'
  | 'MANUAL_ACTION_REQUIRED'
  | 'CANCELLED';

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
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface Job {
  id: number;
  prompt: string;
  status: JobStatus;
  model?: string;
  orientation?: string;
  duration?: string;
  output_count: number;
  project?: string;
  generation_mode: string;
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
  agent_available: boolean;
  standard_generation: boolean;
  models_available: string[];
  orientations: string[];
  durations: string[];
  max_outputs: number;
  credit_balance?: number;
  credit_info_text?: string;
  current_project?: string;
}

export interface SystemStatus {
  status: string;
  app_env: string;
  headless: boolean;
  stats: {
    active: number;
    queued: number;
    completed_today: number;
    failed_today: number;
    total_videos: number;
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
  HEADLESS: boolean;
  GENERATION_TIMEOUT: number;
  RETRY_COUNT: number;
}
