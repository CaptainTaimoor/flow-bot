import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { AppSettings, CreditSafetyMode } from '../types';
import { 
  Settings, 
  Save, 
  RotateCcw, 
  ShieldAlert, 
  Sliders, 
  Globe, 
  Check, 
  Cpu,
  Coins
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<AppSettings | null>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => api.getSettings(),
  });

  const { data: caps } = useQuery({
    queryKey: ['capabilities'],
    queryFn: () => api.getCapabilities(),
  });

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: (updates: Partial<AppSettings>) => api.updateSettings(updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      queryClient.invalidateQueries({ queryKey: ['status'] });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    },
  });

  if (isLoading || !formData) {
    return (
      <div className="py-24 text-center text-slate-400">
        <RotateCcw className="w-8 h-8 animate-spin mx-auto mb-3 text-indigo-500" />
        Loading application settings...
      </div>
    );
  }

  const handleChange = (key: keyof AppSettings, value: any) => {
    setFormData((prev) => (prev ? { ...prev, [key]: value } : null));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData) {
      updateMutation.mutate(formData);
    }
  };

  const availableModels = caps?.models_available && caps.models_available.length > 0
    ? caps.models_available
    : ['Nano Banana 2', 'Gemini Omni Flash'];

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Settings className="w-6 h-6 text-indigo-400" />
            System & Engine Settings
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Configure Google Flow automation parameters, credit policy guards, and browser runtime options.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {savedSuccess && (
            <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 bg-emerald-950/40 px-3 py-1.5 rounded-lg border border-emerald-500/30">
              <Check className="w-3.5 h-3.5" />
              Settings Saved
            </span>
          )}
          <button
            type="submit"
            disabled={updateMutation.isPending}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg shadow-sm transition cursor-pointer"
          >
            <Save className="w-4 h-4" />
            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Credit Policy & Safety Section */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-5">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <Coins className="w-4 h-4 text-amber-400" />
          <h2 className="text-base font-semibold text-white">Flow Model & Credit Policy</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Credit Safety Mode
            </label>
            <select
              value={formData.CREDIT_SAFETY_MODE || 'STRICT'}
              onChange={(e) => handleChange('CREDIT_SAFETY_MODE', e.target.value as CreditSafetyMode)}
              className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition"
            >
              <option value="STRICT">STRICT (Block if credit balance or cost is UNKNOWN)</option>
              <option value="WARN">WARN (Log warning, permit generation with unverified balance)</option>
              <option value="ALLOW_UNKNOWN">ALLOW_UNKNOWN (Explicitly allow unverified credit execution)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Max Daily Generation Limit
            </label>
            <input
              type="number"
              min={1}
              value={formData.MAX_DAILY_GENERATIONS}
              onChange={(e) => handleChange('MAX_DAILY_GENERATIONS', parseInt(e.target.value) || 20)}
              className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition font-mono"
            />
          </div>
        </div>

        <div className="space-y-3 pt-2">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.BLOCK_ON_UNVERIFIED_BALANCE ?? true}
              onChange={(e) => handleChange('BLOCK_ON_UNVERIFIED_BALANCE', e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 bg-slate-950 border-slate-700 focus:ring-indigo-500"
            />
            <div>
              <span className="text-sm font-medium text-slate-200">Block on Unverified Balance (Strict Mode)</span>
              <p className="text-xs text-slate-400">
                Prevents accidental credit expenditure if Google Flow does not visibly publish the account balance.
              </p>
            </div>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.BLOCK_ON_UNVERIFIED_COST ?? true}
              onChange={(e) => handleChange('BLOCK_ON_UNVERIFIED_COST', e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 bg-slate-950 border-slate-700 focus:ring-indigo-500"
            />
            <div>
              <span className="text-sm font-medium text-slate-200">Block on Unverified Cost (Strict Mode)</span>
              <p className="text-xs text-slate-400">
                Prevents submission if generation cost cannot be confirmed from the prompt bar.
              </p>
            </div>
          </label>
        </div>
      </div>

      {/* Flow Service Section */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-5">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <Globe className="w-4 h-4 text-indigo-400" />
          <h2 className="text-base font-semibold text-white">Flow Target & Engine</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Flow URL
            </label>
            <input
              type="text"
              value={formData.FLOW_URL}
              onChange={(e) => handleChange('FLOW_URL', e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Generation Mode
            </label>
            <select
              value={formData.FLOW_GENERATION_MODE}
              onChange={(e) => handleChange('FLOW_GENERATION_MODE', e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition"
            >
              <option value="STANDARD">Standard Form</option>
              <option value="AGENT">Agent / Studio Chat</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Project Selection Mode
            </label>
            <select
              value={formData.FLOW_PROJECT_MODE}
              onChange={(e) => handleChange('FLOW_PROJECT_MODE', e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition"
            >
              <option value="REUSE_SINGLE_PROJECT">Reuse Single / Latest Project</option>
              <option value="CREATE_PROJECT_PER_JOB">Always Create New Project</option>
            </select>
          </div>
        </div>

        <div className="pt-2">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.AUTO_CONFIRM_GENERATION}
              onChange={(e) => handleChange('AUTO_CONFIRM_GENERATION', e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 bg-slate-950 border-slate-700 focus:ring-indigo-500"
            />
            <div>
              <span className="text-sm font-medium text-slate-200">Auto-Approve Generation Prompts</span>
              <p className="text-xs text-slate-400">
                Automatically confirm Google Flow confirmation dialogs (e.g. "Always approve" / "Approve")
              </p>
            </div>
          </label>
        </div>
      </div>

      {/* Generation Defaults Section */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-5">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <Sliders className="w-4 h-4 text-cyan-400" />
          <h2 className="text-base font-semibold text-white">Generation Defaults</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Default Model
            </label>
            <select
              value={formData.DEFAULT_MODEL}
              onChange={(e) => handleChange('DEFAULT_MODEL', e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition"
            >
              {availableModels.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Default Orientation
            </label>
            <select
              value={formData.DEFAULT_ORIENTATION}
              onChange={(e) => handleChange('DEFAULT_ORIENTATION', e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition"
            >
              <option value="16:9">Landscape (16:9)</option>
              <option value="9:16">Portrait (9:16)</option>
              <option value="1:1">Square (1:1)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Default Duration
            </label>
            <select
              value={formData.DEFAULT_DURATION}
              onChange={(e) => handleChange('DEFAULT_DURATION', e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition"
            >
              <option value="5">5 Seconds</option>
              <option value="8">8 Seconds</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Default Outputs Count
            </label>
            <input
              type="number"
              min={1}
              max={4}
              value={formData.DEFAULT_OUTPUTS}
              onChange={(e) => handleChange('DEFAULT_OUTPUTS', parseInt(e.target.value) || 1)}
              className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition font-mono"
            />
          </div>
        </div>
      </div>

      {/* Runtime & Browser Section */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-5">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
          <Cpu className="w-4 h-4 text-purple-400" />
          <h2 className="text-base font-semibold text-white">Browser & Engine Runtime</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Generation Timeout (seconds)
            </label>
            <input
              type="number"
              min={30}
              value={formData.GENERATION_TIMEOUT}
              onChange={(e) => handleChange('GENERATION_TIMEOUT', parseInt(e.target.value) || 300)}
              className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Max Failure Retries
            </label>
            <input
              type="number"
              min={0}
              max={5}
              value={formData.RETRY_COUNT}
              onChange={(e) => handleChange('RETRY_COUNT', parseInt(e.target.value) || 0)}
              className="w-full px-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition font-mono"
            />
          </div>
        </div>

        <div className="pt-2">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.HEADLESS}
              onChange={(e) => handleChange('HEADLESS', e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 bg-slate-950 border-slate-700 focus:ring-indigo-500"
            />
            <div>
              <span className="text-sm font-medium text-slate-200">Run Headless Browser</span>
              <p className="text-xs text-slate-400">
                Run browser without visible window during automated execution. (Turn off if manual login or visual verification is needed)
              </p>
            </div>
          </label>
        </div>
      </div>
    </form>
  );
};
