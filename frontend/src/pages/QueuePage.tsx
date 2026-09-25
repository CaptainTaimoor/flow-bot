import React from 'react';
import {
  ListOrdered,
  RotateCw,
  XCircle,
  Copy,
  Clock,
  AlertTriangle,
  PlayCircle,
  CheckCircle,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { Job } from '../types';

interface QueuePageProps {
  onRetry: (id: number) => void;
  onCancel: (id: number) => void;
  onDuplicate: (id: number) => void;
}

export const QueuePage: React.FC<QueuePageProps> = ({
  onRetry,
  onCancel,
  onDuplicate,
}) => {
  const { data: allJobs = [] } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => api.getJobs(),
    refetchInterval: 4000,
  });

  const running = allJobs.filter((j) => j.status === 'RUNNING');
  const queued = allJobs.filter((j) => j.status === 'QUEUED');
  const failed = allJobs.filter((j) => j.status === 'FAILED');

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center space-x-2">
            <ListOrdered className="w-6 h-6 text-brand-400" />
            <span>Generation Queue</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage pending, active, and failed video generation tasks. Concurrency is limited to 1 for account safety.
          </p>
        </div>
      </div>

      {/* Running Section */}
      <div className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-cyan-400 flex items-center space-x-2">
          <PlayCircle className="w-4 h-4" />
          <span>Currently Processing ({running.length})</span>
        </h2>

        {running.length === 0 ? (
          <div className="p-4 bg-studio-900/40 border border-slate-800/80 rounded-xl text-xs text-slate-500 text-center">
            No job currently processing.
          </div>
        ) : (
          running.map((j) => (
            <QueueItem key={j.id} job={j} onCancel={() => onCancel(j.id)} isRunning />
          ))
        )}
      </div>

      {/* Queued Section */}
      <div className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-amber-400 flex items-center space-x-2">
          <Clock className="w-4 h-4" />
          <span>Up Next in Queue ({queued.length})</span>
        </h2>

        {queued.length === 0 ? (
          <div className="p-4 bg-studio-900/40 border border-slate-800/80 rounded-xl text-xs text-slate-500 text-center">
            Queue is currently empty.
          </div>
        ) : (
          queued.map((j) => (
            <QueueItem
              key={j.id}
              job={j}
              onCancel={() => onCancel(j.id)}
              onDuplicate={() => onDuplicate(j.id)}
            />
          ))
        )}
      </div>

      {/* Failed Section */}
      {failed.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-rose-400 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4" />
            <span>Failed Jobs ({failed.length})</span>
          </h2>

          {failed.map((j) => (
            <QueueItem
              key={j.id}
              job={j}
              onRetry={() => onRetry(j.id)}
              onDuplicate={() => onDuplicate(j.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const QueueItem: React.FC<{
  job: Job;
  isRunning?: boolean;
  onRetry?: () => void;
  onCancel?: () => void;
  onDuplicate?: () => void;
}> = ({ job, isRunning, onRetry, onCancel, onDuplicate }) => {
  return (
    <div className="bg-studio-900 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
      <div className="space-y-1.5 max-w-xl">
        <div className="flex items-center space-x-2 text-xs flex-wrap gap-y-1">
          <span className="font-mono font-bold text-slate-300">#{job.id}</span>
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${
              isRunning
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : job.status === 'FAILED'
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
            }`}
          >
            {job.status}
          </span>
          <span className="text-slate-500 text-[11px]">
            {new Date(job.created_at).toLocaleTimeString()}
          </span>
        </div>
        <p className="text-xs text-slate-200 line-clamp-2">"{job.prompt}"</p>
        {job.error_message && (
          <p className="text-[11px] text-rose-400 font-mono line-clamp-2">{job.error_message}</p>
        )}
      </div>

      <div className="flex items-center space-x-2 self-end sm:self-auto shrink-0">
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Retry</span>
          </button>
        )}

        {onDuplicate && (
          <button
            onClick={onDuplicate}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            title="Duplicate job"
          >
            <Copy className="w-4 h-4" />
          </button>
        )}

        {onCancel && (
          <button
            onClick={onCancel}
            className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
            title="Cancel job"
          >
            <XCircle className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
