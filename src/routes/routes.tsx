import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import MainPage from '@/pages/main';

const Router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route index element={<MainPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default Router;
