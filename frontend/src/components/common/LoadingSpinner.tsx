import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Loading...',
  size = 'md',
  className = '',
}) => {
  const sizeMap = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-10 h-10',
  };

  return (
    <div
      className={`flex flex-col items-center justify-center p-8 gap-3 text-slate-500 ${className}`}
      role="status"
      aria-live="polite"
    >
      <Loader2 className={`${sizeMap[size]} animate-spin text-brand-600`} aria-hidden="true" />
      {label && <span className="text-sm font-medium">{label}</span>}
      <span className="sr-only">{label}</span>
    </div>
  );
};
