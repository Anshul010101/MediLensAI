import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp } from 'lucide-react';
import { EducationalContent } from '../../types/report';

interface EducationalNotesCardProps {
  notes: EducationalContent[];
}

export const EducationalNotesCard: React.FC<EducationalNotesCardProps> = ({ notes }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!notes || notes.length === 0) {
    return null;
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-subtle overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 sm:p-5 text-left flex items-center justify-between hover:bg-slate-50/50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-slate-100 text-slate-700 rounded-lg">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              Deterministic Biological Reference Guide ({notes.length} Analytes)
            </h3>
            <p className="text-xs text-slate-500">
              Static medical knowledge explaining physiological roles from verified clinical sources
            </p>
          </div>
        </div>

        <div className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg">
          {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </div>
      </button>

      {isOpen && (
        <div className="p-5 border-t border-slate-100 bg-slate-50/30 space-y-3.5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {notes.map((note) => (
              <div
                key={note.analyte_name}
                className="p-3.5 bg-white rounded-lg border border-slate-200 shadow-subtle space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm text-slate-900">{note.analyte_name}</span>
                  <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                    Verified Source
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{note.physiological_role}</p>
                <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-100">
                  Source: {note.source}
                </div>
              </div>
            ))}
          </div>

          <div className="text-[11px] text-slate-400 italic pt-2">
            Deterministic Knowledge Base content is strictly independent of AI generation and validated against clinical literature.
          </div>
        </div>
      )}
    </div>
  );
};
