export type FlagStatus =
  | 'NORMAL'
  | 'LOW'
  | 'HIGH'
  | 'INCONCLUSIVE'
  | 'AMBIGUOUS'
  | 'UNSUPPORTED'
  | 'CRITICAL_LOW'
  | 'CRITICAL_HIGH';

export interface ReferenceInterval {
  raw_text: string;
  low?: number | null;
  high?: number | null;
  unit?: string | null;
  is_numeric: boolean;
  comparator?: string | null;
}

export interface TestResult {
  name: string;
  canonical_name: string;
  category: string;
  value_text: string;
  value_numeric?: number | null;
  unit?: string | null;
  reference_interval?: ReferenceInterval | null;
  flag: FlagStatus;
  flag_reason: string;
  source_page?: number | null;
  uncertainty_notes: string[];
  is_synthetic: boolean;
}

export interface ExtractionMetadata {
  page_count: number;
  extracted_character_count: number;
  is_scanned: boolean;
  ocr_applied: boolean;
  ocr_available: boolean;
  warnings: string[];
  processing_time_ms: number;
  is_synthetic: boolean;
}

export interface EducationalContent {
  analyte_name: string;
  source: string;
  physiological_role: string;
  clinical_disclaimer: string;
}

export type AIExplanationStatus =
  | 'ai_unavailable'
  | 'pending'
  | 'completed'
  | 'failed';

export interface AIExplanation {
  status: AIExplanationStatus;
  provider?: string | null;
  model?: string | null;
  summary_text?: string | null;
  per_test_explanations: Record<string, string>;
  limitations_and_uncertainty: string[];
  questions_for_doctor: string[];
  status_reason?: string | null;
  disclaimer: string;
}

export interface ReportSummary {
  id: string;
  filename: string;
  upload_timestamp: string;
  metadata: ExtractionMetadata;
  tests: TestResult[];
  educational_notes: EducationalContent[];
  ai_explanation: AIExplanation;
  total_tests_detected: number;
  in_range_count: number;
  out_of_range_count: number;
  inconclusive_count: number;
  is_synthetic: boolean;
  disclaimer: string;
}

export interface ReportListItem {
  id: string;
  filename: string;
  upload_timestamp: string;
  total_tests_detected: number;
  in_range_count: number;
  out_of_range_count: number;
  inconclusive_count: number;
  is_synthetic: boolean;
  ai_status: AIExplanationStatus;
}

export interface ReportListResponse {
  items: ReportListItem[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
  history_enabled: boolean;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  environment: string;
  ocr_status: {
    ocr_available: boolean;
    binary_path?: string | null;
    engine_version?: string | null;
    warning?: string | null;
  };
  gemini_configured: boolean;
  version: string;
}
