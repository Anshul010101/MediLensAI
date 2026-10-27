import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  Lock,
  Sparkles,
  FlaskConical,
} from 'lucide-react';
import { apiService } from '../services/api';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB limit matching backend config

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(0);

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (file: File) => {
    setError(null);

    // Validate mime-type and extension
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setError('Invalid file format. MediLens AI accepts PDF documents only (.pdf).');
      setSelectedFile(null);
      return;
    }

    // Validate size limit (10MB)
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setError(
        `File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds the maximum allowed limit of 10 MB.`
      );
      setSelectedFile(null);
      return;
    }

    if (file.size === 0) {
      setError('The selected PDF file is completely empty (0 bytes).');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || isUploading) return;

    try {
      setIsUploading(true);
      setError(null);
      setCurrentStep(1); // Step 1: Uploading & Text Extraction

      // Trigger actual upload
      const report = await apiService.uploadReport(selectedFile);
      setCurrentStep(2); // Step 2: Deterministic Reference Bounds

      // Short delay for visual feedback before navigation
      setTimeout(() => {
        setCurrentStep(3); // Step 3: Complete
        setTimeout(() => {
          navigate(`/reports/${report.id}`);
        }, 300);
      }, 300);
    } catch (err: any) {
      setError(err.message || 'An unexpected failure occurred while analyzing the document.');
      setCurrentStep(0);
      setIsUploading(false);
    }
  };

  const handleLoadSample = async (sampleType: 'cbc' | 'cmp' | 'glucose' | 'lipid') => {
    try {
      setIsUploading(true);
      setError(null);
      const report = await apiService.loadSyntheticSample(sampleType);
      navigate(`/reports/${report.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to load synthetic sample.');
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Upload Laboratory Report</h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload a routine laboratory report PDF for deterministic analyte extraction, reference range analysis, and plain-language summary.
        </p>
      </div>

      {/* Assessment demonstration advisory banner */}
      <div className="bg-purple-50/80 border border-purple-200 rounded-xl p-4 flex items-start gap-3 text-purple-900 text-sm">
        <FlaskConical className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
        <div>
          <h2 className="font-semibold text-purple-950 text-sm">Assessment Demonstration Notice</h2>
          <p className="text-xs text-purple-800 leading-relaxed mt-0.5">
            For local evaluation, we recommend testing with synthetic laboratory reports. If uploading your own records, note that files are processed in-memory and raw PDFs are never written to disk.
          </p>
        </div>
      </div>

      {error && (
        <Alert type="error" title="Upload Validation Error">
          {error}
        </Alert>
      )}

      {/* Main Upload Dropzone */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-subtle p-6 sm:p-8 space-y-6">
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 sm:p-12 text-center transition-all ${
            dragActive
              ? 'border-brand-500 bg-brand-50/50 scale-[1.01]'
              : 'border-slate-300 hover:border-slate-400 bg-slate-50/40'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileInputChange}
            className="hidden"
            id="pdf-upload-input"
            disabled={isUploading}
          />

          <div className="max-w-md mx-auto space-y-4">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center shadow-subtle">
              <UploadCloud className="w-7 h-7" />
            </div>

            <div className="space-y-1">
              <p className="text-base font-semibold text-slate-800">
                Drag and drop your laboratory PDF here
              </p>
              <p className="text-xs text-slate-500">
                Supports digital PDFs up to 10 MB (CBC, CMP, Lipid Profile, Metabolic Panels)
              </p>
            </div>

            <Button
              type="button"
              variant="outline"
              size="md"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              Browse Local Files
            </Button>
          </div>
        </div>

        {/* Selected File Card */}
        {selectedFile && (
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-4 animate-fade-in">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-lg bg-teal-100 text-teal-800 flex items-center justify-center flex-shrink-0">
                <FileText className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-900 truncate">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-slate-500">
                  {(selectedFile.size / 1024).toFixed(1)} KB &bull; PDF Document
                </p>
              </div>
            </div>

            <Button
              variant="primary"
              size="md"
              onClick={handleUpload}
              isLoading={isUploading}
              disabled={isUploading}
            >
              Process Document
            </Button>
          </div>
        )}

        {/* Step-by-Step Processing Indicator */}
        {isUploading && (
          <div className="p-5 bg-slate-50 rounded-xl border border-slate-200 space-y-4 animate-fade-in">
            <h3 className="text-sm font-bold text-slate-800">Processing Stages</h3>
            <div className="space-y-3">
              {/* Step 1 */}
              <div className="flex items-center gap-3 text-xs">
                {currentStep >= 1 ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border-2 border-slate-300 flex-shrink-0" />
                )}
                <span className={currentStep >= 1 ? 'font-semibold text-slate-900' : 'text-slate-400'}>
                  1. In-memory digital text extraction (PyMuPDF)
                </span>
              </div>

              {/* Step 2 */}
              <div className="flex items-center gap-3 text-xs">
                {currentStep >= 2 ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border-2 border-slate-300 flex-shrink-0" />
                )}
                <span className={currentStep >= 2 ? 'font-semibold text-slate-900' : 'text-slate-400'}>
                  2. Deterministic reference range evaluation & PII/PHI minimization
                </span>
              </div>

              {/* Step 3 */}
              <div className="flex items-center gap-3 text-xs">
                {currentStep >= 3 ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border-2 border-slate-300 flex-shrink-0" />
                )}
                <span className={currentStep >= 3 ? 'font-semibold text-slate-900' : 'text-slate-400'}>
                  3. Plain-language synthesis & questions formulation
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Alternative Synthetic Demonstrations */}
      <div className="bg-slate-50 rounded-2xl border border-slate-200 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Or Try a Verified Synthetic Report
            </h3>
            <p className="text-xs text-slate-500">
              Instant pre-configured panels for immediate assessment with zero upload required.
            </p>
          </div>
          <Sparkles className="w-5 h-5 text-purple-600" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            onClick={() => handleLoadSample('cbc')}
            disabled={isUploading}
            className="p-3 bg-white rounded-xl border border-slate-200 hover:border-brand-500 hover:shadow-subtle text-left transition-all group disabled:opacity-50"
          >
            <span className="text-xs font-bold text-slate-900 group-hover:text-brand-600 block">
              Complete Blood Count
            </span>
            <span className="text-[11px] text-slate-500 mt-1 block">Hemoglobin, Platelets, WBC</span>
          </button>

          <button
            onClick={() => handleLoadSample('cmp')}
            disabled={isUploading}
            className="p-3 bg-white rounded-xl border border-slate-200 hover:border-brand-500 hover:shadow-subtle text-left transition-all group disabled:opacity-50"
          >
            <span className="text-xs font-bold text-slate-900 group-hover:text-brand-600 block">
              Metabolic Panel (CMP)
            </span>
            <span className="text-[11px] text-slate-500 mt-1 block">Elevated Glucose example</span>
          </button>

          <button
            onClick={() => handleLoadSample('lipid')}
            disabled={isUploading}
            className="p-3 bg-white rounded-xl border border-slate-200 hover:border-brand-500 hover:shadow-subtle text-left transition-all group disabled:opacity-50"
          >
            <span className="text-xs font-bold text-slate-900 group-hover:text-brand-600 block">
              Lipid Profile
            </span>
            <span className="text-[11px] text-slate-500 mt-1 block">Cholesterol, HDL, LDL, Trig</span>
          </button>

          <button
            onClick={() => handleLoadSample('glucose')}
            disabled={isUploading}
            className="p-3 bg-white rounded-xl border border-slate-200 hover:border-brand-500 hover:shadow-subtle text-left transition-all group disabled:opacity-50"
          >
            <span className="text-xs font-bold text-slate-900 group-hover:text-brand-600 block">
              Fasting Glucose
            </span>
            <span className="text-[11px] text-slate-500 mt-1 block">Routine metabolic screen</span>
          </button>
        </div>
      </div>

      {/* Privacy Guarantees */}
      <div className="p-4 bg-white rounded-xl border border-slate-200 text-xs text-slate-600 space-y-2">
        <div className="flex items-center gap-2 font-semibold text-slate-800">
          <Lock className="w-4 h-4 text-brand-600" />
          <span>Privacy & Minimization Policy</span>
        </div>
        <p className="leading-relaxed">
          MediLens AI operates entirely in-memory. Raw PDF files and unrestricted document text are never written to disk. If Google Gemini is configured, a strictly minimized, allowlisted payload containing only laboratory test names, numbers, and reference intervals is dispatched. Patient identifiers (names, dates of birth, MRNs, phone numbers) are scrubbed prior to any external transmission.
        </p>
      </div>
    </div>
  );
};
