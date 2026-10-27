import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ReportHistoryPage } from '../pages/ReportHistoryPage';
import { apiService } from '../services/api';
import { mockReportListResponse } from './mockData';

vi.mock('../services/api', () => ({
  apiService: {
    getReports: vi.fn(),
    deleteReport: vi.fn(),
    downloadExport: vi.fn(),
  },
}));

describe('ReportHistoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders history table with saved reports', async () => {
    vi.mocked(apiService.getReports).mockResolvedValue(mockReportListResponse);

    render(
      <BrowserRouter>
        <ReportHistoryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('synthetic_cbc_panel.pdf')).toBeInTheDocument();
    });

    expect(screen.getByText('Report History')).toBeInTheDocument();
    expect(screen.getByText('rep-test-cbc-12345')).toBeInTheDocument();
    expect(screen.getByText('3 tests')).toBeInTheDocument();
    expect(screen.getByText('AI Explanation Ready')).toBeInTheDocument();
  });

  it('filters reports when searching', async () => {
    vi.mocked(apiService.getReports).mockResolvedValue(mockReportListResponse);
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <ReportHistoryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Search by filename or Report ID/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search by filename or Report ID/i);
    await user.type(searchInput, 'cbc');

    await waitFor(() => {
      expect(apiService.getReports).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'cbc' })
      );
    });
  });

  it('renders pagination controls when total exceeds page limit', async () => {
    vi.mocked(apiService.getReports).mockResolvedValue({
      items: Array.from({ length: 10 }, (_, i) => ({
        id: `rep-item-${i}`,
        filename: `report_${i}.pdf`,
        upload_timestamp: '2026-10-27T10:00:00Z',
        total_tests_detected: 5,
        in_range_count: 4,
        out_of_range_count: 1,
        inconclusive_count: 0,
        is_synthetic: false,
        ai_status: 'completed' as const,
      })),
      total: 25,
      page: 1,
      limit: 10,
      has_more: true,
      history_enabled: true,
    });

    render(
      <BrowserRouter>
        <ReportHistoryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /Next/i })).toBeEnabled();
    expect(screen.getByRole('button', { name: /Previous/i })).toBeDisabled();
  });

  it('opens delete confirmation modal and triggers deletion', async () => {
    vi.mocked(apiService.getReports).mockResolvedValue(mockReportListResponse);
    vi.mocked(apiService.deleteReport).mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <ReportHistoryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByTitle('Delete Report')).toBeInTheDocument();
    });

    const deleteBtn = screen.getByTitle('Delete Report');
    await user.click(deleteBtn);

    expect(screen.getByText('Confirm Report Deletion')).toBeInTheDocument();
    const confirmBtn = screen.getByRole('button', { name: /Delete Permanently/i });
    await user.click(confirmBtn);

    expect(apiService.deleteReport).toHaveBeenCalledWith('rep-test-cbc-12345');
  });

  it('renders empty state when no historical reports exist', async () => {
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
        <ReportHistoryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No reports found')).toBeInTheDocument();
    });
  });
});
