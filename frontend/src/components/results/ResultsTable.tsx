import React, { useState } from 'react';
import { AlertCircle, Filter, Search } from 'lucide-react';
import { TestResult } from '../../types/report';
import { StatusBadge } from '../common/Badge';
import { RangeVisualizer } from './RangeVisualizer';

interface ResultsTableProps {
  tests: TestResult[];
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ tests }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFlag, setSelectedFlag] = useState<string>('ALL');

  const filteredTests = tests.filter((t) => {
    const matchesSearch =
      t.canonical_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.category.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFlag =
      selectedFlag === 'ALL' ||
      (selectedFlag === 'OUT_OF_RANGE' &&
        ['LOW', 'HIGH', 'CRITICAL_LOW', 'CRITICAL_HIGH'].includes(t.flag)) ||
      t.flag === selectedFlag;

    return matchesSearch && matchesFlag;
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-subtle overflow-hidden">
      {/* Table Toolbar */}
      <div className="p-4 sm:p-5 border-b border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search test names or categories..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm bg-white border border-slate-300 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 text-slate-800 placeholder-slate-400"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedFlag}
            onChange={(e) => setSelectedFlag(e.target.value)}
            className="text-sm bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            <option value="ALL">All Results ({tests.length})</option>
            <option value="OUT_OF_RANGE">Out-of-Range Only</option>
            <option value="NORMAL">Normal</option>
            <option value="LOW">Low</option>
            <option value="HIGH">High</option>
            <option value="INCONCLUSIVE">Inconclusive</option>
          </select>
        </div>
      </div>

      {/* Table Body */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold text-xs tracking-wider uppercase">
              <th scope="col" className="py-3.5 px-4 sm:px-6">Test Analyte</th>
              <th scope="col" className="py-3.5 px-4">Result</th>
              <th scope="col" className="py-3.5 px-4">Reference Interval</th>
              <th scope="col" className="py-3.5 px-4">Evaluation</th>
              <th scope="col" className="py-3.5 px-4 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredTests.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-slate-400">
                  No laboratory tests match the current filter criteria.
                </td>
              </tr>
            ) : (
              filteredTests.map((test, index) => (
                <tr
                  key={`${test.canonical_name}-${index}`}
                  className="hover:bg-slate-50/70 transition-colors"
                >
                  {/* Test Name & Category */}
                  <td className="py-4 px-4 sm:px-6 align-top">
                    <div className="font-semibold text-slate-900">{test.canonical_name}</div>
                    <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-2">
                      <span>{test.category}</span>
                      {test.source_page && (
                        <span>&bull; Page {test.source_page}</span>
                      )}
                    </div>
                    {test.uncertainty_notes.length > 0 && (
                      <div className="mt-1.5 flex items-start gap-1 text-[11px] text-amber-700 bg-amber-50/80 px-2 py-1 rounded border border-amber-200">
                        <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                        <span>{test.uncertainty_notes.join(' ')}</span>
                      </div>
                    )}
                  </td>

                  {/* Extracted Value & Unit */}
                  <td className="py-4 px-4 align-top">
                    <span className="font-mono font-bold text-base text-slate-900">
                      {test.value_text}
                    </span>
                    {test.unit && (
                      <span className="ml-1 text-xs text-slate-500 font-medium">
                        {test.unit}
                      </span>
                    )}
                  </td>

                  {/* Stated Reference Range */}
                  <td className="py-4 px-4 align-top">
                    <div className="text-xs text-slate-700 font-medium">
                      {test.reference_interval ? (
                        test.reference_interval.raw_text
                      ) : (
                        <span className="text-slate-400 italic">None stated in report</span>
                      )}
                    </div>
                  </td>

                  {/* Range Visualizer / Evaluation */}
                  <td className="py-4 px-4 align-top min-w-[160px]">
                    <RangeVisualizer test={test} />
                  </td>

                  {/* Status Flag Badge */}
                  <td className="py-4 px-4 align-top text-right">
                    <StatusBadge flag={test.flag} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
