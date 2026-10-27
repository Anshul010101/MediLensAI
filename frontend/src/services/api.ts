import axios, { AxiosError } from 'axios';
import {
  HealthResponse,
  ReportListResponse,
  ReportSummary,
} from '../types/report';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 45000,
});

export class ApiError extends Error {
  statusCode: number;
  constructor(message: string, statusCode: number = 500) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
  }
}

function parseErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{ detail?: string | { msg?: string }[] }>;
    if (axiosErr.response?.data) {
      const detail = axiosErr.response.data.detail;
      if (typeof detail === 'string') {
        return detail;
      }
      if (Array.isArray(detail) && detail.length > 0 && detail[0].msg) {
        return detail[0].msg;
      }
    }
    if (axiosErr.code === 'ECONNABORTED') {
      return 'Request timed out. Please verify that the backend server is running.';
    }
    if (!axiosErr.response) {
      return 'Unable to connect to the MediLens AI backend server. Please verify it is running on http://127.0.0.1:8000.';
    }
    return axiosErr.message || 'An unexpected API error occurred.';
  }
  return error instanceof Error ? error.message : 'An unknown error occurred.';
}

export const apiService = {
  async getHealth(): Promise<HealthResponse> {
    try {
      const response = await apiClient.get<HealthResponse>('/health');
      return response.data;
    } catch (error) {
      throw new ApiError(parseErrorMessage(error), (error as AxiosError)?.response?.status || 500);
    }
  },

  async uploadReport(file: File): Promise<ReportSummary> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await apiClient.post<ReportSummary>('/reports/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new ApiError(parseErrorMessage(error), (error as AxiosError)?.response?.status || 500);
    }
  },

  async loadSyntheticSample(sampleType: 'cbc' | 'cmp' | 'glucose' | 'lipid'): Promise<ReportSummary> {
    try {
      const response = await apiClient.post<ReportSummary>('/reports/sample', {
        sample_type: sampleType,
      });
      return response.data;
    } catch (error) {
      throw new ApiError(parseErrorMessage(error), (error as AxiosError)?.response?.status || 500);
    }
  },

  async getReports(params?: { page?: number; limit?: number; search?: string }): Promise<ReportListResponse> {
    try {
      const response = await apiClient.get<ReportListResponse>('/reports', {
        params: {
          page: params?.page || 1,
          limit: params?.limit || 10,
          search: params?.search || undefined,
        },
      });
      return response.data;
    } catch (error) {
      throw new ApiError(parseErrorMessage(error), (error as AxiosError)?.response?.status || 500);
    }
  },

  async getReportById(reportId: string): Promise<ReportSummary> {
    try {
      const response = await apiClient.get<ReportSummary>(`/reports/${encodeURIComponent(reportId)}`);
      return response.data;
    } catch (error) {
      throw new ApiError(parseErrorMessage(error), (error as AxiosError)?.response?.status || 500);
    }
  },

  async deleteReport(reportId: string): Promise<void> {
    try {
      await apiClient.delete(`/reports/${encodeURIComponent(reportId)}`);
    } catch (error) {
      throw new ApiError(parseErrorMessage(error), (error as AxiosError)?.response?.status || 500);
    }
  },

  async downloadExport(reportId: string, format: 'pdf' | 'json'): Promise<void> {
    try {
      const response = await apiClient.get(`/reports/${encodeURIComponent(reportId)}/export`, {
        params: { format },
        responseType: 'blob',
      });

      // Extract filename from header or construct fallback
      let filename = `medilens_${reportId}.${format}`;
      const disposition = response.headers['content-disposition'];
      if (disposition && disposition.includes('filename=')) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }

      // Trigger browser download
      const blob = new Blob([response.data], {
        type: format === 'pdf' ? 'application/pdf' : 'application/json',
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      throw new ApiError(parseErrorMessage(error), (error as AxiosError)?.response?.status || 500);
    }
  },
};
