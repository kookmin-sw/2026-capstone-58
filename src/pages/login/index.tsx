import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import CritLogo from '@/assets/icons/critLogo.svg?react';
import GoogleIcon from '@/assets/icons/google-icon.svg?react';
import useUserStore from '@/stores/useUserStore';

const LoginPage = () => {
  const navigate = useNavigate();
  const setUser = useUserStore(s => s.setUser);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    console.log('전체 파라미터:', Object.fromEntries(params));

    const token = params.get('token');
    const channelName = params.get('channelName');
    const channelURL = params.get('channelURL');

    if (token) {
      localStorage.setItem('token', token);
      setUser(channelName, channelURL);
      navigate('/');
    }
  }, [navigate, setUser]);

  const handleGoogleLogin = () => {
    window.location.href = `${import.meta.env.VITE_SERVER_URL}/oauth2/authorization/google`;
  };

  const handleMockLogin = () => {
    localStorage.setItem('token', 'mock-jwt-token-for-development');
    setUser('CRiT', 'https://www.youtube.com/@CRiT');
    navigate('/');
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="flex flex-col items-center gap-8">
        <CritLogo className="w-[330px] h-[165px]" />

        <div className="flex w-[612px] flex-col items-start gap-8">
          <div className="flex flex-col items-start gap-3 self-stretch">
            <div
              className="text-[#232323]"
              style={{
                fontFamily: 'Pretendard',
                fontSize: '35px',
                fontStyle: 'normal',
                fontWeight: 600,
                lineHeight: '49px',
                letterSpacing: '-0.875px',
              }}
            >
              Sign in
            </div>

            <div
              className="text-[#969696]"
              style={{
                fontFamily: 'Pretendard',
                fontSize: '20px',
                fontStyle: 'normal',
                fontWeight: 500,
                lineHeight: '28px',
                letterSpacing: '1px',
              }}
            >
              구글 계정으로 로그인하세요.
            </div>
          </div>

          <button
            type="button"
            onClick={handleGoogleLogin}
            className="flex h-[54px] px-2 py-4 justify-center items-center self-stretch rounded-[10px] border border-[#E6E8E7] bg-[#CDC1FF] cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <span
                className="text-[#232323]"
                style={{
                  fontFamily: 'Pretendard',
                  fontSize: '20px',
                  fontStyle: 'normal',
                  fontWeight: 500,
                  lineHeight: '28px',
                  letterSpacing: '1px',
                }}
              >
                Sign in with Google
              </span>
              <GoogleIcon className="w-6 h-6" />
            </div>
          </button>

          {import.meta.env.VITE_USE_MOCK === 'true' && (
            <button
              type="button"
              onClick={handleMockLogin}
              className="flex h-[54px] px-2 py-4 justify-center items-center self-stretch rounded-[10px] border border-dashed border-gray-400 bg-gray-100 cursor-pointer"
            >
              <span className="text-gray-600 text-[16px] font-medium">🧪 개발자 로그인</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
