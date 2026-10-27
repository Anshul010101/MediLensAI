import React, { useEffect, useState } from 'react';
import { Menu, ShieldCheck, FileText } from 'lucide-react';
import { apiService } from '../../services/api';
import { HealthResponse } from '../../types/report';

interface NavbarProps {
  onToggleMobileMenu: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleMobileMenu }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    apiService
      .getHealth()
      .then((data) => {
        if (mounted) {
          setHealth(data);
          setIsBackendHealthy(true);
        }
      })
      .catch(() => {
        if (mounted) {
          setIsBackendHealthy(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Mobile menu toggle & brand */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleMobileMenu}
            className="lg:hidden p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            aria-label="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-700 to-teal-500 flex items-center justify-center text-white shadow-subtle">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold text-slate-900 tracking-tight">MediLens</span>
              <span className="text-lg font-bold text-brand-600 ml-1">AI</span>
              <span className="hidden sm:inline-block ml-2 text-[11px] font-semibold text-slate-500 uppercase tracking-wider bg-slate-100 px-1.5 py-0.5 rounded">
                Clinical Lab Reader
              </span>
            </div>
          </div>
        </div>

        {/* Status badges */}
        <div className="flex items-center gap-3">
          {/* Health indicator */}
          <div
            className={`flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
              isBackendHealthy === true
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : isBackendHealthy === false
                ? 'bg-rose-50 text-rose-700 border-rose-200'
                : 'bg-slate-50 text-slate-500 border-slate-200'
            }`}
            title={
              health
                ? `Backend: ${health.status} | Gemini: ${health.gemini_configured ? 'Configured' : 'Unconfigured'}`
                : 'Checking API health...'
            }
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isBackendHealthy === true
                  ? 'bg-emerald-500'
                  : isBackendHealthy === false
                  ? 'bg-rose-500'
                  : 'bg-slate-400 animate-pulse'
              }`}
            />
            <span className="hidden md:inline">
              {isBackendHealthy === true
                ? 'Backend Online'
                : isBackendHealthy === false
                ? 'Backend Offline'
                : 'Connecting...'}
            </span>
          </div>

          {/* Privacy posture pill */}
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
            <ShieldCheck className="w-3.5 h-3.5 text-brand-600" />
            <span>Zero-Disk PDF Processing</span>
          </div>
        </div>
      </div>
    </header>
  );
};
