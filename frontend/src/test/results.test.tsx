import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ReportResultsPage } from '../pages/ReportResultsPage';
import { apiService } from '../services/api';
import { mockReportSummary } from './mockData';

const mockedNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockedNavigate,
  };
});

vi.mock('../services/api', () => ({
  apiService: {
    getReportById: vi.fn(),
    downloadExport: vi.fn(),
    deleteReport: vi.fn(),
  },
}));

describe('ReportResultsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWithRouter = (reportId: string = 'rep-test-cbc-12345') => {
    return render(
      <MemoryRouter initialEntries={[`/reports/${reportId}`]}>
        <Routes>
          <Route path="/reports/:reportId" element={<ReportResultsPage />} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders report details, tests, and deterministic status flags', async () => {
    vi.mocked(apiService.getReportById).mockResolvedValue(mockReportSummary);

    renderWithRouter();

    await waitFor(() => {
      expect(screen.getAllByText('synthetic_cbc_panel.pdf').length).toBeGreaterThan(0);
    });

    // Check analytes
    expect(screen.getAllByText('Hemoglobin').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Platelets').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Glucose').length).toBeGreaterThan(0);

    // Check deterministic status badges
    expect(screen.getAllByText('Normal').length).toBeGreaterThan(0);
    expect(screen.getByText('Below Range (Low)')).toBeInTheDocument();
    expect(screen.getByText('Above Range (High)')).toBeInTheDocument();

    // Check uncertainty notes
    expect(
      screen.getByText(/Slightly below standard laboratory reference boundary/i)
    ).toBeInTheDocument();
  });

  it('renders completed AI explanation narrative and doctor questions', async () => {
    vi.mocked(apiService.getReportById).mockResolvedValue(mockReportSummary);

    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText(/Plain-Language AI Educational Summary/i)).toBeInTheDocument();
    });

    expect(screen.getByText(mockReportSummary.ai_explanation.summary_text!)).toBeInTheDocument();
    expect(
      screen.getByText('Should we repeat the platelet count in 4 weeks?')
    ).toBeInTheDocument();
  });

  it('renders explicit AI unavailable state when Gemini is offline', async () => {
    const unavailableReport = {
      ...mockReportSummary,
      ai_explanation: {
        status: 'ai_unavailable' as const,
        provider: null,
        model: null,
        summary_text: null,
        per_test_explanations: {},
        limitations_and_uncertainty: [],
        questions_for_doctor: [],
        status_reason: 'Gemini API key is not configured.',
        disclaimer: 'Informational non-diagnostic summary.',
      },
    };

    vi.mocked(apiService.getReportById).mockResolvedValue(unavailableReport);

    renderWithRouter();

    await waitFor(() => {
      expect(
        screen.getByText(/AI Narrative Explanation: Offline \/ Unavailable/i)
      ).toBeInTheDocument();
    });

    expect(screen.getByText(/Gemini API key is not configured/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Zero clinical data was fabricated/i)
    ).toBeInTheDocument();
  });

  it('triggers PDF and JSON exports on button click', async () => {
    vi.mocked(apiService.getReportById).mockResolvedValue(mockReportSummary);
    vi.mocked(apiService.downloadExport).mockResolvedValue(undefined);
    const user = userEvent.setup();

    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByText('Export PDF')).toBeInTheDocument();
    });

    const exportPdfBtn = screen.getByRole('button', { name: /Export PDF/i });
    await user.click(exportPdfBtn);

    expect(apiService.downloadExport).toHaveBeenCalledWith(mockReportSummary.id, 'pdf');

    const exportJsonBtn = screen.getByRole('button', { name: /Export JSON/i });
    await user.click(exportJsonBtn);

    expect(apiService.downloadExport).toHaveBeenCalledWith(mockReportSummary.id, 'json');
  });

  it('opens confirmation modal and deletes report', async () => {
    vi.mocked(apiService.getReportById).mockResolvedValue(mockReportSummary);
    vi.mocked(apiService.deleteReport).mockResolvedValue(undefined);
    const user = userEvent.setup();

    renderWithRouter();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^Delete$/i })).toBeInTheDocument();
    });

    const deleteBtn = screen.getByRole('button', { name: /^Delete$/i });
    await user.click(deleteBtn);

    // Modal should be open
    expect(screen.getByText('Confirm Report Deletion')).toBeInTheDocument();

    const confirmDeleteBtn = screen.getByRole('button', { name: /Delete Permanently/i });
    await user.click(confirmDeleteBtn);

    expect(apiService.deleteReport).toHaveBeenCalledWith(mockReportSummary.id);
    await waitFor(() => {
      expect(mockedNavigate).toHaveBeenCalledWith('/history');
    });
  });
});
