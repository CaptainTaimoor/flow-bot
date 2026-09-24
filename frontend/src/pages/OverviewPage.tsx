import React, { useState } from 'react';
import {
  Sparkles,
  PlayCircle,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Film,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { Asset } from '../types';

interface OverviewPageProps {
  onCreateJob: (prompt: string) => void;
  onSelectAsset: (asset: Asset) => void;
  onNavigate: (tab: any) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  onCreateJob,
  onSelectAsset,
  onNavigate,
}) => {
  const [quickPrompt, setQuickPrompt] = useState('');

  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: api.getStatus,
    refetchInterval: 10000,
  });

  const { data: assets } = useQuery({
    queryKey: ['assets'],
    queryFn: api.getAssets,
    refetchInterval: 10000,
  });

  const handleQuickSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickPrompt.trim()) return;
    onCreateJob(quickPrompt.trim());
    setQuickPrompt('');
  };

  const stats = status?.stats || {
    active: 0,
    queued: 0,
    completed_today: 0,
    failed_today: 0,
    total_videos: 0,
  };

  const recentAssets = (assets || []).slice(0, 4);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-900/60 via-studio-850 to-studio-900 border border-brand-500/20 p-8 shadow-xl">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-medium mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Google Flow Video Studio V2</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight mb-2">
            AI Video Generation Command Center
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Autonomous multi-signal Flow automation with persistent browser sessions, live stage tracking, and seamless video streaming.
          </p>
        </div>

        {/* Subtle decorative glow */}
        <div className="absolute right-0 top-0 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-studio-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Active Generations</span>
            <PlayCircle className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-white">{stats.active}</p>
        </div>

        <div className="bg-studio-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">In Queue</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-white">{stats.queued}</p>
        </div>

        <div className="bg-studio-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Completed Today</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-emerald-400">{stats.completed_today}</p>
        </div>

        <div className="bg-studio-900 border border-slate-800 p-4 rounded-xl shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Failed</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-rose-400">{stats.failed_today}</p>
        </div>

        <div className="bg-studio-900 border border-slate-800 p-4 rounded-xl shadow-sm col-span-2 md:col-span-1">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Library Assets</span>
            <Film className="w-4 h-4 text-purple-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-purple-400">{stats.total_videos}</p>
        </div>
      </div>

      {/* Quick Generator Composer */}
      <div className="bg-studio-900 border border-slate-800 rounded-2xl p-6 shadow-md">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-brand-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
              Instant Generation
            </h2>
          </div>
          <button
            onClick={() => onNavigate('create')}
            className="flex items-center space-x-1 text-xs text-brand-400 hover:text-brand-300 font-medium"
          >
            <span>Advanced Composer</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <form onSubmit={handleQuickSubmit} className="space-y-4">
          <div className="relative">
            <textarea
              rows={3}
              value={quickPrompt}
              onChange={(e) => setQuickPrompt(e.target.value)}
              placeholder="Describe your scene in cinematic detail (e.g. A futuristic city at twilight with glowing neon reflections on wet asphalt, volumetric lighting...)"
              className="w-full bg-studio-950 border border-slate-700/80 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all"
            />
            <span className="absolute bottom-3 right-3 text-[11px] font-mono text-slate-500">
              {quickPrompt.length}/4000
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs text-slate-400">
              <span>Standard Model: <strong className="text-slate-200">Veo (16:9, 5s)</strong></span>
            </div>
            <button
              type="submit"
              disabled={!quickPrompt.trim()}
              className="flex items-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl text-xs font-semibold shadow-lg shadow-brand-600/20 transition-all cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>Queue Video</span>
            </button>
          </div>
        </form>
      </div>

      {/* Recent Videos Row */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Film className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
              Recent Video Renders
            </h2>
          </div>
          <button
            onClick={() => onNavigate('library')}
            className="flex items-center space-x-1 text-xs text-brand-400 hover:text-brand-300 font-medium"
          >
            <span>View All Library</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recentAssets.length === 0 ? (
          <div className="bg-studio-900/60 border border-dashed border-slate-800 rounded-2xl p-8 text-center">
            <Film className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-400 font-medium">No videos generated yet</p>
            <p className="text-xs text-slate-500 mt-1">Submit your first prompt above to initiate video generation!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {recentAssets.map((asset) => {
              const thumb = asset.thumbnail_path ? api.getThumbnailUrl(asset.id) : undefined;
              return (
                <div
                  key={asset.id}
                  onClick={() => onSelectAsset(asset)}
                  className="group relative bg-studio-900 border border-slate-800 rounded-xl overflow-hidden cursor-pointer hover:border-brand-500/60 transition-all shadow-md"
                >
                  <div className="aspect-video bg-black relative flex items-center justify-center overflow-hidden">
                    {thumb ? (
                      <img src={thumb} alt={asset.filename} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                    ) : (
                      <div className="flex flex-col items-center justify-center text-slate-600">
                        <Film className="w-8 h-8 mb-1" />
                        <span className="text-[10px]">Ready</span>
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                      <div className="w-10 h-10 rounded-full bg-brand-500 text-white flex items-center justify-center shadow-lg">
                        <PlayCircle className="w-6 h-6" />
                      </div>
                    </div>
                  </div>
                  <div className="p-3">
                    <p className="text-xs font-medium text-slate-200 truncate">{asset.filename}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">{new Date(asset.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
