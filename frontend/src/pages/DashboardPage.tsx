import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FlaskConical,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  TrendingUp,
  Clock,
  Sparkles,
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { apiService } from '../services/api';
import { ReportListItem, ReportListResponse } from '../types/report';
import { SyntheticBadge, AIStatusBadge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Alert } from '../components/common/Alert';
import { Modal } from '../components/common/Modal';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reportsData, setReportsData] = useState<ReportListResponse | null>(null);
  const [sampleModalOpen, setSampleModalOpen] = useState(false);
  const [loadingSample, setLoadingSample] = useState(false);

  useEffect(() => {
    let mounted = true;
    apiService
      .getReports({ page: 1, limit: 10 })
      .then((data) => {
        if (mounted) {
          setReportsData(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || 'Failed to load report history');
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const handleLoadSample = async (sampleType: 'cbc' | 'cmp' | 'glucose' | 'lipid') => {
    try {
      setLoadingSample(true);
      const report = await apiService.loadSyntheticSample(sampleType);
      setSampleModalOpen(false);
      navigate(`/reports/${report.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to load synthetic demonstration report');
    } finally {
      setLoadingSample(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading MediLens AI dashboard..." size="lg" className="py-20" />;
  }

  const reports: ReportListItem[] = reportsData?.items || [];
  const totalReports = reportsData?.total || 0;
  const historyEnabled = reportsData?.history_enabled ?? true;

  // Aggregate metrics derived purely from actual reports returned by backend
  const totalTests = reports.reduce((acc, r) => acc + r.total_tests_detected, 0);
  const totalInRange = reports.reduce((acc, r) => acc + r.in_range_count, 0);
  const totalOutOfRange = reports.reduce((acc, r) => acc + r.out_of_range_count, 0);
  const totalInconclusive = reports.reduce((acc, r) => acc + r.inconclusive_count, 0);

  // Chart data
  const chartData = [
    { name: 'In-Range', value: totalInRange, color: '#059669' },
    { name: 'Out-of-Range', value: totalOutOfRange, color: '#e11d48' },
    { name: 'Inconclusive', value: totalInconclusive, color: '#94a3b8' },
  ].filter((d) => d.value > 0);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero Welcome Header */}
      <div className="bg-gradient-to-br from-slate-900 via-navy-900 to-slate-800 text-white rounded-2xl p-6 sm:p-8 shadow-elevated relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-brand-600/20 to-transparent pointer-events-none" />
        <div className="max-w-2xl space-y-3 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Deterministic Clinical Parsing & Zero-Disk Processing</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Understand Laboratory Findings with Clarity
          </h1>
          <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
            MediLens AI extracts numerical lab values, evaluates them deterministically against stated reference ranges, and translates complex medical metrics into plain language.
          </p>

          <div className="pt-3 flex flex-wrap items-center gap-3">
            <Link to="/upload">
              <Button variant="primary" size="lg" icon={<UploadCloud className="w-5 h-5" />}>
                Upload Lab Report
              </Button>
            </Link>
            <Button
              variant="outline"
              size="lg"
              className="bg-white/10 hover:bg-white/20 text-white border-white/20 hover:border-white/30"
              icon={<FlaskConical className="w-5 h-5 text-purple-300" />}
              onClick={() => setSampleModalOpen(true)}
            >
              Try Synthetic Demo
            </Button>
          </div>
        </div>
      </div>

      {/* History disabled banner if applicable */}
      {!historyEnabled && (
        <Alert type="warning" title="History Persistence Disabled">
          The backend is configured with history persistence disabled (<code>ENABLE_HISTORY_PERSISTENCE=False</code>). Reports are parsed ephemerally in memory and will not appear in this list after navigating away.
        </Alert>
      )}

      {error && (
        <Alert type="error" title="Backend Error">
          {error}
        </Alert>
      )}

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Reports */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-subtle flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Reports In History</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{totalReports}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center text-slate-600">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        {/* Tests Reviewed */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-subtle flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Analytes Extracted</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{totalTests}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-teal-50 flex items-center justify-center text-teal-700">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>

        {/* In-Range Results */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-subtle flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Within Reference</p>
            <p className="text-2xl font-bold text-emerald-700 mt-1">{totalInRange}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-700">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        {/* Out-of-Range Results */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-subtle flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Outside Reference</p>
            <p className="text-2xl font-bold text-rose-700 mt-1">{totalOutOfRange}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-50 flex items-center justify-center text-rose-700">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Main Content Grid: Recent Reports & Analytics Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Reports List (2 cols on lg) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-subtle overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-500" />
              <h2 className="text-base font-bold text-slate-900">Recent Lab Analyses</h2>
            </div>
            {reports.length > 0 && (
              <Link
                to="/history"
                className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1"
              >
                <span>View All</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            )}
          </div>

          {reports.length === 0 ? (
            <div className="p-8 text-center space-y-3">
              <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 text-slate-400 flex items-center justify-center">
                <FileText className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-700">No reports recorded yet</p>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  Upload a digital lab report PDF or launch an instant synthetic demonstration to explore results.
                </p>
              </div>
              <div className="pt-2 flex justify-center gap-3">
                <Link to="/upload">
                  <Button variant="primary" size="sm">Upload Report</Button>
                </Link>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSampleModalOpen(true)}
                >
                  Load Synthetic Demo
                </Button>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {reports.slice(0, 5).map((report) => (
                <div
                  key={report.id}
                  className="p-4 sm:px-5 hover:bg-slate-50/80 transition-colors flex items-center justify-between gap-4"
                >
                  <div className="min-w-0 space-y-1">
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/reports/${report.id}`}
                        className="font-semibold text-sm text-slate-900 hover:text-brand-600 truncate block"
                      >
                        {report.filename}
                      </Link>
                      {report.is_synthetic && <SyntheticBadge />}
                    </div>
                    <div className="text-xs text-slate-400 flex items-center gap-3">
                      <span>{new Date(report.upload_timestamp).toLocaleDateString()}</span>
                      <span>&bull;</span>
                      <span>{report.total_tests_detected} tests</span>
                      <span>&bull;</span>
                      <span className="text-emerald-700 font-medium">{report.in_range_count} normal</span>
                      {report.out_of_range_count > 0 && (
                        <>
                          <span>&bull;</span>
                          <span className="text-rose-700 font-medium">{report.out_of_range_count} flagged</span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <AIStatusBadge status={report.ai_status} />
                    <Link to={`/reports/${report.id}`}>
                      <Button variant="ghost" size="sm" icon={<ArrowRight className="w-4 h-4" />}>
                        View
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Deterministic Distribution Visualization */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-5 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 mb-1">Results Distribution</h2>
            <p className="text-xs text-slate-500 mb-4">
              Aggregate deterministic bounds evaluation across active reports
            </p>

            {chartData.length === 0 ? (
              <div className="h-48 flex items-center justify-center text-xs text-slate-400 italic text-center p-4">
                No laboratory tests analyzed yet. Upload a report to see range metrics.
              </div>
            ) : (
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={75}
                      paddingAngle={3}
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(val: any, name: any) => [`${val} tests`, name]}
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderColor: '#e2e8f0',
                        borderRadius: '0.5rem',
                        fontSize: '12px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-100 grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2 rounded bg-emerald-50 text-emerald-800">
              <span className="block font-bold text-sm">{totalInRange}</span>
              <span className="text-[11px] text-emerald-600">Normal</span>
            </div>
            <div className="p-2 rounded bg-rose-50 text-rose-800">
              <span className="block font-bold text-sm">{totalOutOfRange}</span>
              <span className="text-[11px] text-rose-600">Flagged</span>
            </div>
            <div className="p-2 rounded bg-slate-100 text-slate-700">
              <span className="block font-bold text-sm">{totalInconclusive}</span>
              <span className="text-[11px] text-slate-500">Other</span>
            </div>
          </div>
        </div>
      </div>

      {/* Synthetic Demonstration Selection Modal */}
      <Modal
        isOpen={sampleModalOpen}
        onClose={() => setSampleModalOpen(false)}
        title="Select Synthetic Lab Report"
        description="Choose a verified pre-parsed demonstration panel to inspect MediLens AI without uploading personal health files."
      >
        <div className="space-y-3 pt-2">
          <button
            onClick={() => handleLoadSample('cbc')}
            disabled={loadingSample}
            className="w-full p-3.5 text-left rounded-xl border border-slate-200 hover:border-brand-500 hover:bg-brand-50/40 transition-all flex items-start gap-3 group"
          >
            <div className="p-2 rounded-lg bg-teal-50 text-teal-700 group-hover:bg-brand-500 group-hover:text-white transition-colors">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-sm text-slate-900">Complete Blood Count (CBC)</h4>
              <p className="text-xs text-slate-500 mt-0.5">
                Evaluates red cells, hemoglobin, white blood cell count, and platelets.
              </p>
            </div>
          </button>

          <button
            onClick={() => handleLoadSample('cmp')}
            disabled={loadingSample}
            className="w-full p-3.5 text-left rounded-xl border border-slate-200 hover:border-brand-500 hover:bg-brand-50/40 transition-all flex items-start gap-3 group"
          >
            <div className="p-2 rounded-lg bg-amber-50 text-amber-700 group-hover:bg-brand-500 group-hover:text-white transition-colors">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-sm text-slate-900">Comprehensive Metabolic Panel (CMP)</h4>
              <p className="text-xs text-slate-500 mt-0.5">
                Features elevated Glucose (106 mg/dL) demonstrating out-of-range detection.
              </p>
            </div>
          </button>

          <button
            onClick={() => handleLoadSample('lipid')}
            disabled={loadingSample}
            className="w-full p-3.5 text-left rounded-xl border border-slate-200 hover:border-brand-500 hover:bg-brand-50/40 transition-all flex items-start gap-3 group"
          >
            <div className="p-2 rounded-lg bg-purple-50 text-purple-700 group-hover:bg-brand-500 group-hover:text-white transition-colors">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-sm text-slate-900">Lipid Cardiovascular Profile</h4>
              <p className="text-xs text-slate-500 mt-0.5">
                Cholesterol, HDL, LDL, and Triglycerides with single-sided reference bounds (&lt;200).
              </p>
            </div>
          </button>

          <button
            onClick={() => handleLoadSample('glucose')}
            disabled={loadingSample}
            className="w-full p-3.5 text-left rounded-xl border border-slate-200 hover:border-brand-500 hover:bg-brand-50/40 transition-all flex items-start gap-3 group"
          >
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700 group-hover:bg-brand-500 group-hover:text-white transition-colors">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-sm text-slate-900">Fasting Plasma Glucose</h4>
              <p className="text-xs text-slate-500 mt-0.5">
                Routine metabolic screening analyte with standard reference intervals.
              </p>
            </div>
          </button>
        </div>
      </Modal>
    </div>
  );
};
