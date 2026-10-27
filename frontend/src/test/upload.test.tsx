import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { UploadPage } from '../pages/UploadPage';
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
    uploadReport: vi.fn(),
    loadSyntheticSample: vi.fn(),
  },
}));

describe('UploadPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders upload instructions and dropzone', () => {
    render(
      <BrowserRouter>
        <UploadPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Upload Laboratory Report')).toBeInTheDocument();
    expect(screen.getByText(/Drag and drop your laboratory PDF here/i)).toBeInTheDocument();
    expect(screen.getByText(/Supports digital PDFs up to 10 MB/i)).toBeInTheDocument();
  });

  it('rejects non-PDF files with clear error message', async () => {
    render(
      <BrowserRouter>
        <UploadPage />
      </BrowserRouter>
    );

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const txtFile = new File(['plain text data'], 'report.txt', { type: 'text/plain' });

    fireEvent.change(fileInput, { target: { files: [txtFile] } });

    expect(
      screen.getByText(/Invalid file format. MediLens AI accepts PDF documents only/i)
    ).toBeInTheDocument();
  });

  it('rejects files exceeding 10 MB limit', async () => {
    const user = userEvent.setup();
    render(
      <BrowserRouter>
        <UploadPage />
      </BrowserRouter>
    );

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    // Create oversized dummy file (11MB)
    const largeFile = new File([new Uint8Array(11 * 1024 * 1024)], 'large_report.pdf', {
      type: 'application/pdf',
    });

    await user.upload(fileInput, largeFile);

    expect(screen.getByText(/exceeds the maximum allowed limit of 10 MB/i)).toBeInTheDocument();
  });

  it('accepts valid PDF and submits to API, then navigates to report detail', async () => {
    vi.mocked(apiService.uploadReport).mockResolvedValue(mockReportSummary);
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <UploadPage />
      </BrowserRouter>
    );

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const validPdf = new File(['%PDF-1.4 mock binary content'], 'lab_cbc.pdf', {
      type: 'application/pdf',
    });

    await user.upload(fileInput, validPdf);

    // Selected file card should be visible
    expect(screen.getByText('lab_cbc.pdf')).toBeInTheDocument();
    const processBtn = screen.getByRole('button', { name: /Process Document/i });

    await user.click(processBtn);

    expect(apiService.uploadReport).toHaveBeenCalledWith(validPdf);
    await waitFor(() => {
      expect(mockedNavigate).toHaveBeenCalledWith(`/reports/${mockReportSummary.id}`);
    });
  });

  it('triggers synthetic sample loading when clicked', async () => {
    vi.mocked(apiService.loadSyntheticSample).mockResolvedValue(mockReportSummary);
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <UploadPage />
      </BrowserRouter>
    );

    const cbcSampleBtn = screen.getByRole('button', { name: /Complete Blood Count/i });
    await user.click(cbcSampleBtn);

    expect(apiService.loadSyntheticSample).toHaveBeenCalledWith('cbc');
    await waitFor(() => {
      expect(mockedNavigate).toHaveBeenCalledWith(`/reports/${mockReportSummary.id}`);
    });
  });
});
