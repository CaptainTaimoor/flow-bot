import React from 'react';
import {
  LayoutDashboard,
  Sparkles,
  PlayCircle,
  ListOrdered,
  Film,
  History,
  Cpu,
  Settings,
  ChevronLeft,
  ChevronRight,
  X,
  Activity,
  Wifi,
  Radio,
  ExternalLink,
} from 'lucide-react';

export type NavItem =
  | 'overview'
  | 'create'
  | 'active'
  | 'queue'
  | 'library'
  | 'history'
  | 'diagnostics'
  | 'settings';

interface SidebarProps {
  currentTab: NavItem;
  onTabChange: (tab: NavItem) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  activeJobsCount: number;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
  network?: {
    local: string;
    network: string[];
    tailscale: string[];
    hostname?: string;
  };
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onTabChange,
  collapsed,
  onToggleCollapse,
  activeJobsCount,
  mobileOpen = false,
  onCloseMobile,
  network,
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'create', label: 'Create Video', icon: Sparkles, badge: 'New' },
    { id: 'active', label: 'Active Jobs', icon: PlayCircle, count: activeJobsCount },
    { id: 'queue', label: 'Queue', icon: ListOrdered },
    { id: 'library', label: 'Video Library', icon: Film },
    { id: 'history', label: 'History', icon: History },
    { id: 'diagnostics', label: 'Diagnostics', icon: Cpu },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const handleItemClick = (id: NavItem) => {
    onTabChange(id);
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  const navContent = (
    <div className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = currentTab === item.id;

        return (
          <button
            key={item.id}
            onClick={() => handleItemClick(item.id as NavItem)}
            className={`w-full flex items-center px-3.5 py-2.5 rounded-xl font-medium text-xs transition-all group ${
              isActive
                ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
            title={collapsed ? item.label : undefined}
          >
            <Icon
              className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-110 ${
                isActive ? 'text-white' : 'text-slate-400 group-hover:text-brand-400'
              }`}
            />

            {(!collapsed || mobileOpen) && (
              <div className="flex-1 flex items-center justify-between ml-3 text-left">
                <span>{item.label}</span>
                {item.count !== undefined && item.count > 0 && (
                  <span className="px-1.5 py-0.5 text-[10px] font-mono bg-cyan-500/20 text-cyan-300 rounded-full border border-cyan-500/30">
                    {item.count}
                  </span>
                )}
                {item.badge && (
                  <span className="px-1.5 py-0.2 text-[9px] uppercase tracking-wider font-bold bg-brand-500/20 text-brand-300 rounded">
                    {item.badge}
                  </span>
                )}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );

  return (
    <>
      {/* Mobile Backdrop & Drawer */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 md:hidden animate-fade-in"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-studio-900 border-r border-slate-800 flex flex-col md:hidden transition-transform duration-300 ease-out shadow-2xl ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Mobile Drawer Header */}
        <div className="h-16 px-4 border-b border-slate-800 flex items-center justify-between bg-studio-950/60">
          <div className="flex items-center space-x-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-brand-600 to-cyan-400 flex items-center justify-center">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-white tracking-wide">FLOW STUDIO</h2>
              <p className="text-[9px] font-mono text-brand-400">Mobile Navigation</p>
            </div>
          </div>
          <button
            onClick={onCloseMobile}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation list */}
        {navContent}

        {/* Remote Access Quick Info for Mobile */}
        {network && (network.tailscale.length > 0 || network.network.length > 0) && (
          <div className="p-3 border-t border-slate-800 bg-studio-950/40 text-[10px] space-y-1.5">
            <span className="font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <Wifi className="w-3 h-3 text-emerald-400" />
              <span>Remote Access</span>
            </span>
            {network.tailscale.map((ts, i) => (
              <div key={i} className="text-slate-300 font-mono truncate">
                Tailnet: <span className="text-cyan-400">{ts}</span>
              </div>
            ))}
            {network.network.map((lan, i) => (
              <div key={i} className="text-slate-400 font-mono truncate">
                Wi-Fi: <span className="text-slate-300">{lan}</span>
              </div>
            ))}
          </div>
        )}
      </aside>

      {/* Desktop Persistent Sidebar */}
      <aside
        className={`hidden md:flex bg-studio-900 border-r border-slate-800 transition-all duration-300 flex-col z-30 ${
          collapsed ? 'w-18' : 'w-64'
        }`}
      >
        {navContent}

        {/* Desktop Collapse Toggle */}
        <div className="p-3 border-t border-slate-800">
          <button
            onClick={onToggleCollapse}
            className="w-full flex items-center justify-center p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </aside>
    </>
  );
};
