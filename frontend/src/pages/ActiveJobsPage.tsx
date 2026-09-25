import React, { useState, useEffect } from 'react';
import {
  PlayCircle,
  Clock,
  AlertCircle,
  XCircle,
  CheckCircle,
  ExternalLink,
  Cpu,
  Loader2,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { Job, GenerationState } from '../types';

interface ActiveJobsPageProps {
  onCancelJob: (jobId: number) => void;
  onOpenDiagnostics: () => void;
}

const STAGES: { state: GenerationState; label: string }[] = [
  { state: 'QUEUED', label: 'Queued' },
  { state: 'OPENING_BROWSER', label: 'Browser' },
  { state: 'CHECKING_AUTH', label: 'Session' },
  { state: 'OPENING_FLOW', label: 'Flow Studio' },
  { state: 'PREPARING', label: 'Preparing' },
  { state: 'SUBMITTING', label: 'Submitting' },
  { state: 'GENERATING', label: 'Generating' },
  { state: 'DOWNLOADING', label: 'Downloading' },
  { state: 'VALIDATING', label: 'Validating' },
  { state: 'SUCCESS', label: 'Ready' },
];

export const ActiveJobsPage: React.FC<ActiveJobsPageProps> = ({
  onCancelJob,
  onOpenDiagnostics,
}) => {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs', 'RUNNING'],
    queryFn: () => api.getJobs('RUNNING'),
    refetchInterval: 3000,
  });

  const activeJobs = jobs || [];

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center space-x-2">
            <PlayCircle className="w-6 h-6 text-brand-400" />
            <span>Active Generations</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time stage tracking and progress of active Google Flow rendering jobs.
          </p>
        </div>

        <button
          onClick={onOpenDiagnostics}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-studio-850 hover:bg-slate-800 border border-slate-700/80 rounded-xl text-xs text-slate-300 transition-colors"
        >
          <Cpu className="w-3.5 h-3.5 text-brand-400" />
          <span>System Diagnostics</span>
        </button>
      </div>

      {isLoading ? (
        <div className="p-12 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-brand-500 mx-auto" />
        </div>
      ) : activeJobs.length === 0 ? (
        <div className="bg-studio-900 border border-slate-800 rounded-2xl p-12 text-center space-y-3">
          <div className="w-12 h-12 bg-slate-800/80 text-slate-500 rounded-full flex items-center justify-center mx-auto">
            <Clock className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-200">No Active Generations</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            All submitted jobs have completed or the queue is currently idle. Create a new prompt to start generating.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {activeJobs.map((job) => (
            <ActiveJobCard key={job.id} job={job} onCancel={() => onCancelJob(job.id)} />
          ))}
        </div>
      )}
    </div>
  );
};

const ActiveJobCard: React.FC<{ job: Job; onCancel: () => void }> = ({ job, onCancel }) => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const startTime = job.started_at ? new Date(job.started_at).getTime() : Date.now();
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [job.started_at]);

  const currentState = job.latest_state || 'GENERATING';

  // Find index of current stage
  const currentStageIndex = STAGES.findIndex((s) => s.state === currentState);
  const progressPercent =
    currentStageIndex >= 0 ? Math.round(((currentStageIndex + 1) / STAGES.length) * 100) : 50;

  const formatElapsed = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}m ${s < 10 ? '0' : ''}${s}s`;
  };

  return (
    <div className="bg-studio-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Top Details */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div className="space-y-1.5 max-w-2xl">
          <div className="flex items-center space-x-2 flex-wrap gap-y-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-brand-500/20 text-brand-300 border border-brand-500/30">
              JOB #{job.id}
            </span>
            <span className="text-xs font-mono text-slate-400">
              Model: {job.model || 'veo'} • {job.orientation || '16:9'} • {job.duration || '5'}s
            </span>
          </div>
          <p className="text-sm font-medium text-slate-100 pt-1 line-clamp-3 sm:line-clamp-2">
            "{job.prompt}"
          </p>
        </div>

        <div className="flex items-center justify-between sm:justify-end space-x-4 border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-800">
          <div className="text-left sm:text-right">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Elapsed</span>
            <span className="text-sm font-mono font-semibold text-white">{formatElapsed(elapsed)}</span>
          </div>

          <button
            onClick={onCancel}
            className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 rounded-xl transition-colors"
            title="Cancel local tracking"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-300 font-medium flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-brand-400 animate-ping" />
            <span>Current Stage: <strong className="text-brand-300 font-mono">{currentState}</strong></span>
          </span>
          <span className="text-slate-400 font-mono">{progressPercent}%</span>
        </div>

        <div className="h-2 w-full bg-studio-950 rounded-full overflow-hidden border border-slate-800 relative">
          <div
            className="h-full bg-gradient-to-r from-brand-600 via-cyan-500 to-brand-400 transition-all duration-500 rounded-full"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Visual Stage Stepper */}
      <div className="overflow-x-auto no-scrollbar pb-1">
        <div className="grid grid-cols-5 md:grid-cols-10 gap-2 min-w-[300px] pt-2">
          {STAGES.map((st, idx) => {
            const isDone = idx < currentStageIndex;
            const isCurrent = idx === currentStageIndex;

            return (
              <div key={st.state} className="flex flex-col items-center text-center space-y-1">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-mono transition-all ${
                    isDone
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                      : isCurrent
                      ? 'bg-brand-500 text-white shadow-lg shadow-brand-500/40 animate-pulse'
                      : 'bg-studio-950 text-slate-600 border border-slate-800'
                  }`}
                >
                  {isDone ? <CheckCircle className="w-3.5 h-3.5" /> : idx + 1}
                </div>
                <span
                  className={`text-[10px] truncate max-w-full ${
                    isCurrent ? 'text-brand-300 font-semibold' : isDone ? 'text-slate-400' : 'text-slate-600'
                  }`}
                >
                  {st.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
