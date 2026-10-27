# MediLens AI — Prompt & Development Log

This document records the exact progression of prompts, architecture decisions, implementation steps, testing outcomes, and debugging activities.

---

## Prompt 01: Foundation and Architecture

- **Date**: 2026-10-26
- **Status**: Completed (Architecture Proposed & Awaiting User Review)
- **Objective**: Establish the technical architecture, directory structure, API contracts, deterministic processing pipeline, AI integration design, privacy/security guardrails, and phased implementation plan for MediLens AI.

### Actions Taken
1. **Workspace Inspection**:
   - Inspected `c:\Users\happy\Downloads\medilens-ai`. Workspace was completely empty.
   - Verified system toolchain: Python 3.9.13, Node.js v26.4.0, npm 11.17.0.
   - Identified that Tesseract OCR is not installed in the default system PATH. Designed architecture with PyMuPDF as the primary digital text extraction engine, with an optional/graceful fallback to Tesseract OCR when available.
2. **Architecture Formulation**:
   - Proposed modular monorepo structure with decoupled React + TypeScript + Tailwind frontend and FastAPI + Pydantic backend.
   - Formulated strict separation between deterministic lab test extraction/reference range logic and non-diagnostic LLM explanation.
   - Formulated privacy layer: pre-LLM PII/PHI sanitization, ephemeral file handling, no raw health data logging.
   - Outlined 5 required core application pages: Dashboard, Upload, Results, History, Privacy & Settings.
   - Outlined full REST API specification and test plan.
3. **Phased Implementation Plan**:
   - Phase 1: Architecture, Scaffolding & Documentation Baseline (Current).
   - Phase 2: Backend Core & Deterministic Processing Engine.
   - Phase 3: Gemini AI Integration & Privacy Guardrails.
   - Phase 4: FastAPI REST API & Export Engine.
   - Phase 5: Frontend Design System & Scaffold (React + Vite + Tailwind + Lucide + Recharts).
   - Phase 6: Five Core Application Pages & Interactive Flows.
   - Phase 7: End-to-End Testing, Synthetic Data Verification & Presentation Materials.

### Status
- Approved with modifications (recorded in Prompt 02).

---

## Prompt 02: Approve Architecture and Implement Backend Core

- **Date**: 2026-10-26
- **Status**: Completed & Verified (29 of 29 Tests Passing)
- **Objective**: Implement Phase 2: FastAPI application foundation, configuration management, in-memory PDF extraction with PyMuPDF, optional Tesseract OCR detection, deterministic laboratory parsing for common panels (CBC, CMP, Glucose, Lipid, Thyroid), deterministic reference-range comparison, synthetic sample data generation, privacy-safe logging, and automated test suite.

### Architecture Corrections Incorporated
1. **Python Environment**: Checked available runtimes. Python 3.13.13 (64-bit) was detected via `py -3.13` and selected for the virtual environment (`backend/venv`). Python 3.11 and 3.12 were not present on this machine.
2. **Current `google-genai` SDK and Valid Model**: Verified target model identifier `gemini-2.5-flash` and structured schema to use official Google GenAI SDK in Phase 3.
3. **No Inferred Critical Status**: Removed any automatic inference of `CRITICAL` flags; results are classified strictly as `NORMAL`, `LOW`, `HIGH`, or `INCONCLUSIVE` against stated reference intervals. `CRITICAL_LOW`/`CRITICAL_HIGH` reserved solely for verified source-supported panic values.
4. **Data Minimization & Synthetic Datasets**: All test cases and demo reports use synthetic datasets; uploaded PDFs are processed in-memory without disk persistence.
5. **Explicit AI Status**: If Gemini is unconfigured or unavailable, response models return `AIExplanationStatus.AI_UNAVAILABLE` rather than silently fabricating or substituting generated text.
6. **Separation of Educational Content**: Static biological analyte descriptions come from a deterministic knowledge base and are stored separately in `educational_notes`, explicitly labeled by source.
7. **Ephemeral PDF Processing**: Raw PDF files and extracted text are held in memory during processing and discarded.
8. **Documentation Verification**: Verified existence of all documentation files before editing.

