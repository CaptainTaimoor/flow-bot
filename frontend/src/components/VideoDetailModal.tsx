import React from 'react';
import { X, Download, Copy, Film, Sparkles, Check, Clock, HardDrive, Maximize } from 'lucide-react';
import { Asset, Job } from '../types';
import { VideoPlayer } from './VideoPlayer';
import { api } from '../api/client';

interface VideoDetailModalProps {
  asset: Asset;
  job?: Job;
  onClose: () => void;
  onDuplicatePrompt?: (prompt: string) => void;
}

export const VideoDetailModal: React.FC<VideoDetailModalProps> = ({
  asset,
  job,
  onClose,
  onDuplicatePrompt,
}) => {
  const [copied, setCopied] = React.useState(false);

  const streamUrl = api.getStreamUrl(asset.id);
  const downloadUrl = api.getDownloadUrl(asset.id);
  const thumbUrl = asset.thumbnail_path ? api.getThumbnailUrl(asset.id) : undefined;

  const promptText = job?.prompt || asset.filename;

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(promptText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes) return 'N/A';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const isPortrait = Boolean(asset.width && asset.height && asset.height > asset.width);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-5xl bg-studio-900 border border-slate-800 rounded-xl sm:rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[94vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-800 bg-studio-950/50">
          <div className="flex items-center space-x-2.5 sm:space-x-3 min-w-0">
            <div className="p-2 bg-brand-500/10 text-brand-400 rounded-lg shrink-0">
              <Film className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm sm:text-base font-semibold text-white truncate max-w-[200px] xs:max-w-xs sm:max-w-md">
                {asset.filename}
              </h2>
              <p className="text-[11px] sm:text-xs text-slate-400">
                Job #{asset.job_id} • Created {new Date(asset.created_at).toLocaleString()}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors shrink-0 ml-2"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 p-4 sm:p-6 overflow-y-auto">
          {/* Main Video Player */}
          <div className="lg:col-span-2 flex flex-col justify-center items-center">
            <div
              className={`w-full rounded-xl overflow-hidden bg-black shadow-lg flex items-center justify-center ${
                isPortrait ? 'max-w-[280px] sm:max-w-xs aspect-[9/16]' : 'aspect-video'
              }`}
            >
              <VideoPlayer src={streamUrl} poster={thumbUrl} autoPlay className="w-full h-full" />
            </div>
          </div>

          {/* Metadata & Actions Panel */}
          <div className="flex flex-col space-y-6">
            {/* Prompt Box */}
            <div className="bg-studio-850 p-4 rounded-xl border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Generation Prompt
                </span>
                <button
                  onClick={handleCopyPrompt}
                  className="flex items-center space-x-1 text-xs text-brand-400 hover:text-brand-300"
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <p className="text-xs text-slate-200 leading-relaxed max-h-36 overflow-y-auto">
                {promptText}
              </p>
            </div>

            {/* Technical Specifications */}
            <div className="bg-studio-850 p-4 rounded-xl border border-slate-800 space-y-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Asset Metadata
              </span>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex items-center space-x-2 text-slate-300">
                  <Clock className="w-4 h-4 text-slate-500" />
                  <span>Duration: {asset.duration ? `${asset.duration.toFixed(1)}s` : '5.0s'}</span>
                </div>
                <div className="flex items-center space-x-2 text-slate-300">
                  <HardDrive className="w-4 h-4 text-slate-500" />
                  <span>Size: {formatFileSize(asset.file_size)}</span>
                </div>
                <div className="flex items-center space-x-2 text-slate-300">
                  <Maximize className="w-4 h-4 text-slate-500" />
                  <span>
                    Resolution: {asset.width && asset.height ? `${asset.width}x${asset.height}` : '1920x1080'}
                  </span>
                </div>
                <div className="flex items-center space-x-2 text-slate-300">
                  <Sparkles className="w-4 h-4 text-slate-500" />
                  <span>Model: {job?.model || 'veo'}</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3 pt-2">
              <a
                href={downloadUrl}
                download={asset.filename}
                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-sm font-medium transition-all shadow-lg shadow-brand-600/20"
              >
                <Download className="w-4 h-4" />
                <span>Download MP4 File</span>
              </a>

              {onDuplicatePrompt && (
                <button
                  onClick={() => {
                    onDuplicatePrompt(promptText);
                    onClose();
                  }}
                  className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-sm font-medium transition-colors border border-slate-700"
                >
                  <Copy className="w-4 h-4" />
                  <span>Duplicate to Composer</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
