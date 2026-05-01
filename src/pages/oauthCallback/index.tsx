import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const OAuthCallbackPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');

    if (token) {
      // token 저장
      localStorage.setItem('accessToken', token);

      // 로그인 성공 후 추천 페이지로 이동
      navigate('/recommend');
    } else {
      // token 없으면 로그인 페이지로 이동
      navigate('/');
    }
  }, [navigate]);

  // 화면에 보여줄 UI 없음
  return null;
};

export default OAuthCallbackPage;