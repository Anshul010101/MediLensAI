import React from 'react';
import { ShieldAlert } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <div className="bg-amber-50/80 border-b border-amber-200/80 px-4 py-2.5 text-xs text-amber-900">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-700 flex-shrink-0" aria-hidden="true" />
          <span>
            <strong className="font-semibold text-amber-950">Informational Support Only:</strong> MediLens AI provides
            plain-language context for routine lab results. It is <em>not</em> a medical diagnostic, prognostic, or
            treatment-prescribing system. Always consult a qualified physician for clinical decisions.
          </span>
        </div>
        <span className="hidden sm:inline-block px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-medium text-[11px] whitespace-nowrap">
          Assessment Demo
        </span>
      </div>
    </div>
  );
};
