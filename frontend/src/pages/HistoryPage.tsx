import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { Job, Asset } from '../types';
import { 
  Search, 
  Filter, 
  RotateCw, 
  Copy, 
  Play, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  XCircle,
  Film,
  ExternalLink
} from 'lucide-react';

interface HistoryPageProps {
  onSelectAsset: (asset: Asset) => void;
  onNavigateToCreate: (prompt?: string) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ onSelectAsset, onNavigateToCreate }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  const queryClient = useQueryClient();

  const { data: jobs = [], isLoading, refetch } = useQuery({
    queryKey: ['jobs', statusFilter, searchTerm],
    queryFn: () => api.getJobs(statusFilter === 'ALL' ? undefined : statusFilter, searchTerm || undefined),
    refetchInterval: 10000,
  });

  const retryMutation = useMutation({
    mutationFn: (id: number) => api.retryJob(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['status'] });
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: (id: number) => api.duplicateJob(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['status'] });
    },
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" /> Completed
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3 h-3" /> Failed
          </span>
        );
      case 'RUNNING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <RotateCw className="w-3 h-3 animate-spin" /> In Progress
          </span>
        );
      case 'QUEUED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Clock className="w-3 h-3" /> Queued
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-300">
            {status}
          </span>
        );
    }
  };

  const filteredJobs = jobs.filter((job) => {
    if (statusFilter !== 'ALL' && job.status !== statusFilter) return false;
    if (searchTerm) {
      const matchPrompt = job.prompt.toLowerCase().includes(searchTerm.toLowerCase());
      const matchId = job.id.toString() === searchTerm;
      const matchModel = job.model?.toLowerCase().includes(searchTerm.toLowerCase());
      return matchPrompt || matchId || matchModel;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Generation History</h1>
          <p className="text-sm text-slate-400 mt-1">
            Complete audit trail of all prompt submissions, state transitions, and generated media.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 px-3 py-2 text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition"
        >
          <RotateCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by prompt, Job ID, or model..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-900/80 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900/80 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 transition"
          >
            <option value="ALL">All Statuses</option>
            <option value="SUCCESS">Completed</option>
            <option value="FAILED">Failed</option>
            <option value="RUNNING">Running</option>
            <option value="QUEUED">Queued</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/60 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Job ID</th>
                <th className="py-3 px-4">Prompt</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Model & Settings</th>
                <th className="py-3 px-4">Assets</th>
                <th className="py-3 px-4">Date & Time</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <RotateCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
                    Loading generation history...
                  </td>
                </tr>
              ) : filteredJobs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    No generation records match your filter criteria.
                  </td>
                </tr>
              ) : (
                filteredJobs.map((job) => {
                  const hasAsset = job.assets && job.assets.length > 0;
                  const firstAsset = hasAsset ? job.assets![0] : null;

                  return (
                    <tr key={job.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-mono text-xs text-indigo-400 font-semibold">
                        #{job.id}
                      </td>
                      <td className="py-3 px-4 max-w-xs md:max-w-md">
                        <p className="line-clamp-2 text-slate-200 font-medium">{job.prompt}</p>
                        {job.error_message && (
                          <p className="text-xs text-rose-400 mt-1 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3 flex-shrink-0" />
                            <span className="truncate">{job.error_message}</span>
                          </p>
                        )}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        {getStatusBadge(job.status)}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap text-xs text-slate-400">
                        <div><span className="text-slate-300 font-medium">{job.model || 'Veo 2'}</span></div>
                        <div className="text-[11px] text-slate-500">
                          {job.orientation || '16:9'} • {job.duration || '5s'}
                        </div>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        {hasAsset && firstAsset ? (
                          <button
                            onClick={() => onSelectAsset(firstAsset)}
                            className="inline-flex items-center gap-1.5 px-2 py-1 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 rounded text-xs transition"
                          >
                            <Play className="w-3 h-3" />
                            <span>View Video</span>
                          </button>
                        ) : (
                          <span className="text-xs text-slate-500">—</span>
                        )}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap text-xs text-slate-400">
                        {new Date(job.created_at).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap text-right text-xs">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => onNavigateToCreate(job.prompt)}
                            title="Duplicate prompt into Create page"
                            className="p-1.5 hover:bg-slate-700/60 rounded text-slate-400 hover:text-slate-200 transition"
                          >
                            <Copy className="w-3.5 h-3.5" />
                          </button>
                          {job.status === 'FAILED' && (
                            <button
                              onClick={() => retryMutation.mutate(job.id)}
                              disabled={retryMutation.isPending}
                              title="Retry generation"
                              className="p-1.5 hover:bg-slate-700/60 rounded text-rose-400 hover:text-rose-300 transition"
                            >
                              <RotateCw className={`w-3.5 h-3.5 ${retryMutation.isPending ? 'animate-spin' : ''}`} />
                            </button>
                          )}
                          <button
                            onClick={() => setSelectedJob(job)}
                            title="Inspect job details"
                            className="p-1.5 hover:bg-slate-700/60 rounded text-indigo-400 hover:text-indigo-300 transition"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspect Job Modal */}
      {selectedJob && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Film className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-semibold text-white">Job #{selectedJob.id} Details</h3>
              </div>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-slate-400 hover:text-white"
              >
                &times;
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Prompt</label>
                <p className="mt-1 p-3 bg-slate-950/60 rounded-lg text-slate-200 border border-slate-800/80">
                  {selectedJob.prompt}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800/60">
                  <span className="text-xs text-slate-400">Status</span>
                  <div className="mt-1">{getStatusBadge(selectedJob.status)}</div>
                </div>
                <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800/60">
                  <span className="text-xs text-slate-400">Model</span>
                  <div className="mt-1 font-medium text-slate-200">{selectedJob.model || 'Veo 2'}</div>
                </div>
                <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800/60">
                  <span className="text-xs text-slate-400">Orientation / Duration</span>
                  <div className="mt-1 font-medium text-slate-200">
                    {selectedJob.orientation || '16:9'} • {selectedJob.duration || '5s'}
                  </div>
                </div>
                <div className="p-3 bg-slate-950/40 rounded-lg border border-slate-800/60">
                  <span className="text-xs text-slate-400">Retries</span>
                  <div className="mt-1 font-medium text-slate-200">{selectedJob.retry_count}</div>
                </div>
              </div>

              {selectedJob.error_message && (
                <div className="p-3 bg-rose-950/20 border border-rose-900/50 rounded-lg text-rose-300 text-xs">
                  <span className="font-semibold block mb-0.5">Error Log:</span>
                  {selectedJob.error_message}
                </div>
              )}

              {selectedJob.assets && selectedJob.assets.length > 0 && (
                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Generated Assets</label>
                  <div className="mt-2 space-y-2">
                    {selectedJob.assets.map((asset) => (
                      <div
                        key={asset.id}
                        className="flex items-center justify-between p-2.5 bg-slate-950/60 border border-slate-800 rounded-lg"
                      >
                        <div className="text-xs">
                          <p className="font-medium text-slate-200 truncate max-w-xs">{asset.filename}</p>
                          <p className="text-slate-500">{(asset.file_size / (1024 * 1024)).toFixed(2)} MB</p>
                        </div>
                        <button
                          onClick={() => {
                            setSelectedJob(null);
                            onSelectAsset(asset);
                          }}
                          className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs transition"
                        >
                          Play Video
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedJob(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
