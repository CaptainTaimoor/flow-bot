import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Sliders,
  Ratio,
  Clock,
  Layers,
  Bot,
  Coins,
  Trash2,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

interface CreateVideoPageProps {
  onSubmit: (jobData: {
    prompt: string;
    model?: string;
    orientation?: string;
    duration?: string;
    output_count?: number;
    generation_mode?: string;
    project?: string;
    allow_unverified_credits?: boolean;
  }) => void;
  initialPrompt?: string;
}

const EXAMPLE_PROMPTS = [
  "A cinematic landscape of a peaceful mountain lake at sunrise, realistic lighting, gentle camera movement.",
  "A futuristic cyberpunk street corner at night, vibrant neon signs reflecting in puddles, cinematic mist.",
  "Slow motion macro shot of raindrops landing on green tropical monstera leaf, photorealistic 8k.",
  "An aerial drone shot gliding across golden sand dunes in the Sahara desert at dusk, warm glow.",
];

export const CreateVideoPage: React.FC<CreateVideoPageProps> = ({
  onSubmit,
  initialPrompt = '',
}) => {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [model, setModel] = useState('');
  const [orientation, setOrientation] = useState('16:9');
  const [duration, setDuration] = useState('8');
  const [outputCount, setOutputCount] = useState(1);
  const [generationMode, setGenerationMode] = useState('STANDARD');
  const [allowUnverifiedCredits, setAllowUnverifiedCredits] = useState(false);

  const { data: caps } = useQuery({
    queryKey: ['capabilities'],
    queryFn: api.getCapabilities,
  });

  // Automatically sync model with live discovered active model
  useEffect(() => {
    if (caps?.models_available && caps.models_available.length > 0 && !model) {
      setModel(caps.active_model || caps.models_available[0]);
    }
  }, [caps, model]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    onSubmit({
      prompt: prompt.trim(),
      model: model || undefined,
      orientation,
      duration,
      output_count: outputCount,
      generation_mode: generationMode,
      allow_unverified_credits: allowUnverifiedCredits,
    });
  };

  const isCostVerified = caps?.cost_status === 'VERIFIED' && caps?.cost_per_job !== undefined && caps?.cost_per_job !== null;
  const isBalanceVerified = caps?.credit_status === 'VERIFIED' && caps?.credit_balance !== undefined && caps?.credit_balance !== null;
  
  // Dynamic cost calculation based on verified Google Flow rates
  const getEstimatedCost = () => {
    if (isCostVerified) return caps!.cost_per_job! * outputCount;
    const durNum = parseInt(duration, 10) || 8;
    const isOmni = (model || '').toLowerCase().includes('omni');
    const basePerSec = isOmni ? 1.5 : 4.0;
    return Math.round(durNum * basePerSec * outputCount);
  };
  const verifiedCost = getEstimatedCost();

  const availableModels = caps?.models_available && caps.models_available.length > 0
    ? caps.models_available
    : ['Omni 1.1 Flash', 'Veo 3.1 - Lite', 'Veo 3.1 - Fast', 'Veo 3.1 - Quality'];

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Video Composer</h1>
          <p className="text-xs text-slate-400 mt-1">
            Craft prompts with cinematic precision and configure Flow generation parameters.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Prompt Editor */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-studio-900 border border-slate-800 rounded-2xl p-6 shadow-md space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-brand-400" />
                <span>Prompt Script</span>
              </label>

              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setPrompt('')}
                  className="text-xs text-slate-400 hover:text-rose-400 transition-colors flex items-center space-x-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Clear</span>
                </button>
              </div>
            </div>

            <div className="relative">
              <textarea
                rows={7}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your scene in detail: subject, setting, atmosphere, camera motion, lighting, and style..."
                className="w-full bg-studio-950 border border-slate-700/80 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all font-sans leading-relaxed"
                required
              />
              <div className="flex items-center justify-between mt-2 px-1">
                <span className="text-[11px] text-slate-500">
                  Tip: Include camera angles (e.g. "aerial drone shot", "macro close-up")
                </span>
                <span className="text-[11px] font-mono text-slate-500">
                  {prompt.length} / 4000
                </span>
              </div>
            </div>

            {/* Presets */}
            <div className="space-y-2 pt-2 border-t border-slate-800/80">
              <span className="text-xs font-medium text-slate-400">Example Inspirations</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {EXAMPLE_PROMPTS.map((ex, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setPrompt(ex)}
                    className="p-2.5 rounded-lg bg-studio-850 hover:bg-slate-800 border border-slate-800/80 text-left text-xs text-slate-300 hover:text-white transition-colors truncate"
                  >
                    "{ex}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Settings Panel */}
        <div className="space-y-6">
          <div className="bg-studio-900 border border-slate-800 rounded-2xl p-6 shadow-md space-y-6">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
              <Sliders className="w-4 h-4 text-brand-400" />
              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Generation Parameters
              </h2>
            </div>

            {/* Model Selector */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-slate-300">Live Flow Model</label>
                {caps?.model_source === 'live' && (
                  <span className="text-[10px] text-emerald-400 font-mono flex items-center space-x-1">
                    <CheckCircle2 className="w-3 h-3 inline" />
                    <span>Live UI Verified</span>
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {availableModels.map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setModel(m)}
                    className={`py-2 px-3 rounded-xl text-xs font-medium border text-left truncate transition-all ${
                      model === m
                        ? 'bg-brand-600/20 border-brand-500 text-brand-300'
                        : 'bg-studio-950 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            {/* Orientation */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <Ratio className="w-3.5 h-3.5 text-slate-400" />
                <span>Aspect Ratio</span>
              </label>
              <div className="grid grid-cols-2 gap-2">
                {(caps?.orientations || ['16:9', '9:16']).map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setOrientation(item)}
                    className={`py-2 px-3 rounded-xl text-xs font-medium border transition-all ${
                      orientation === item
                        ? 'bg-brand-600/20 border-brand-500 text-brand-300'
                        : 'bg-studio-950 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {item === '16:9' ? '16:9 Landscape' : item === '9:16' ? '9:16 Portrait' : item}
                  </button>
                ))}
              </div>
            </div>

            {/* Duration */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>Clip Duration</span>
              </label>
              <div className="grid grid-cols-4 gap-1.5">
                {(caps?.durations || ['4', '6', '8', '10']).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDuration(d)}
                    className={`py-2 px-1 text-center rounded-xl text-xs font-medium border transition-all ${
                      duration === d
                        ? 'bg-brand-600/20 border-brand-500 text-brand-300'
                        : 'bg-studio-950 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {d}s
                  </button>
                ))}
              </div>
            </div>

            {/* Generation Mode */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <Bot className="w-3.5 h-3.5 text-slate-400" />
                <span>Flow Strategy</span>
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'STANDARD', label: 'Standard' },
                  { id: 'AGENT', label: 'Flow Agent' },
                ].map((mode) => (
                  <button
                    key={mode.id}
                    type="button"
                    onClick={() => setGenerationMode(mode.id)}
                    className={`py-2 px-3 rounded-xl text-xs font-medium border transition-all ${
                      generationMode === mode.id
                        ? 'bg-brand-600/20 border-brand-500 text-brand-300'
                        : 'bg-studio-950 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {mode.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Truthful Credit Cost Panel */}
            <div className="p-3.5 rounded-xl bg-studio-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 font-medium flex items-center space-x-1">
                  <Coins className="w-3.5 h-3.5 text-amber-400" />
                  <span>Available Balance</span>
                </span>
                <span className="font-mono font-bold text-slate-100">
                  {isBalanceVerified ? `${caps?.credit_balance?.toLocaleString()} Credits` : 'UNKNOWN'}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 font-medium">Estimated Cost</span>
                <span className="font-mono font-bold text-amber-300">
                  {verifiedCost ? `${verifiedCost} Credits` : 'Standard Flow Rate'}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                {isBalanceVerified
                  ? `Active account verified with ${caps?.credit_balance} Flow credits.`
                  : 'Flow credit balance is checked dynamically via the live session.'}
              </p>

              {/* Unverified Balance Safety Option */}
              {!isBalanceVerified && (
                <div className="pt-2 border-t border-slate-800/80">
                  <label className="flex items-start space-x-2 text-[11px] text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={allowUnverifiedCredits}
                      onChange={(e) => setAllowUnverifiedCredits(e.target.checked)}
                      className="mt-0.5 rounded border-slate-700 bg-studio-900 text-brand-500 focus:ring-0"
                    />
                    <span>Allow submission even if credit balance is UNKNOWN (bypasses strict check).</span>
                  </label>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!prompt.trim()}
              className="w-full py-3 px-4 bg-brand-600 hover:bg-brand-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-semibold rounded-xl text-sm shadow-xl shadow-brand-600/25 transition-all flex items-center justify-center space-x-2 cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>Queue Video Generation</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
