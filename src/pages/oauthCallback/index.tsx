import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const OAuthCallbackPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const channelName = params.get('channelName');
    const channelId = params.get('channelId');

    if (token) {
      localStorage.setItem('token', token);
      localStorage.removeItem('accessToken');

      if (channelName) {
        localStorage.setItem('channelName', channelName);
      }
      if (channelId) {
        localStorage.setItem('channelId', channelId);
      }

      navigate('/recommend');
    } else {
      navigate('/');
    }
  }, [navigate]);

  return null;
};

export default OAuthCallbackPage;