### Commands Run
- `py -3.13 -m venv backend/venv`: Successfully created Python 3.13 virtual environment.
- `.\backend\venv\Scripts\pip install -r .\backend\requirements.txt`: Successfully installed FastAPI 0.162.0, Pydantic 2.14.1, PyMuPDF 2.0.0, Pillow 13.0.0, ReportLab 5.1.0, Pytest 9.1.1, HTTPX 0.28.1, etc.
- `.\backend\venv\Scripts\python.exe .\backend\sample_reports\generate_samples.py`: Successfully generated synthetic CBC, CMP, Lipid, and Thyroid PDF reports.
- `.\backend\venv\Scripts\pytest .\backend\tests -v`: Initial run executed 29 tests (27 passed, 2 failed).

### Failures Detected & Resolved
1. **`test_extract_empty_pdf`**: `fitz.open().tobytes()` failed with `ValueError: cannot save with zero pages` because PyMuPDF prevents writing zero-page PDFs from scratch.
   - *Resolution*: Replaced with a valid raw PDF container binary (`ZERO_PAGE_PDF`) with `/Count 0`. PyMuPDF parses it as 0 pages and `pdf_extractor.extract_from_bytes` cleanly raises `EmptyPDFError`.
2. **`test_parse_full_page_and_educational_notes`**: Analyte `Platelets` was not matched because the regex pattern `r"\bplatelet(?: count)?\b"` lacked the plural `s`.
   - *Resolution*: Updated regex alias to `r"\bplatelets?(?: count)?\b"` (and similarly updated `white blood cells?` and `red blood cells?`).
3. **PyMuPDF Deprecation Warning**: `import fitz` issued a deprecation warning in PyMuPDF 2.0+.
   - *Resolution*: Migrated import to `import pymupdf` across `pdf_extractor.py` and test modules.

### Final Test Results
- Re-run command: `.\backend\venv\Scripts\pytest .\backend\tests -v`
- Outcome: **29 passed, 1 warning (Starlette testclient HTTPX deprecation notice) in 4.89s**.
- Zero failures, zero regressions.

### Deliverables Created / Updated
- `backend/app/config.py` & `backend/.env.example`
- `backend/app/core/security.py` & `backend/app/core/__init__.py`
- `backend/app/utils/logger.py` & `backend/app/utils/__init__.py`
- `backend/app/models/report.py` & `backend/app/models/__init__.py`
- `backend/app/services/ocr_service.py`
- `backend/app/services/pdf_extractor.py`
- `backend/app/services/reference_ranges.py`
- `backend/app/services/parser.py`
- `backend/app/services/synthetic_samples.py`
- `backend/app/services/__init__.py`
- `backend/app/api/routes/health.py`
- `backend/app/api/routes/reports.py`
- `backend/app/api/routes/__init__.py`
- `backend/app/main.py`
- `backend/sample_reports/generate_samples.py` + 4 synthetic sample PDFs
- `backend/tests/` (7 test modules covering security, extractor, ranges, parser, OCR, logger, API)
- `docs/ARCHITECTURE.md`, `docs/PROMPT_LOG.md`, `docs/VIDEO_PRESENTATION.md`

---

## Prompt 03: Gemini Integration, Privacy Sanitization & Safe AI Handling

- **Date**: 2026-10-26
- **Status**: Completed & Verified (44 of 44 Tests Passing)
- **Objective**: Implement Phase 3: Official `google-genai` SDK integration, dedicated PII/PHI sanitization and payload minimization layer, structured non-diagnostic prompt template, strict error handling (missing credentials, timeouts, rate limits, schema validation, malformed responses), and unit tests for privacy, injection defense, and failure boundaries.

### Actions Taken & Architecture Implemented
1. **Official SDK Installation**:
   - Installed `google-genai` version 2.33.0 in `backend/venv` with zero wheel conflicts on Python 3.13. Updated `backend/requirements.txt`.
2. **Dedicated Privacy Sanitization Layer (`backend/app/services/privacy_sanitizer.py`)**:
   - Implemented regex and heuristic detectors for SSNs, phone numbers, email addresses, MRNs/accession numbers, DOBs, labeled names, and postal addresses.
   - Implemented prompt-injection defense to neutralize malicious or adversarial instructions embedded in document text.
   - Constructed strictly minimized allowlist payloads (`SanitizedPayload`) from parsed `TestResult` objects; raw PDF text is never forwarded to external APIs.
   - Added safety circuit breaker: if all analytes are contaminated or unresolvable, the AI request is explicitly blocked (`is_blocked = True`).
