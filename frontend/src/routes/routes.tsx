import { Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import RecommendPage from '@/pages/recommend';
import AnalysisPage from '@/pages/analysis';
import LoginPage from '@/pages/login';
import MainPage from '@/pages/main';
import PrivateRoute from '@/routes/privateRoute';

const Router = () => {
  return (
    <Suspense>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<PrivateRoute />}>
            <Route index element={<MainPage />} />
            <Route path="recommend" element={<RecommendPage />} />
            <Route path="analysis" element={<AnalysisPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </Suspense>
  );
};

export default Router;
