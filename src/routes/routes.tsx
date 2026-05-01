import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import MainPage from '@/pages/main';
import LoginPage from '@/pages/login';
import OAuthCallbackPage from '@/pages/oauthCallback';

const Router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route index element={<LoginPage />} />
        <Route path="recommend" element={<MainPage />} />
        <Route path="oauth-callback" element={<OAuthCallbackPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default Router;