3. **Structured Prompt Builder (`backend/app/services/gemini_prompt.py`)**:
   - Designed `GeminiStructuredResponse` Pydantic schema (`summary_text`, `per_test_explanations`, `limitations_and_uncertainty`, `questions_for_doctor`, `disclaimer`).
   - Drafted system instructions enforcing an 8th-grade reading level, non-diagnostic posture, zero-hallucination mandate, and respect for deterministic flags.
4. **Resilient Gemini Service (`backend/app/services/gemini_service.py`)**:
   - Configured official `genai.Client` targeting `gemini-2.5-flash` with timeout (`30s`), bounded retries (`2`), and temperature (`0.2`).
   - Implemented explicit status returns: `AIExplanationStatus.AI_UNAVAILABLE` on missing keys, timeouts, rate limits (429), provider errors (503), malformed JSON, and schema failures.
   - Never substitutes fabricated prose when Gemini is unconfigured or failing.
   - Ensures no API keys, raw reports, or patient identifiers are ever logged.
5. **API Connection (`backend/app/api/routes/reports.py`)**:
   - Connected `gemini_service.generate_explanation(test_results)` to the PDF upload flow.
   - Verified that deterministic parsing results and educational notes remain 100% intact even when Gemini returns `ai_unavailable`.
6. **Configuration & Version Control**:
   - Added `.gitignore` to prevent any `.env` secrets, `venv/`, or temporary files from being tracked.
   - Updated `backend/.env.example` with safe placeholders for `GEMINI_TIMEOUT_SECONDS`, `GEMINI_MAX_RETRIES`, and `GEMINI_TEMPERATURE`.

### Commands Run
- `.\backend\venv\Scripts\pip install google-genai`: Installed `google-genai` 2.33.0.
- `.\backend\venv\Scripts\pytest .\backend\tests -v`: Initial run (43 passed, 1 failed).
- `.\backend\venv\Scripts\pytest .\backend\tests -v`: Second run (44 passed, 0 failed in 8.92s).

### Failures Detected & Resolved
1. **`test_sanitizer_scrubs_postal_addresses_and_ssn`**: Address `"742 Evergreen Terrace"` was not scrubbed because `Terrace`/`Ter` was missing from `ADDRESS_REGEX`.
   - *Resolution*: Expanded `ADDRESS_REGEX` with `Terrace|Ter|Circle|Cir|Place|Pl|Parkway|Pkwy`.
2. **`PytestCollectionWarning` on `TestResult`**: Pytest attempted to collect the Pydantic data model `TestResult` as a test class due to the `Test` prefix.
   - *Resolution*: Added `__test__ = False` to `TestResult` in `backend/app/models/report.py`.

### Final Test Results
- Re-run command: `.\backend\venv\Scripts\pytest .\backend\tests -v`
- Outcome: **44 passed, 1 warning (Starlette testclient HTTPX deprecation notice) in 8.92s**.
- Zero regressions across Phase 2 tests (all 29 baseline tests preserved and passing, 15 new Phase 3 tests added and passing).

---

## Prompt 04 — MediLens AI: Report History, Retrieval APIs and PDF Export

### Prompt Input
```text
Phase 2 and Phase 3 are complete. The existing backend test suite reports 44 passed tests. Phase 3 integrates the official Google Gen AI SDK behind a dedicated privacy-sanitization layer. Live Gemini connectivity has not yet been verified.

Implement Phase 4 in the existing workspace. Inspect the code before changing it. Preserve working upload, sample, deterministic processing, privacy, and Gemini behavior.

1. Inspect the current implementation
2. Report retrieval and history APIs (GET /api/v1/reports, GET /api/v1/reports/{report_id}, DELETE /api/v1/reports/{report_id})
3. Privacy-aware storage (SQLite repository, zero raw PDF/prompt persistence, toggleable persistence, complete deletion)
4. PDF export (ReportLab PDF generation with disclaimer, synthetic badge, test findings table, conditional AI explanation; JSON export)
5. Consistency and lifecycle
6. Automated tests (storage, export, API lifecycle, history disabled, test isolation)
7. Documentation (ARCHITECTURE.md, PROMPT_LOG.md, VIDEO_PRESENTATION.md)
8. Completion report
```

