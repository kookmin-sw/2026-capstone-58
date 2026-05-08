import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import RecommendPage from '@/pages/recommend';
import AnalysisPage from '@/pages/analysis';
import LoginPage from '@/pages/login';
import OAuthCallbackPage from '@/pages/oauthCallback';

const Router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route index element={<LoginPage />} />
        <Route path="oauth-callback" element={<OAuthCallbackPage />} />
        <Route path="recommend" element={<RecommendPage />} />
        <Route path="analysis" element={<AnalysisPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default Router;
