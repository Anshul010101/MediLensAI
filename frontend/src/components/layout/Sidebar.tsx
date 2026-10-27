import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  UploadCloud,
  History,
  Shield,
  X,
  Sparkles,
  ExternalLink,
} from 'lucide-react';

interface SidebarProps {
  isMobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isMobileOpen, onCloseMobile }) => {
  const navItems = [
    {
      to: '/',
      label: 'Dashboard',
      icon: <LayoutDashboard className="w-5 h-5" />,
      end: true,
    },
    {
      to: '/upload',
      label: 'Upload Report',
      icon: <UploadCloud className="w-5 h-5" />,
    },
    {
      to: '/history',
      label: 'Report History',
      icon: <History className="w-5 h-5" />,
    },
    {
      to: '/settings',
      label: 'Privacy & Settings',
      icon: <Shield className="w-5 h-5" />,
    },
  ];

  const linkClasses = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
      isActive
        ? 'bg-brand-50 text-brand-700 font-semibold border border-brand-200/80 shadow-subtle'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
    }`;

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white border-r border-slate-200">
      {/* Mobile header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-100 lg:hidden">
        <span className="font-bold text-slate-900">Navigation</span>
        <button
          onClick={onCloseMobile}
          className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
          aria-label="Close menu"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation links */}
      <nav className="flex-1 p-4 space-y-1.5" aria-label="Main Navigation">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onCloseMobile}
            className={linkClasses}
          >
            <span className="text-current">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Sidebar footer: demo mode info */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="p-3 bg-white rounded-xl border border-slate-200/80 shadow-subtle">
          <div className="flex items-center gap-2 text-xs font-semibold text-purple-700 mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Demonstration Notice</span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Use synthetic laboratory samples for risk-free assessment. Raw PDFs are not persisted to disk.
          </p>
          <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] text-slate-500 font-medium">MediLens v0.1.0</span>
            <NavLink
              to="/settings"
              onClick={onCloseMobile}
              className="text-[11px] text-brand-600 hover:text-brand-700 font-medium inline-flex items-center gap-0.5"
            >
              <span>Audit</span>
              <ExternalLink className="w-3 h-3" />
            </NavLink>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop static sidebar */}
      <aside className="hidden lg:block w-64 flex-shrink-0">
        <div className="sticky top-16 h-[calc(100vh-4rem)]">
          {sidebarContent}
        </div>
      </aside>

      {/* Mobile drawer backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden animate-fade-in"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* Mobile drawer */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-72 transform transition-transform duration-200 ease-in-out lg:hidden ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {sidebarContent}
      </div>
    </>
  );
};
