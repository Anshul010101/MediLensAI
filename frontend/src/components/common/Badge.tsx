import React from 'react';
import {
  CheckCircle2,
  ArrowDown,
  ArrowUp,
  AlertTriangle,
  HelpCircle,
  AlertCircle,
  FlaskConical,
  Bot,
} from 'lucide-react';
import { AIExplanationStatus, FlagStatus } from '../../types/report';

interface BadgeProps {
  children?: React.ReactNode;
  className?: string;
}

export const StatusBadge: React.FC<{ flag: FlagStatus; className?: string }> = ({ flag, className = '' }) => {
  switch (flag) {
    case 'NORMAL':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 ${className}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
          <span>Normal</span>
        </span>
      );
    case 'LOW':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 ${className}`}
        >
          <ArrowDown className="w-3.5 h-3.5 text-amber-600" aria-hidden="true" />
          <span>Below Range (Low)</span>
        </span>
      );
    case 'HIGH':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-200 ${className}`}
        >
          <ArrowUp className="w-3.5 h-3.5 text-rose-600" aria-hidden="true" />
          <span>Above Range (High)</span>
        </span>
      );
    case 'CRITICAL_LOW':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-900 border border-red-300 animate-pulse ${className}`}
        >
          <AlertCircle className="w-3.5 h-3.5 text-red-700" aria-hidden="true" />
          <span>Critical Low</span>
        </span>
      );
    case 'CRITICAL_HIGH':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-900 border border-red-300 animate-pulse ${className}`}
        >
          <AlertCircle className="w-3.5 h-3.5 text-red-700" aria-hidden="true" />
          <span>Critical High</span>
        </span>
      );
    case 'INCONCLUSIVE':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200 ${className}`}
        >
          <HelpCircle className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
          <span>Inconclusive</span>
        </span>
      );
    case 'AMBIGUOUS':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200 ${className}`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" aria-hidden="true" />
          <span>Ambiguous</span>
        </span>
      );
    case 'UNSUPPORTED':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200 ${className}`}
        >
          <HelpCircle className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
          <span>Unsupported</span>
        </span>
      );
  }
};

export const SyntheticBadge: React.FC<BadgeProps> = ({ className = '' }) => (
  <span
    className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200 ${className}`}
    title="Demonstration dataset generated for testing. Contains no real patient information."
  >
    <FlaskConical className="w-3 h-3 text-purple-500" aria-hidden="true" />
    <span>Synthetic Demo</span>
  </span>
);

export const AIStatusBadge: React.FC<{ status: AIExplanationStatus; className?: string }> = ({
  status,
  className = '',
}) => {
  switch (status) {
    case 'completed':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-teal-50 text-teal-700 border border-teal-200 ${className}`}
        >
          <Bot className="w-3.5 h-3.5 text-teal-600" aria-hidden="true" />
          <span>AI Explanation Ready</span>
        </span>
      );
    case 'pending':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-sky-50 text-sky-700 border border-sky-200 ${className}`}
        >
          <span className="w-2 h-2 rounded-full bg-sky-500 animate-ping" />
          <span>AI Explaining...</span>
        </span>
      );
    case 'ai_unavailable':
    case 'failed':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200 ${className}`}
        >
          <Bot className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
          <span>AI Unavailable (Deterministic Only)</span>
        </span>
      );
  }
};
