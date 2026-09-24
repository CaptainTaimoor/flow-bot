import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  RotateCw, 
  ShieldCheck, 
  Cpu, 
  Database, 
  HardDrive, 
  Globe, 
  Film, 
  Server
} from 'lucide-react';

export const DiagnosticsPage: React.FC = () => {
  const { data: report, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['diagnostics'],
    queryFn: () => api.getDiagnostics(),
  });

  const getStatusIcon = (status: 'PASS' | 'WARN' | 'FAIL') => {
    switch (status) {
      case 'PASS':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case 'WARN':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      case 'FAIL':
        return <XCircle className="w-5 h-5 text-rose-400" />;
    }
  };

  const getStatusBadge = (status: 'PASS' | 'WARN' | 'FAIL') => {
    switch (status) {
      case 'PASS':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            HEALTHY
          </span>
        );
      case 'WARN':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            WARNING
          </span>
        );
      case 'FAIL':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            CRITICAL
          </span>
        );
    }
  };

  const getIconForName = (name: string) => {
    if (name.includes('Core')) return <Cpu className="w-5 h-5 text-indigo-400" />;
    if (name.includes('Database')) return <Database className="w-5 h-5 text-cyan-400" />;
    if (name.includes('Media')) return <HardDrive className="w-5 h-5 text-blue-400" />;
    if (name.includes('Playwright') || name.includes('Browser')) return <Globe className="w-5 h-5 text-amber-400" />;
    if (name.includes('FFmpeg') || name.includes('FFprobe')) return <Film className="w-5 h-5 text-purple-400" />;
    return <Server className="w-5 h-5 text-slate-400" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Activity className="w-6 h-6 text-indigo-400" />
            System Diagnostics & Health
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Automated verification of runtime dependencies, database connectivity, and media binaries.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg shadow-sm transition"
        >
          <RotateCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          Run Health Check
        </button>
      </div>

      {/* Overall Health Summary Banner */}
      {report && (
        <div className={`p-6 rounded-2xl border transition-all ${
          report.overall_status === 'PASS'
            ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200'
            : report.overall_status === 'WARN'
            ? 'bg-amber-950/20 border-amber-500/30 text-amber-200'
            : 'bg-rose-950/20 border-rose-500/30 text-rose-200'
        }`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <ShieldCheck className="w-8 h-8 text-indigo-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-white">System Status: {report.overall_status}</h2>
                  {getStatusBadge(report.overall_status)}
                </div>
                <p className="text-sm text-slate-400 mt-0.5">
                  Last evaluated at {new Date(report.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Diagnostics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {isLoading ? (
          <div className="col-span-2 py-16 text-center text-slate-400">
            <RotateCw className="w-8 h-8 animate-spin mx-auto mb-3 text-indigo-500" />
            Evaluating system health checks...
          </div>
        ) : (
          report?.items.map((item, idx) => (
            <div
              key={idx}
              className="p-5 bg-slate-900/80 border border-slate-800 rounded-xl hover:border-slate-700/80 transition flex items-start gap-4"
            >
              <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/50">
                {getIconForName(item.name)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold text-white truncate">{item.name}</h3>
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    {getStatusIcon(item.status)}
                    <span className="text-xs font-mono font-medium text-slate-400">{item.status}</span>
                  </div>
                </div>
                <p className="text-xs text-slate-300 mt-1.5 break-words font-mono bg-slate-950/40 p-2 rounded border border-slate-800/60">
                  {item.message}
                </p>
                {item.details && (
                  <p className="text-[11px] text-slate-500 mt-1 truncate">
                    {item.details}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Recommendations & Guidelines */}
      <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Troubleshooting Notes</h4>
        <ul className="text-xs text-slate-400 space-y-1.5 list-disc list-inside">
          <li>Ensure Google Chrome profile in <code className="text-indigo-400">runtime/profile</code> remains logged in to Google Flow.</li>
          <li>For optimal thumbnail generation, verify <code className="text-indigo-400">ffmpeg</code> and <code className="text-indigo-400">ffprobe</code> are accessible on your system PATH.</li>
          <li>Never share or commit browser profile directories containing session tokens.</li>
        </ul>
      </div>
    </div>
  );
};
