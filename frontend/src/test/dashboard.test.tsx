import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { DashboardPage } from '../pages/DashboardPage';
import { apiService } from '../services/api';
import { mockReportListResponse } from './mockData';

vi.mock('../services/api', () => ({
  apiService: {
    getReports: vi.fn(),
    loadSyntheticSample: vi.fn(),
  },
}));

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(apiService.getReports).mockReturnValue(new Promise(() => {}));
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );
    expect(screen.getAllByText(/Loading MediLens AI dashboard/i)[0]).toBeInTheDocument();
  });

  it('renders metrics and recent reports when data is available', async () => {
    vi.mocked(apiService.getReports).mockResolvedValue(mockReportListResponse);

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Understand Laboratory Findings with Clarity/i)).toBeInTheDocument();
    });

    // Check metric counters
    expect(screen.getByText('Reports In History')).toBeInTheDocument();
    expect(screen.getByText('Analytes Extracted')).toBeInTheDocument();
    expect(screen.getByText('Within Reference')).toBeInTheDocument();
    expect(screen.getByText('Outside Reference')).toBeInTheDocument();

    // Check recent report filename
    expect(screen.getByText('synthetic_cbc_panel.pdf')).toBeInTheDocument();
    expect(screen.getByText('AI Explanation Ready')).toBeInTheDocument();
  });

  it('renders empty state when no reports exist', async () => {
    vi.mocked(apiService.getReports).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      has_more: false,
      history_enabled: true,
    });

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No reports recorded yet/i)).toBeInTheDocument();
    });
  });

  it('opens synthetic demo modal on button click', async () => {
    vi.mocked(apiService.getReports).mockResolvedValue(mockReportListResponse);
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Try Synthetic Demo/i)).toBeInTheDocument();
    });

    const demoBtn = screen.getByRole('button', { name: /Try Synthetic Demo/i });
    await user.click(demoBtn);

    expect(screen.getByText('Select Synthetic Lab Report')).toBeInTheDocument();
    expect(screen.getByText('Complete Blood Count (CBC)')).toBeInTheDocument();
    expect(screen.getByText('Comprehensive Metabolic Panel (CMP)')).toBeInTheDocument();
  });
});
