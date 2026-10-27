import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Download,
  Trash2,
  ArrowLeft,
  Calendar,
  AlertTriangle,
  FileDown,
} from 'lucide-react';
import { apiService } from '../services/api';
import { ReportSummary } from '../types/report';
import { SyntheticBadge, AIStatusBadge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Alert } from '../components/common/Alert';
import { Modal } from '../components/common/Modal';
import { ResultsTable } from '../components/results/ResultsTable';
import { AIExplanationCard } from '../components/results/AIExplanationCard';
import { DoctorQuestionsCard } from '../components/results/DoctorQuestionsCard';
import { EducationalNotesCard } from '../components/results/EducationalNotesCard';

export const ReportResultsPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<ReportSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Export & delete states
  const [exportingPdf, setExportingPdf] = useState(false);
  const [exportingJson, setExportingJson] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (!reportId) {
      setError('No report identifier specified.');
      setLoading(false);
      return;
    }

    let mounted = true;
    apiService
      .getReportById(reportId)
      .then((data) => {
        if (mounted) {
          setReport(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || `Report '${reportId}' could not be located.`);
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [reportId]);

  const handleExport = async (format: 'pdf' | 'json') => {
    if (!reportId) return;
    try {
      if (format === 'pdf') setExportingPdf(true);
      else setExportingJson(true);
      await apiService.downloadExport(reportId, format);
    } catch (err: any) {
      alert(`Export failed: ${err.message || 'Unknown error'}`);
    } finally {
      if (format === 'pdf') setExportingPdf(false);
      else setExportingJson(false);
    }
  };

  const handleDelete = async () => {
    if (!reportId) return;
    try {
      setIsDeleting(true);
      await apiService.deleteReport(reportId);
      setDeleteModalOpen(false);
      navigate('/history');
    } catch (err: any) {
      alert(`Deletion failed: ${err.message || 'Unknown error'}`);
      setIsDeleting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Retrieving structured report findings..." size="lg" className="py-20" />;
  }

  if (error || !report) {
    return (
      <div className="max-w-2xl mx-auto py-12 space-y-4">
        <Alert type="error" title="Report Not Found">
          {error || 'The requested laboratory report was not found in active storage.'}
        </Alert>
        <div className="flex gap-3">
          <Link to="/history">
            <Button variant="outline" icon={<ArrowLeft className="w-4 h-4" />}>
              Back to History
            </Button>
          </Link>
          <Link to="/upload">
            <Button variant="primary">Upload a New Report</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Top Breadcrumb & Action Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <Link to="/history">
            <Button variant="ghost" size="sm" icon={<ArrowLeft className="w-4 h-4" />}>
              History
            </Button>
          </Link>
          <span className="text-slate-300">/</span>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-700 text-sm">{report.filename}</span>
            {report.is_synthetic && <SyntheticBadge />}
          </div>
        </div>

        {/* Export & Actions */}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('pdf')}
            isLoading={exportingPdf}
            icon={<Download className="w-4 h-4" />}
          >
            Export PDF
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('json')}
            isLoading={exportingJson}
            icon={<FileDown className="w-4 h-4" />}
          >
            Export JSON
          </Button>

          <Button
            variant="danger"
            size="sm"
            onClick={() => setDeleteModalOpen(true)}
            icon={<Trash2 className="w-4 h-4" />}
          >
            Delete
          </Button>
        </div>
      </div>

      {/* Report Summary Card Header */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-subtle p-6 sm:p-7 space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900">{report.filename}</h1>
              {report.is_synthetic && <SyntheticBadge />}
              <AIStatusBadge status={report.ai_explanation.status} />
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Uploaded {new Date(report.upload_timestamp).toLocaleString()}</span>
              </span>
              <span>&bull;</span>
              <span className="font-mono text-slate-400">ID: {report.id}</span>
              {report.metadata.page_count > 0 && (
                <>
                  <span>&bull;</span>
                  <span>{report.metadata.page_count} Page(s)</span>
                </>
              )}
            </div>
          </div>

          {/* Quick Metrics Badges */}
          <div className="flex items-center gap-3">
            <div className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-center">
              <span className="text-xs text-slate-500 font-semibold uppercase block">Total</span>
              <span className="text-lg font-bold text-slate-900">{report.total_tests_detected}</span>
            </div>
            <div className="px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
              <span className="text-xs text-emerald-800 font-semibold uppercase block">In-Range</span>
              <span className="text-lg font-bold text-emerald-700">{report.in_range_count}</span>
            </div>
            <div className="px-3 py-2 bg-rose-50 border border-rose-200 rounded-xl text-center">
              <span className="text-xs text-rose-800 font-semibold uppercase block">Out-of-Range</span>
              <span className="text-lg font-bold text-rose-700">{report.out_of_range_count}</span>
            </div>
          </div>
        </div>

        {/* Extraction Warnings if any */}
        {report.metadata.warnings.length > 0 && (
          <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-amber-950">Extraction Warnings: </span>
              <span>{report.metadata.warnings.join('; ')}</span>
            </div>
          </div>
        )}
      </div>

      {/* AI Explanation Section */}
      <AIExplanationCard aiExplanation={report.ai_explanation} />

      {/* Doctor Questions Section */}
      <DoctorQuestionsCard questions={report.ai_explanation.questions_for_doctor} />

      {/* Deterministic Laboratory Findings Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Extracted Laboratory Tests</h2>
            <p className="text-xs text-slate-500">
              Evaluated deterministically against laboratory reference ranges stated in the source document
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {report.tests.length} Analyte(s) detected
          </span>
        </div>

        <ResultsTable tests={report.tests} />
      </div>

      {/* Educational Static Notes */}
      <EducationalNotesCard notes={report.educational_notes} />

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Confirm Report Deletion"
        description="Are you sure you want to delete this report from history?"
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDeleteModalOpen(false)}
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
          This will permanently remove <strong>{report.filename}</strong> (ID: <code>{report.id}</code>) and all of its structured clinical findings from local storage. This action cannot be undone.
        </p>
      </Modal>
    </div>
  );
};
