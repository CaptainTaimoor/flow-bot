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
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onTabChange,
  collapsed,
  onToggleCollapse,
  activeJobsCount,
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

  return (
    <aside
      className={`bg-studio-900 border-r border-slate-800 transition-all duration-300 flex flex-col z-30 ${
        collapsed ? 'w-18' : 'w-64'
      }`}
    >
      {/* Navigation List */}
      <nav className="flex-1 py-6 px-3 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id as NavItem)}
              className={`w-full flex items-center px-3 py-2.5 rounded-xl font-medium text-xs transition-all group ${
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

              {!collapsed && (
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
      </nav>

      {/* Collapse Toggle */}
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
  );
};
