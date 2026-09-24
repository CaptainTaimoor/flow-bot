import React, { useState } from 'react';
import {
  Film,
  Download,
  Play,
  Search,
  SlidersHorizontal,
  Clock,
  HardDrive,
  Maximize2,
  Trash2,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { Asset } from '../types';

interface VideoLibraryPageProps {
  onSelectAsset: (asset: Asset) => void;
}

export const VideoLibraryPage: React.FC<VideoLibraryPageProps> = ({
  onSelectAsset,
}) => {
  const [search, setSearch] = useState('');

  const { data: assets = [], isLoading } = useQuery({
    queryKey: ['assets'],
    queryFn: api.getAssets,
    refetchInterval: 10000,
  });

  const filteredAssets = assets.filter((a) =>
    a.filename.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in max-w-6xl mx-auto">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center space-x-2">
            <Film className="w-6 h-6 text-purple-400" />
            <span>Video Library</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Browse, preview, and download completed Google Flow video assets.
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by filename..."
            className="w-full pl-9 pr-4 py-2 bg-studio-900 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
          />
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="p-16 text-center text-slate-500">Loading library...</div>
      ) : filteredAssets.length === 0 ? (
        <div className="p-16 bg-studio-900 border border-dashed border-slate-800 rounded-2xl text-center space-y-2">
          <Film className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300">No Video Assets Found</h3>
          <p className="text-xs text-slate-500">
            {search ? 'Try adjusting your search criteria.' : 'Videos downloaded by Flow Bot will appear here.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filteredAssets.map((asset) => {
            const thumbUrl = asset.thumbnail_path ? api.getThumbnailUrl(asset.id) : undefined;
            const downloadUrl = api.getDownloadUrl(asset.id);

            return (
              <div
                key={asset.id}
                className="group bg-studio-900 border border-slate-800 hover:border-brand-500/50 rounded-2xl overflow-hidden shadow-lg transition-all duration-300 flex flex-col"
              >
                {/* Thumbnail / Video Preview Area */}
                <div
                  onClick={() => onSelectAsset(asset)}
                  className="aspect-video bg-black relative cursor-pointer overflow-hidden flex items-center justify-center"
                >
                  {thumbUrl ? (
                    <img
                      src={thumbUrl}
                      alt={asset.filename}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center text-slate-600">
                      <Film className="w-10 h-10 mb-1" />
                      <span className="text-[10px]">Video Ready</span>
                    </div>
                  )}

                  {/* Duration Pill */}
                  <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/70 backdrop-blur-md text-[10px] font-mono text-white flex items-center space-x-1">
                    <Clock className="w-2.5 h-2.5" />
                    <span>{asset.duration ? `${asset.duration.toFixed(1)}s` : '5.0s'}</span>
                  </div>

                  {/* Play Overlay */}
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                    <div className="w-12 h-12 rounded-full bg-brand-500 text-white flex items-center justify-center shadow-xl transform scale-90 group-hover:scale-100 transition-transform">
                      <Play className="w-6 h-6 fill-current ml-0.5" />
                    </div>
                  </div>
                </div>

                {/* Details Footer */}
                <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                  <div>
                    <h3
                      onClick={() => onSelectAsset(asset)}
                      className="text-xs font-semibold text-slate-100 hover:text-brand-300 cursor-pointer truncate transition-colors"
                      title={asset.filename}
                    >
                      {asset.filename}
                    </h3>
                    <div className="flex items-center space-x-2 text-[10px] text-slate-400 mt-1">
                      <span>Job #{asset.job_id}</span>
                      <span>•</span>
                      <span>{new Date(asset.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* Quick Action Buttons */}
                  <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                    <button
                      onClick={() => onSelectAsset(asset)}
                      className="flex items-center space-x-1 text-xs text-brand-400 hover:text-brand-300 font-medium"
                    >
                      <Maximize2 className="w-3.5 h-3.5" />
                      <span>Inspect</span>
                    </button>

                    <a
                      href={downloadUrl}
                      download={asset.filename}
                      className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                      title="Direct download"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
