import React from 'react';
import { TestResult } from '../../types/report';

interface RangeVisualizerProps {
  test: TestResult;
}

export const RangeVisualizer: React.FC<RangeVisualizerProps> = ({ test }) => {
  const { value_numeric, reference_interval, unit, flag } = test;

  // Only render visual range bar if we have valid numeric values and a two-sided or single-sided numeric interval
  if (
    value_numeric == null ||
    !reference_interval ||
    !reference_interval.is_numeric
  ) {
    return (
      <span className="text-xs text-slate-400 italic">
        {reference_interval?.raw_text || 'No numeric range'}
      </span>
    );
  }

  const { low, high } = reference_interval;

  // Case 1: Two-sided range [low, high]
  if (low != null && high != null && high > low) {
    const rangeSpan = high - low;
    // Buffer margins on either side for display
    const buffer = rangeSpan * 0.25;
    const minScale = Math.max(0, low - buffer);
    const maxScale = high + buffer;
    const totalScale = maxScale - minScale;

    // Calculate percentage positions
    const lowPct = Math.max(0, Math.min(100, ((low - minScale) / totalScale) * 100));
    const highPct = Math.max(0, Math.min(100, ((high - minScale) / totalScale) * 100));
    const valPct = Math.max(0, Math.min(100, ((value_numeric - minScale) / totalScale) * 100));

    const isNormal = flag === 'NORMAL';
    const isLow = flag === 'LOW' || flag === 'CRITICAL_LOW';

    const pinColor = isNormal
      ? 'bg-emerald-600 text-white'
      : isLow
      ? 'bg-amber-600 text-white'
      : 'bg-rose-600 text-white';

    return (
      <div className="w-full max-w-xs space-y-1">
        {/* Visual Bar */}
        <div className="relative h-2 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-200">
          {/* Normal Zone */}
          <div
            className="absolute top-0 bottom-0 bg-emerald-100 border-x border-emerald-300"
            style={{ left: `${lowPct}%`, width: `${highPct - lowPct}%` }}
            title={`Normal Range: ${low} - ${high} ${unit || ''}`}
          />
        </div>

        {/* Marker & Scale Labels */}
        <div className="relative h-5 text-[11px] text-slate-500">
          {/* Lower bound label */}
          <span
            className="absolute top-0 transform -translate-x-1/2 text-slate-400"
            style={{ left: `${lowPct}%` }}
          >
            {low}
          </span>
          {/* Upper bound label */}
          <span
            className="absolute top-0 transform -translate-x-1/2 text-slate-400"
            style={{ left: `${highPct}%` }}
          >
            {high}
          </span>
          {/* Patient Value Pin */}
          <div
            className={`absolute top-0 transform -translate-x-1/2 px-1 rounded text-[10px] font-bold shadow-subtle ${pinColor}`}
            style={{ left: `${valPct}%` }}
            title={`Your result: ${value_numeric} ${unit || ''}`}
          >
            {value_numeric}
          </div>
        </div>
      </div>
    );
  }

  // Case 2: Single-sided bound (e.g. < 100 or > 60)
  if (reference_interval.comparator) {
    return (
      <div className="text-xs text-slate-600">
        <span>Stated: </span>
        <span className="font-semibold">{reference_interval.raw_text}</span>
        {unit && <span className="ml-1 text-slate-400">{unit}</span>}
      </div>
    );
  }

  return (
    <span className="text-xs text-slate-500 font-medium">
      {reference_interval.raw_text}
    </span>
  );
};
