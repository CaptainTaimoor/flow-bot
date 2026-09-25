import React from 'react';
import {
  LayoutDashboard,
  Sparkles,
  PlayCircle,
  Film,
  Menu,
} from 'lucide-react';
import { NavItem } from './Sidebar';

interface MobileBottomNavProps {
  currentTab: NavItem;
  onTabChange: (tab: NavItem) => void;
  onOpenMenu: () => void;
  activeJobsCount: number;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  currentTab,
  onTabChange,
  onOpenMenu,
  activeJobsCount,
}) => {
  const primaryTabs: { id: NavItem; label: string; icon: React.FC<{ className?: string }> }[] = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'create', label: 'Create', icon: Sparkles },
    { id: 'active', label: 'Active', icon: PlayCircle },
    { id: 'library', label: 'Library', icon: Film },
  ];

  return (
    <nav className="fixed bottom-0 inset-x-0 h-16 bg-studio-950/90 backdrop-blur-xl border-t border-slate-800/80 z-40 flex items-center justify-around px-1 md:hidden select-none safe-area-bottom">
      {primaryTabs.map((item) => {
        const Icon = item.icon;
        const isActive = currentTab === item.id;
        const isCreate = item.id === 'create';

        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onTabChange(item.id)}
            className="flex-1 flex flex-col items-center justify-center py-1 px-1 relative transition-colors"
          >
            {isCreate ? (
              <div
                className={`w-10 h-10 -mt-5 rounded-2xl flex items-center justify-center shadow-lg transition-transform active:scale-95 ${
                  isActive
                    ? 'bg-gradient-to-tr from-brand-600 to-cyan-400 text-white shadow-brand-500/30'
                    : 'bg-studio-800 border border-slate-700 text-brand-400'
                }`}
              >
                <Icon className="w-5 h-5" />
              </div>
            ) : (
              <div className="relative">
                <Icon
                  className={`w-5 h-5 transition-colors ${
                    isActive ? 'text-brand-400' : 'text-slate-400 hover:text-slate-200'
                  }`}
                />
                {item.id === 'active' && activeJobsCount > 0 && (
                  <span className="absolute -top-1 -right-2 w-4 h-4 bg-cyan-500 text-slate-950 font-bold font-mono text-[9px] rounded-full flex items-center justify-center ring-2 ring-studio-950 animate-pulse">
                    {activeJobsCount}
                  </span>
                )}
              </div>
            )}
            <span
              className={`text-[10px] font-medium tracking-tight mt-1 transition-colors ${
                isActive ? 'text-brand-400 font-semibold' : 'text-slate-400'
              }`}
            >
              {item.label}
            </span>
          </button>
        );
      })}

      {/* Menu Drawer Toggle */}
      <button
        type="button"
        onClick={onOpenMenu}
        className="flex-1 flex flex-col items-center justify-center py-1 px-1 transition-colors text-slate-400 hover:text-slate-200 active:scale-95"
      >
        <Menu className="w-5 h-5" />
        <span className="text-[10px] font-medium tracking-tight mt-1">More</span>
      </button>
    </nav>
  );
};
