import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { ReportResultsPage } from './pages/ReportResultsPage';
import { ReportHistoryPage } from './pages/ReportHistoryPage';
import { PrivacySettingsPage } from './pages/PrivacySettingsPage';
import { NotFoundPage } from './pages/NotFoundPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="reports/:reportId" element={<ReportResultsPage />} />
          <Route path="history" element={<ReportHistoryPage />} />
          <Route path="settings" element={<PrivacySettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