### Implementation Actions
1. **Configuration & Environment (`backend/app/config.py`, `backend/.env.example`)**:
   - Added `enable_history_persistence: bool = True` and `sqlite_db_path: str = "medilens_history.db"`.
   - Updated `.env.example` with documented environment variables for SQLite storage path and toggleable persistence.
2. **Pydantic Response Schemas (`backend/app/models/report.py`, `backend/app/models/__init__.py`)**:
   - Created `ReportListItem` for lightweight history items (id, filename, upload_timestamp, total_tests, aggregate counters, is_synthetic, ai_status).
   - Created `ReportListResponse` containing paginated items, total count, page, limit, has_more, and history_enabled flag.
3. **Privacy-Aware Storage Repository (`backend/app/services/storage.py`)**:
   - Implemented `StorageRepository` backed by SQLite with automatic schema creation (`reports` table and indexes on `upload_timestamp` and `filename`).
   - Thread-safe connection context with parameterized SQL queries preventing SQL injection.
   - Enforced zero raw PDF persistence: raw binary bytes and unrestricted OCR text are never persisted; only validated structured JSON representations are stored.
   - Implemented `save(report)`, `get(report_id)`, `list_reports(page, limit, search)`, and `delete(report_id)`.
   - Built explicit fallback when `enabled=False`: returns empty lists, ignores save, and reports `history_enabled: False`.
4. **Clinical-Grade Export Service (`backend/app/services/export_service.py`)**:
   - Implemented `ExportService.generate_pdf(report)` using ReportLab:
     - Header with "MediLens AI" branding, Report ID, and generation timestamp.
     - Visible, prominent non-diagnostic informational disclaimer banner.
     - Synthetic data warning banner when `report.is_synthetic == True`.
     - Deterministic laboratory results table with analyte names, extracted values, units, reference intervals, and status flags.
     - Uncertainty callouts and notes explicitly rendered alongside affected tests.
     - Conditional AI explanation section: rendered only when `ai_explanation.status == "completed"`. If AI is unavailable or failed, explicitly prints status as "Unavailable" and notes that deterministic results remain valid.
     - Questions for doctor discussion guide.
   - Implemented `ExportService.generate_json(report)` for formatted, structured JSON exports.
5. **REST API Routes (`backend/app/api/routes/reports.py`)**:
   - Connected `upload_and_process_report` and `load_synthetic_sample` to persist structured summaries to `storage_repo` when enabled.
   - Implemented `GET /api/v1/reports`: paginated list with search filtering across filenames and IDs.
   - Implemented `GET /api/v1/reports/{report_id}`: retrieves full structured report, returning `404 Not Found` for missing IDs.
   - Implemented `DELETE /api/v1/reports/{report_id}`: permanently removes report, returning `204 No Content` on success, or `404 Not Found` if not present.
   - Implemented `GET /api/v1/reports/{report_id}/export`: supports `format=pdf` (`application/pdf`) and `format=json` (`application/json`), returning `400 Bad Request` on unsupported formats and `404 Not Found` on missing IDs.
6. **Automated Test Suite Expansion**:
   - Created `backend/tests/test_storage.py` (6 tests): save/retrieve, cross-instance persistence, pagination/search, deletion, disabled mode, and verification of zero raw PDF persistence.
   - Created `backend/tests/test_export_service.py` (3 tests): PDF structure and `%PDF-` signature, PDF export with AI unavailable, and JSON export schema.
   - Updated `backend/tests/test_api.py` (added 6 comprehensive integration tests with `isolate_storage` temporary DB fixture):
     - `test_list_reports_pagination_and_search`
     - `test_get_report_by_id_and_not_found`
     - `test_delete_report_lifecycle`
     - `test_export_report_pdf_and_json`
     - `test_export_report_invalid_format_and_missing_id`
     - `test_history_disabled_behavior`
7. **Documentation Updates**:
   - Updated `docs/ARCHITECTURE.md` with Storage Architecture, Export Engine, and API response contracts.
   - Updated `docs/PROMPT_LOG.md` with complete Phase 4 implementation records.
   - Updated `docs/VIDEO_PRESENTATION.md` with history retrieval, search, deletion, and PDF export demonstration steps.

