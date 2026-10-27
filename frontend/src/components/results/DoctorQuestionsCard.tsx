import React, { useState } from 'react';
import { HelpCircle, Copy, Check, MessageSquare } from 'lucide-react';

interface DoctorQuestionsCardProps {
  questions: string[];
}

export const DoctorQuestionsCard: React.FC<DoctorQuestionsCardProps> = ({ questions }) => {
  const [copied, setCopied] = useState(false);

  if (!questions || questions.length === 0) {
    return null;
  }

  const handleCopy = () => {
    const textToCopy = questions.map((q, i) => `${i + 1}. ${q}`).join('\n');
    navigator.clipboard.writeText(textToCopy).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-subtle p-5 sm:p-6 space-y-4">
      <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-indigo-50 text-indigo-700 rounded-lg">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Questions for Your Healthcare Provider
            </h3>
            <p className="text-xs text-slate-500">
              Personalized topics to discuss during your next clinical appointment
            </p>
          </div>
        </div>

        <button
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          title="Copy questions to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-emerald-700 font-semibold">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy All</span>
            </>
          )}
        </button>
      </div>

      <div className="space-y-2.5">
        {questions.map((question, index) => (
          <div
            key={index}
            className="flex items-start gap-3 p-3 bg-slate-50/70 rounded-lg border border-slate-200/80 text-sm text-slate-800"
          >
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-800 font-semibold text-xs flex items-center justify-center">
              {index + 1}
            </span>
            <p className="leading-relaxed mt-0.5">{question}</p>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-500 pt-2">
        <HelpCircle className="w-4 h-4 text-slate-400 flex-shrink-0" />
        <span>
          Tip: Bring this list along with previous annual lab reports to help your clinician evaluate historical trends.
        </span>
      </div>
    </div>
  );
};
