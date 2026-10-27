import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { DisclaimerBanner } from './DisclaimerBanner';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';

export const Layout: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
      {/* Permanent non-diagnostic banner */}
      <DisclaimerBanner />

      {/* Main navigation header */}
      <Navbar onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)} />

      {/* App Body */}
      <div className="flex-1 max-w-7xl w-full mx-auto flex">
        {/* Navigation Sidebar */}
        <Sidebar
          isMobileOpen={isMobileMenuOpen}
          onCloseMobile={() => setIsMobileMenuOpen(false)}
        />

        {/* Dynamic Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 min-w-0">
          <Outlet />
        </main>
      </div>

      {/* Application Footer */}
      <footer className="bg-white border-t border-slate-200 mt-auto py-6 px-4 sm:px-6 lg:px-8 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-700">MediLens AI</span>
            <span>&bull;</span>
            <span>Clinical Laboratory Communication Aid</span>
          </div>
          <p className="text-center sm:text-right text-[11px] max-w-md text-slate-400">
            MediLens AI does not provide medical diagnoses or treatment recommendations. Always discuss routine lab findings with a licensed healthcare clinician.
          </p>
        </div>
      </footer>
    </div>
  );
};