### Commands Run
- `.\backend\venv\Scripts\pytest .\backend\tests -v`: Ran full test suite.

### Failures Detected & Resolved
- **Test Database Pollution**: Without isolation, running API tests against the default `medilens_history.db` could pollute the local workspace or cause test cross-talk.
  - *Resolution*: Implemented `isolate_storage` autouse fixture in `backend/tests/test_api.py` using pytest `tmp_path` to guarantee an ephemeral, isolated SQLite file for every test execution.

### Final Test Results
- Command: `.\backend\venv\Scripts\pytest .\backend\tests -v`
- Outcome: **59 passed, 1 warning (Starlette testclient HTTPX deprecation notice) in 17.91s**.
- Zero regressions across Phase 2 and Phase 3 tests (44 previous tests + 15 new tests = 59 total tests passing).

---

## Prompt 05 — MediLens AI: Build the Complete React Frontend

### Prompt Input
```text
Phases 2, 3 and 4 are complete according to the previous reports. The backend has deterministic laboratory parsing, optional Gemini explanations, privacy sanitization, SQLite report history, report retrieval and PDF/JSON exports. The backend test suite reported 59 passed tests.

Now implement Phase 5: a complete, polished frontend integrated with the existing FastAPI backend.

1. Technology stack (React, Vite, TypeScript, Tailwind CSS, React Router, Recharts, Lucide React, Axios)
2. Design direction (Clinical SaaS, Deep navy typography, restrained teal accents, high contrast accessible badges, responsive)
3. Application layout and navigation (Dashboard /, Upload /upload, Report Results /reports/:reportId, Report History /history, Privacy and Settings /settings)
4. API integration (Centralized Axios client, typed interfaces matching Pydantic schemas, safe error handling, download triggers)
5. State, usability and accessibility (Semantic HTML, loading/empty/error states, confirmation modals, keyboard accessibility)
6. Tests and verification (Vitest + React Testing Library unit tests, type-checking, production build)
7. Documentation (ARCHITECTURE.md, PROMPT_LOG.md, VIDEO_PRESENTATION.md)
8. Local run instructions (PowerShell commands for backend and frontend)
9. Final completion report
```

### Implementation Actions
1. **Frontend Scaffolding & Configuration**:
   - Initialized Vite + React 19 + TypeScript template inside `frontend/`.
   - Configured `tailwind.config.js` and `postcss.config.js` with MediLens clinical design tokens (navy typography, clinical teal/brand accents, semantic badge indicators).
   - Configured `vite.config.ts` with Vitest test runner configuration (`jsdom`, `globals: true`, `setupFiles`).
   - Configured `frontend/.env.example` and `frontend/.env` with safe `VITE_API_BASE_URL=http://127.0.0.1:8000`.
2. **TypeScript Domain Models (`frontend/src/types/report.ts`)**:
   - Implemented TypeScript interfaces precisely matching backend Pydantic schemas: `FlagStatus`, `ReferenceInterval`, `TestResult`, `ExtractionMetadata`, `EducationalContent`, `AIExplanation`, `ReportSummary`, `ReportListItem`, `ReportListResponse`, and `HealthResponse`.
3. **Centralized API Client (`frontend/src/services/api.ts`)**:
   - Configured Axios client with 45s timeout and centralized error parser (`ApiError`).
   - Implemented typed endpoints: `getHealth()`, `uploadReport(file)`, `loadSyntheticSample(type)`, `getReports(params)`, `getReportById(id)`, `deleteReport(id)`, and `downloadExport(id, format)` with dynamic blob download triggers.
4. **Reusable UI Components**:
   - Layout: `DisclaimerBanner` (permanent non-diagnostic notice), `Navbar` (brand header + real-time health indicator pill), `Sidebar` (responsive desktop view + mobile drawer), and `Layout` (page shell).
   - Common: `StatusBadge` (accessible icons + text for `NORMAL`, `LOW`, `HIGH`, `CRITICAL`, `INCONCLUSIVE`), `SyntheticBadge`, `AIStatusBadge`, `Button` (with variants, sizes, and loading state), `Modal` (accessible dialog with focus trap and keyboard listeners), `Alert` (feedback banners), and `LoadingSpinner`.
   - Results: `ResultsTable` (searchable/filterable tabular findings), `RangeVisualizer` (two-sided horizontal range bar with patient value pin), `AIExplanationCard` (plain-language narrative with explicit offline fallback state), `DoctorQuestionsCard` (discussion topics with clipboard copy), and `EducationalNotesCard` (deterministic knowledge base guide).
