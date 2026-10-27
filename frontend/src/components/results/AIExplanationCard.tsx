import React from 'react';
import { Bot, Sparkles, AlertTriangle, ShieldCheck } from 'lucide-react';
import { AIExplanation } from '../../types/report';

interface AIExplanationCardProps {
  aiExplanation: AIExplanation;
}

export const AIExplanationCard: React.FC<AIExplanationCardProps> = ({ aiExplanation }) => {
  const isCompleted = aiExplanation.status === 'completed';

  if (!isCompleted) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 text-slate-700">
        <div className="flex items-start gap-3">
          <div className="p-2.5 bg-slate-200 rounded-lg text-slate-600 flex-shrink-0">
            <Bot className="w-5 h-5" />
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-slate-900">
                AI Narrative Explanation: Offline / Unavailable
              </h3>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-200 text-slate-700">
                Deterministic Processing Active
              </span>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">
              {aiExplanation.status_reason ||
                'Google Gemini is unconfigured or unavailable in this environment. Deterministic analyte extraction, reference intervals, and flag evaluations remain 100% active and clinically intact.'}
            </p>
            <div className="flex items-center gap-2 text-xs text-slate-500 pt-1">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>
                Zero clinical data was fabricated. All findings in the table above are derived solely from laboratory document text.
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-teal-200 rounded-xl shadow-subtle overflow-hidden">
      {/* Card Header */}
      <div className="bg-gradient-to-r from-teal-500/10 to-brand-500/10 p-5 border-b border-teal-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-brand-600 text-white rounded-lg shadow-subtle">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Plain-Language AI Educational Summary
            </h3>
            <p className="text-xs text-slate-500">
              Generated via {aiExplanation.provider || 'Google Gemini'}{' '}
              {aiExplanation.model && `(${aiExplanation.model})`} from pre-sanitized clinical data
            </p>
          </div>
        </div>
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-100 text-teal-800">
          Non-Diagnostic
        </span>
      </div>

      {/* Card Body */}
      <div className="p-5 sm:p-6 space-y-5">
        {/* Main Summary Narrative */}
        {aiExplanation.summary_text && (
          <div className="text-sm sm:text-base text-slate-800 leading-relaxed space-y-3">
            <p className="font-medium text-slate-900">{aiExplanation.summary_text}</p>
          </div>
        )}

        {/* Per-analyte plain-language explanations */}
        {aiExplanation.per_test_explanations &&
          Object.keys(aiExplanation.per_test_explanations).length > 0 && (
            <div className="pt-3 border-t border-slate-100">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                Analyte Insights
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(aiExplanation.per_test_explanations).map(([name, note]) => (
                  <div
                    key={name}
                    className="p-3 bg-slate-50 rounded-lg border border-slate-200/80 text-xs leading-relaxed"
                  >
                    <span className="font-semibold text-slate-900 block mb-1">{name}</span>
                    <span className="text-slate-600">{note}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

        {/* Limitations and Uncertainty Notices */}
        {aiExplanation.limitations_and_uncertainty &&
          aiExplanation.limitations_and_uncertainty.length > 0 && (
            <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900 space-y-1">
              <div className="flex items-center gap-1.5 font-semibold text-amber-950">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Interpretation Caveats & Uncertainties</span>
              </div>
              <ul className="list-disc list-inside space-y-0.5 text-amber-800 pl-1">
                {aiExplanation.limitations_and_uncertainty.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

        {/* Model Disclaimer */}
        <div className="text-[11px] text-slate-400 border-t border-slate-100 pt-3">
          {aiExplanation.disclaimer}
        </div>
      </div>
    </div>
  );
};
