import React from 'react';
import { Radio, Coins, Globe, Activity, ShieldCheck, AlertTriangle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

export const Navbar: React.FC = () => {
  const { data: caps } = useQuery({
    queryKey: ['capabilities'],
    queryFn: api.getCapabilities,
    refetchInterval: 30000,
  });

  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: api.getStatus,
    refetchInterval: 15000,
  });

  const isCreditVerified = caps?.credit_status === 'VERIFIED' && caps?.credit_balance !== undefined && caps?.credit_balance !== null;
  const safetyMode = status?.credit_safety_mode || 'STRICT';

  return (
    <header className="h-16 bg-studio-900/80 backdrop-blur-md border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Left: Branding */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-white tracking-wide">
            FLOW STUDIO <span className="text-brand-400 font-mono text-xs font-normal">V2.0</span>
          </h1>
          <p className="text-[10px] text-slate-400 uppercase tracking-widest">
            Google Flow Automation
          </p>
        </div>
      </div>

      {/* Right: Live Badges */}
      <div className="flex items-center space-x-3 sm:space-x-4">
        {/* Credit Policy Mode */}
        <div className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-studio-800 border border-slate-700/60">
          <ShieldCheck className="w-3.5 h-3.5 text-brand-400" />
          <span className="text-[11px] font-mono text-slate-300 uppercase">
            Policy: {safetyMode}
          </span>
        </div>

        {/* Truthful Credits Chip */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-studio-800 border border-slate-700/60 shadow-inner">
          <Coins className={`w-3.5 h-3.5 ${isCreditVerified ? 'text-amber-400' : 'text-slate-400'}`} />
          <span className="text-xs font-medium text-slate-200">
            {isCreditVerified ? `${caps?.credit_balance?.toLocaleString()} Credits` : 'Credits: UNKNOWN'}
          </span>
        </div>

        {/* Browser Status */}
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-studio-800 border border-slate-700/60">
          <Globe className="w-3.5 h-3.5 text-brand-400" />
          <span className="text-xs text-slate-300">
            {status?.headless ? 'Headless' : 'Headed Profile'}
          </span>
        </div>

        {/* Flow Connection Status */}
        {caps?.authenticated ? (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-medium text-emerald-400">Flow Connected</span>
          </div>
        ) : (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30">
            <div className="w-2 h-2 rounded-full bg-amber-400" />
            <span className="text-xs font-medium text-amber-400">Session Ready</span>
          </div>
        )}

        {/* SSE Live Pulse */}
        <div className="flex items-center space-x-1.5 text-xs text-slate-400">
          <Radio className="w-3.5 h-3.5 text-brand-400 animate-pulse" />
          <span className="hidden md:inline text-[11px] font-mono">LIVE</span>
        </div>
      </div>
    </header>
  );
};
