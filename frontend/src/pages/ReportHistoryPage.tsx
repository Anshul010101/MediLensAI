import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  History,
  Search,
  Trash2,
  Download,
  Eye,
  ChevronLeft,
  ChevronRight,
  UploadCloud,
  FileDown,
} from 'lucide-react';
import { apiService } from '../services/api';
import { ReportListItem, ReportListResponse } from '../types/report';
import { SyntheticBadge, AIStatusBadge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Alert } from '../components/common/Alert';
import { Modal } from '../components/common/Modal';

export const ReportHistoryPage: React.FC = () => {
  const [reportsData, setReportsData] = useState<ReportListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Pagination
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Delete modal state
  const [selectedDeleteReport, setSelectedDeleteReport] = useState<ReportListItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Debounce search
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setPage(1); // Reset to page 1 on new query
    }, 300);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  const loadReports = (currentPage: number, search: string) => {
    setLoading(true);
    apiService
      .getReports({ page: currentPage, limit: 10, search: search || undefined })
      .then((data) => {
        setReportsData(data);
        setError(null);
      })
      .catch((err) => {
        setError(err.message || 'Failed to retrieve report history.');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    loadReports(page, debouncedSearch);
  }, [page, debouncedSearch]);

  const handleDelete = async () => {
    if (!selectedDeleteReport) return;
    try {
      setIsDeleting(true);
      await apiService.deleteReport(selectedDeleteReport.id);
      setSelectedDeleteReport(null);
      // Reload reports
      loadReports(page, debouncedSearch);
    } catch (err: any) {
      alert(`Deletion failed: ${err.message || 'Unknown error'}`);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleExport = async (reportId: string, format: 'pdf' | 'json') => {
    try {
      await apiService.downloadExport(reportId, format);
    } catch (err: any) {
      alert(`Export failed: ${err.message || 'Unknown error'}`);
    }
  };

  const reports = reportsData?.items || [];
  const total = reportsData?.total || 0;
  const historyEnabled = reportsData?.history_enabled ?? true;
  const totalPages = Math.max(1, Math.ceil(total / 10));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Report History</h1>
          <p className="text-sm text-slate-500 mt-1">
            Access previous laboratory findings, download clinical PDF summaries, or remove stored records.
          </p>
        </div>

        <Link to="/upload">
          <Button variant="primary" icon={<UploadCloud className="w-4 h-4" />}>
            Upload Report
          </Button>
        </Link>
      </div>

      {/* History persistence disabled notice */}
      {!historyEnabled && (
        <Alert type="warning" title="History Storage Disabled">
          The backend history persistence setting is currently disabled (<code>ENABLE_HISTORY_PERSISTENCE=False</code>). Reports are processed ephemerally and will not persist across browser sessions.
        </Alert>
      )}

      {error && (
        <Alert type="error" title="History Retrieval Error">
          {error}
        </Alert>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-subtle flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by filename or Report ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 text-slate-800 placeholder-slate-400"
          />
        </div>
        <span className="text-xs text-slate-500 font-medium">
          Showing {reports.length} of {total} record(s)
        </span>
      </div>

      {/* Reports Table or List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle overflow-hidden">
        {loading ? (
          <LoadingSpinner label="Loading historical reports..." size="md" className="py-16" />
        ) : reports.length === 0 ? (
          <div className="py-16 px-4 text-center space-y-3">
            <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 text-slate-400 flex items-center justify-center">
              <History className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-800">No reports found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {debouncedSearch
                ? `No reports match your search query '${debouncedSearch}'.`
                : 'Your report history is currently empty. Upload a PDF or explore a synthetic sample.'}
            </p>
            <div className="pt-2 flex justify-center gap-3">
              <Link to="/upload">
                <Button variant="primary" size="sm">Upload Report</Button>
              </Link>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold text-xs tracking-wider uppercase">
                  <th scope="col" className="py-3.5 px-5">Report Document</th>
                  <th scope="col" className="py-3.5 px-4">Date Uploaded</th>
                  <th scope="col" className="py-3.5 px-4">Analytes</th>
                  <th scope="col" className="py-3.5 px-4">AI Status</th>
                  <th scope="col" className="py-3.5 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {reports.map((report) => (
                  <tr key={report.id} className="hover:bg-slate-50/60 transition-colors">
                    {/* Filename & synthetic badge */}
                    <td className="py-4 px-5 align-middle">
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/reports/${report.id}`}
                          className="font-semibold text-slate-900 hover:text-brand-600 truncate block max-w-xs"
                        >
                          {report.filename}
                        </Link>
                        {report.is_synthetic && <SyntheticBadge />}
                      </div>
                      <span className="font-mono text-[11px] text-slate-400 block mt-0.5">
                        {report.id}
                      </span>
                    </td>

                    {/* Timestamp */}
                    <td className="py-4 px-4 align-middle text-xs text-slate-600">
                      {new Date(report.upload_timestamp).toLocaleDateString()} at{' '}
                      {new Date(report.upload_timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>

                    {/* Test Counts */}
                    <td className="py-4 px-4 align-middle">
                      <div className="text-xs">
                        <span className="font-semibold text-slate-800">{report.total_tests_detected} tests</span>
                        <div className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1.5">
                          <span className="text-emerald-700 font-medium">{report.in_range_count} normal</span>
                          <span>&bull;</span>
                          <span className={report.out_of_range_count > 0 ? 'text-rose-700 font-medium' : 'text-slate-400'}>
                            {report.out_of_range_count} flagged
                          </span>
                        </div>
                      </div>
                    </td>

                    {/* AI Explanation Status */}
                    <td className="py-4 px-4 align-middle">
                      <AIStatusBadge status={report.ai_status} />
                    </td>

                    {/* Actions */}
                    <td className="py-4 px-5 align-middle text-right">
                      <div className="inline-flex items-center gap-1.5">
                        <Link to={`/reports/${report.id}`}>
                          <Button variant="ghost" size="sm" icon={<Eye className="w-3.5 h-3.5" />}>
                            View
                          </Button>
                        </Link>

                        <button
                          onClick={() => handleExport(report.id, 'pdf')}
                          className="p-1.5 text-slate-500 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors"
                          title="Export PDF Summary"
                        >
                          <Download className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => handleExport(report.id, 'json')}
                          className="p-1.5 text-slate-500 hover:text-brand-600 hover:bg-slate-100 rounded-lg transition-colors"
                          title="Export JSON"
                        >
                          <FileDown className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => setSelectedDeleteReport(report)}
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors ml-1"
                          title="Delete Report"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {total > 10 && (
          <div className="p-4 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
            <span>
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                icon={<ChevronLeft className="w-3.5 h-3.5" />}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                icon={<ChevronRight className="w-3.5 h-3.5" />}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={selectedDeleteReport !== null}
        onClose={() => setSelectedDeleteReport(null)}
        title="Confirm Report Deletion"
        description="Permanently remove this report from stored history"
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedDeleteReport(null)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={handleDelete}
              isLoading={isDeleting}
              disabled={isDeleting}
            >
              Delete Permanently
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600 leading-relaxed">
          Are you sure you want to delete <strong>{selectedDeleteReport?.filename}</strong> (ID: <code>{selectedDeleteReport?.id}</code>)? This action immediately purges the record from SQLite storage.
        </p>
      </Modal>
    </div>
  );
};