5. **Five Core Application Pages**:
   - `DashboardPage` (`/`): Real-time metrics from actual reports, recent analyses list, Recharts distribution visualization, synthetic sample launcher modal.
   - `UploadPage` (`/upload`): Drag-and-drop zone, PDF-only validation, 10MB limit enforcement, step-by-step processing tracker, synthetic demo buttons, privacy notice.
   - `ReportResultsPage` (`/reports/:reportId`): Findings display, status badges, uncertainty notes, AI narrative, doctor questions, PDF export, JSON export, permanent deletion modal.
   - `ReportHistoryPage` (`/history`): Paginated history table, real-time search, quick PDF/JSON downloads, deletion confirmation, empty state with upload action.
   - `PrivacySettingsPage` (`/settings`): Live runtime audit of FastAPI backend, Gemini SDK configuration, and SQLite storage status; explicit transparency disclosures on PII scrubbing, anonymity limits, and single-user storage.
   - `NotFoundPage` (`*`): Safe 404 fallback with return to dashboard.
6. **Automated Frontend Test Suite**:
   - Created `frontend/src/test/mockData.ts` with synthetic test fixtures.
   - Created `frontend/src/test/dashboard.test.tsx` (4 tests): loading state, metrics and recent reports, empty state, synthetic sample modal.
   - Created `frontend/src/test/upload.test.tsx` (5 tests): upload instructions, non-PDF validation, 10MB file limit, upload submission and navigation, synthetic demo launcher.
   - Created `frontend/src/test/results.test.tsx` (5 tests): report details and flags, AI explanation narrative and doctor questions, AI unavailable fallback, PDF and JSON exports, delete confirmation.
   - Created `frontend/src/test/history.test.tsx` (5 tests): history table rendering, search query filter, pagination controls, delete confirmation modal, empty history state.
7. **Documentation Updates**:
   - Updated `docs/ARCHITECTURE.md` with complete frontend architecture, page breakdown, and local run instructions.
   - Updated `docs/PROMPT_LOG.md` with Prompt 05 records and test results.
   - Updated `docs/VIDEO_PRESENTATION.md` with frontend demonstration script walkthrough.

### Commands Run
- `npx -y create-vite@latest frontend --template react-ts --no-interactive`: Scaffolding.
- `npm install react-router-dom lucide-react recharts axios tailwindcss@^3.4.17 postcss autoprefixer`: Core dependencies.
- `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom @testing-library/user-event`: Test dependencies.
- `npm run test`: Ran Vitest suite (19 tests).
- `npm run build`: Ran TypeScript check and production bundle build.
- `.\backend\venv\Scripts\pytest .\backend\tests -q`: Ran backend test suite (59 tests).

### Failures Detected & Resolved
1. **Unused Locals with Strict TS (`noUnusedLocals: true`)**:
   - *Problem*: Vite's strict TypeScript settings failed on unused imports (such as `React` when using `react-jsx`).
   - *Resolution*: Removed all unused imports across source and test files.
2. **Ambiguous Query Targets in Testing Library**:
   - *Problem*: Filenames and labels rendered in both breadcrumbs and headings caused `getByText` to find multiple matching elements.
   - *Resolution*: Updated test queries to use `getAllByText` to assert presence across all matching elements.
3. **HTML File Upload Validation**:
   - *Problem*: `userEvent.upload` silently dropped files that did not match the input's `accept=".pdf"` attribute.
   - *Resolution*: Used `fireEvent.change` to test component-level validation logic directly.

### Final Test Results
- Frontend Vitest suite: **19 passed, 0 failed across 4 test files in 4.39s**.
- Frontend Production build: **0 errors, built in 1.71s (`dist/assets/index-*.js`, `dist/assets/index-*.css`)**.
- Backend Pytest suite: **59 passed, 0 failed in 13.49s (0 regressions)**.




