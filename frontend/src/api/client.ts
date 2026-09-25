import {
  Job,
  Asset,
  SystemStatus,
  FlowCapabilities,
  DiagnosticsReport,
  AppSettings,
} from '../types';

const BASE_URL = '/api/v1';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const errorText = await res.text();
    let message = `Request failed: ${res.status}`;
    try {
      const parsed = JSON.parse(errorText);
      message = parsed.detail || message;
    } catch {
      // ignore
    }
    throw new Error(message);
  }

  return res.json();
}

export const api = {
  // System & Health
  getStatus: () => request<SystemStatus>('/status'),
  getCapabilities: () => request<FlowCapabilities>('/capabilities'),

  // Jobs
  getJobs: (status?: string, search?: string) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    return request<Job[]>(`/jobs?${params.toString()}`);
  },
  getJob: (id: number) => request<Job>(`/jobs/${id}`),
  createJob: (payload: {
    prompt: string;
    model?: string;
    orientation?: string;
    duration?: string;
    output_count?: number;
    project?: string;
    generation_mode?: string;
    allow_unverified_credits?: boolean;
  }) => request<Job>('/jobs', { method: 'POST', body: JSON.stringify(payload) }),
  retryJob: (id: number) => request<Job>(`/jobs/${id}/retry`, { method: 'POST' }),
  cancelJob: (id: number) => request<Job>(`/jobs/${id}/cancel`, { method: 'POST' }),
  duplicateJob: (id: number) => request<Job>(`/jobs/${id}/duplicate`, { method: 'POST' }),

  // Assets
  getAssets: () => request<Asset[]>('/assets'),
  getAsset: (id: number) => request<Asset>(`/assets/${id}`),

  // Settings
  getSettings: () => request<AppSettings>('/settings'),
  updateSettings: (updates: Partial<AppSettings>) =>
    request<{ status: string }>('/settings', { method: 'PUT', body: JSON.stringify(updates) }),

  // Diagnostics
  getDiagnostics: () => request<DiagnosticsReport>('/diagnostics'),

  // Media URLs
  getStreamUrl: (assetId: number) => `${BASE_URL}/assets/${assetId}/stream`,
  getDownloadUrl: (assetId: number) => `${BASE_URL}/assets/${assetId}/download`,
  getThumbnailUrl: (assetId: number) => `${BASE_URL}/assets/${assetId}/thumbnail`,
};
