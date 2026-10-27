import React, { useEffect, useState } from 'react';
import {
  Shield,
  ShieldAlert,
  Server,
  Bot,
  Database,
  Lock,
  Info,
  RefreshCw,
} from 'lucide-react';
import { apiService } from '../services/api';
import { HealthResponse } from '../types/report';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';

export const PrivacySettingsPage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [historyEnabled, setHistoryEnabled] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = () => {
    setLoading(true);
    Promise.all([
      apiService.getHealth(),
      apiService.getReports({ page: 1, limit: 1 }),
    ])
      .then(([healthData, reportsData]) => {
        setHealth(healthData);
        setHistoryEnabled(reportsData.history_enabled);
        setError(null);
      })
      .catch((err) => {
        setError(err.message || 'Failed to query backend system parameters.');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Privacy Architecture & System Settings
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Audit verifiable runtime privacy configurations, external AI boundaries, and local storage limits.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchStatus}
          isLoading={loading}
          icon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh Status
        </Button>
      </div>

      {error && (
        <Alert type="error" title="Backend Connection Notice">
          {error}
        </Alert>
      )}

      {/* Live System Configuration Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Backend Status */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-subtle space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">FastAPI Core</span>
            <Server className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                health?.status === 'healthy' ? 'bg-emerald-500' : 'bg-slate-300'
              }`}
            />
            <span className="text-base font-bold text-slate-900 capitalize">
              {health ? health.status : 'Connecting...'}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            {health ? `Environment: ${health.environment} (v${health.version})` : 'Target: http://127.0.0.1:8000'}
          </p>
        </div>

        {/* Gemini API Status */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-subtle space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Gemini 2.5 SDK</span>
            <Bot className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                health?.gemini_configured ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
            />
            <span className="text-base font-bold text-slate-900">
              {health?.gemini_configured ? 'Configured' : 'Unconfigured'}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            {health?.gemini_configured
              ? 'Official google-genai SDK connected'
              : 'Deterministic-only fallback active'}
          </p>
        </div>

        {/* History Storage Status */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-subtle space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Storage Layer</span>
            <Database className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                historyEnabled ? 'bg-emerald-500' : 'bg-slate-400'
              }`}
            />
            <span className="text-base font-bold text-slate-900">
              {historyEnabled ? 'SQLite Active' : 'Ephemeral Mode'}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            {historyEnabled
              ? 'Local structured reports persisted'
              : 'Zero disk persistence enabled'}
          </p>
        </div>
      </div>

      {/* Core Privacy Assurances */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-subtle p-6 sm:p-7 space-y-6">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Privacy & Data Handling Principles</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Architectural guarantees implemented across MediLens AI
          </p>
        </div>

        <div className="space-y-4">
          {/* Principle 1 */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-start gap-3.5">
            <div className="p-2 bg-teal-100 text-teal-800 rounded-lg flex-shrink-0 mt-0.5">
              <Lock className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-slate-900">Zero Raw PDF Disk Persistence</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                When you upload a laboratory PDF document, it is read directly into volatile memory (RAM) via streaming buffers. PyMuPDF extracts digital text and tabular structures in memory. Raw document bytes and full unscrubbed OCR text are completely discarded post-parsing and are never written to server storage.
              </p>
            </div>
          </div>

          {/* Principle 2 */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-start gap-3.5">
            <div className="p-2 bg-indigo-100 text-indigo-800 rounded-lg flex-shrink-0 mt-0.5">
              <Shield className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-slate-900">Pre-LLM Minimization & Scrubbing</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Before any external request is dispatched to Google Gemini, the <code>PrivacySanitizer</code> layer strips direct identifiers including patient names, dates of birth, medical record numbers (MRNs), phone numbers, email addresses, and postal addresses. Only canonical analyte names, numeric values, units, and stated laboratory reference intervals are sent.
              </p>
            </div>
          </div>

          {/* Principle 3: Limitation disclosure */}
          <div className="p-4 bg-amber-50/70 rounded-xl border border-amber-200 flex items-start gap-3.5">
            <div className="p-2 bg-amber-100 text-amber-800 rounded-lg flex-shrink-0 mt-0.5">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-amber-950">
                Anonymity Guarantee Disclaimer
              </h3>
              <p className="text-xs text-amber-900 leading-relaxed">
                While automated PII/PHI minimization significantly reduces data exposure, sanitization algorithms cannot guarantee 100% mathematical anonymity in the presence of rare biometric markers or atypical header formats. For this reason, users evaluating MediLens AI during assessment should strictly utilize synthetic demonstration reports.
              </p>
            </div>
          </div>

          {/* Principle 4: Local Storage limitations */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-start gap-3.5">
            <div className="p-2 bg-purple-100 text-purple-800 rounded-lg flex-shrink-0 mt-0.5">
              <Database className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-slate-900">
                Single-User Assessment Storage Limitations
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                The local SQLite history database (<code>medilens_history.db</code>) does not implement column-level encryption-at-rest or multi-user tenant isolation. In this local demonstration build, reports are visible to any operator with direct filesystem access. For multi-user public deployment, enterprise access controls, TLS, and encrypted databases are required.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Backend Settings Note */}
      <div className="p-5 bg-white rounded-xl border border-slate-200 shadow-subtle flex items-start gap-3 text-xs text-slate-500">
        <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Configuration Note:</strong> Backend settings (such as <code>ENABLE_HISTORY_PERSISTENCE</code>, <code>GEMINI_MODEL</code>, and <code>MAX_UPLOAD_SIZE_MB</code>) are managed directly via environment variables in <code>backend/.env</code>. MediLens AI does not expose mock frontend toggles for settings that require server-level restarts.
        </p>
      </div>
    </div>
  );
};
