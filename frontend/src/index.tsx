import ReactDOM from 'react-dom/client';

import Router from '@/routes/routes';

import './index.css';

const enableMocking = async () => {
  if (import.meta.env.VITE_USE_MOCK === 'true') {
    const { worker } = await import('./mocks/browser');
    return worker.start({ onUnhandledRequest: 'bypass' });
  }
};

enableMocking().then(() => {
  const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
  root.render(<Router />);
});
