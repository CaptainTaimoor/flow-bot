import React from 'react';
import {
  Radio,
  Coins,
  Globe,
  Activity,
  ShieldCheck,
  Menu,
  Wifi,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

interface NavbarProps {
  onToggleMobileMenu?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleMobileMenu }) => {
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

  const isCreditVerified =
    caps?.credit_status === 'VERIFIED' &&
    caps?.credit_balance !== undefined &&
    caps?.credit_balance !== null;
  const safetyMode = status?.credit_safety_mode || 'STRICT';
  const hasTailscale = Boolean(status?.network?.tailscale && status.network.tailscale.length > 0);

  return (
    <header className="h-16 bg-studio-900/80 backdrop-blur-md border-b border-slate-800 px-3 sm:px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Left: Mobile Toggle & Branding */}
      <div className="flex items-center space-x-2.5 sm:space-x-3">
        {onToggleMobileMenu && (
          <button
            type="button"
            onClick={onToggleMobileMenu}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800/80 transition md:hidden"
            title="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-brand-500/20 shrink-0">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-white tracking-wide flex items-center gap-1.5">
            <span>FLOW STUDIO</span>
            <span className="text-brand-400 font-mono text-[10px] font-normal px-1 rounded bg-brand-500/10 border border-brand-500/20">
              V2.0
            </span>
          </h1>
          <p className="text-[9px] sm:text-[10px] text-slate-400 uppercase tracking-widest hidden xs:block">
            Google Flow Automation
          </p>
        </div>
      </div>

      {/* Right: Live Badges */}
      <div className="flex items-center space-x-2 sm:space-x-3">
        {/* Tailnet status pill */}
        {hasTailscale && (
          <div
            className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300"
            title="Tailscale Tailnet remote access enabled"
          >
            <Wifi className="w-3 h-3 text-indigo-400" />
            <span className="text-[10px] font-mono">Tailnet Active</span>
          </div>
        )}

        {/* Credit Policy Mode */}
        <div className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-studio-800 border border-slate-700/60">
          <ShieldCheck className="w-3.5 h-3.5 text-brand-400" />
          <span className="text-[11px] font-mono text-slate-300 uppercase">
            Policy: {safetyMode}
          </span>
        </div>

        {/* Truthful Credits Chip */}
        <div className="flex items-center space-x-1.5 sm:space-x-2 px-2.5 sm:px-3 py-1.5 rounded-full bg-studio-800 border border-slate-700/60 shadow-inner">
          <Coins className={`w-3.5 h-3.5 ${isCreditVerified ? 'text-amber-400' : 'text-slate-400'}`} />
          <span className="text-xs font-semibold text-slate-200">
            {isCreditVerified ? (
              <>
                <span className="hidden sm:inline">{caps?.credit_balance?.toLocaleString()} Credits</span>
                <span className="inline sm:hidden">{caps?.credit_balance} Cr</span>
              </>
            ) : (
              'Unknown'
            )}
          </span>
        </div>

        {/* Browser Status */}
        <div className="hidden xl:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-studio-800 border border-slate-700/60">
          <Globe className="w-3.5 h-3.5 text-brand-400" />
          <span className="text-xs text-slate-300">
            {status?.headless ? 'Headless' : 'Headed Profile'}
          </span>
        </div>

        {/* Flow Connection Status */}
        {caps?.authenticated ? (
          <div className="flex items-center space-x-1.5 sm:space-x-2 px-2.5 sm:px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-medium text-emerald-400 hidden sm:inline">Flow Connected</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 sm:space-x-2 px-2.5 sm:px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30">
            <div className="w-2 h-2 rounded-full bg-amber-400" />
            <span className="text-xs font-medium text-amber-400 hidden sm:inline">Session Ready</span>
          </div>
        )}

        {/* SSE Live Pulse */}
        <div className="flex items-center space-x-1 text-xs text-slate-400 pl-1">
          <Radio className="w-3.5 h-3.5 text-brand-400 animate-pulse" />
          <span className="hidden sm:inline text-[10px] font-mono">LIVE</span>
        </div>
      </div>
    </header>
  );
};
