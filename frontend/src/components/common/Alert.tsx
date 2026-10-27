import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle, Info } from 'lucide-react';

export type AlertType = 'info' | 'warning' | 'error' | 'success';

interface AlertProps {
  type?: AlertType;
  title?: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export const Alert: React.FC<AlertProps> = ({
  type = 'info',
  title,
  children,
  className = '',
  action,
}) => {
  const styles: Record<AlertType, { container: string; icon: React.ReactNode; titleColor: string }> = {
    info: {
      container: 'bg-teal-50 border-teal-200 text-teal-900',
      icon: <Info className="w-5 h-5 text-teal-600 flex-shrink-0 mt-0.5" aria-hidden="true" />,
      titleColor: 'text-teal-950 font-semibold',
    },
    warning: {
      container: 'bg-amber-50 border-amber-200 text-amber-900',
      icon: <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" aria-hidden="true" />,
      titleColor: 'text-amber-950 font-semibold',
    },
    error: {
      container: 'bg-rose-50 border-rose-200 text-rose-900',
      icon: <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" aria-hidden="true" />,
      titleColor: 'text-rose-950 font-semibold',
    },
    success: {
      container: 'bg-emerald-50 border-emerald-200 text-emerald-900',
      icon: <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" aria-hidden="true" />,
      titleColor: 'text-emerald-950 font-semibold',
    },
  };

  const current = styles[type];

  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-xl border text-sm leading-relaxed ${current.container} ${className}`}
      role="alert"
    >
      {current.icon}
      <div className="flex-1">
        {title && <h4 className={`text-sm mb-1 ${current.titleColor}`}>{title}</h4>}
        <div className="opacity-90">{children}</div>
      </div>
      {action && <div className="flex-shrink-0 ml-2">{action}</div>}
    </div>
  );
};
