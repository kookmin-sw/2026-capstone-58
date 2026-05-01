import CritLogo from '@/assets/icons/critLogo.svg?react';
import GoogleIcon from '@/assets/icons/google-icon.svg?react';

const LoginPage = () => {
  const handleGoogleLogin = () => {
    window.location.href = 'http://localhost:8080/oauth2/authorization/google';
  };

  return (
    <div>
      <div className="flex flex-col items-center w-270 mx-auto">
        <div className="flex w-full h-[417px] px-[375px] py-[126px] justify-center items-center">
          <CritLogo className="w-[330px] h-[165px]" />
        </div>

        <div className="flex w-full h-[300px] justify-center items-center">
          <div className="flex w-[612px] flex-col justify-center items-start gap-8">
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;