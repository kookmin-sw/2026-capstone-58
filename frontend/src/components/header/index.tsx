import { useNavigate, useLocation } from 'react-router-dom';
import LogoutIcon from '@/assets/icons/logout-icon.svg?react';
import SettingIcon from '@/assets/icons/setting-icon.svg?react';
import PersonIcon from '@/assets/icons/person-icon.svg?react';
import CritLogo from '@/assets/icons/critLogo.svg?react';
import useUserStore from '@/stores/useUserStore';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;
  const channelName = useUserStore(s => s.channelName);
  const clearUser = useUserStore(s => s.clearUser);

  const handleLogout = () => {
    localStorage.removeItem('token');
    clearUser();
    navigate('/login');
  };

  return (
    <div className="sticky top-0 z-50 flex w-full h-20 justify-between items-center border-b border-[#dad9d9]/30 px-5 bg-white/70 backdrop-blur-md">
      <CritLogo className="w-38 h-11 cursor-pointer" onClick={() => navigate('/main')} />
      <div className="flex justify-center items-center gap-5 self-stretch">
        <div
          className="flex w-24 h-9 flex-col justify-center text-center cursor-pointer typo-body2"
          onClick={() => navigate('/recommend')}
        >
          <div className={currentPath === '/recommend' ? 'text-[#6B4EFF]' : 'text-black'}>
            영상추천
          </div>
        </div>
        <div
          className="flex w-24 h-9 flex-col justify-center text-center cursor-pointer typo-body2"
          onClick={() => navigate('/analysis')}
        >
          <div className={currentPath === '/analysis' ? 'text-[#6B4EFF]' : 'text-black'}>
            채널분석
          </div>
        </div>
        <div className="flex w-24 h-9 flex-col justify-center text-center cursor-not-allowed typo-body2 opacity-40">
          <div className="text-black">트렌드</div>
        </div>
      </div>
      <div className="flex w-40 h-9 justify-center items-center">
        <div className="text-[#6B4EFF] typo-body2">{channelName}</div>
        <div className="text-black typo-body2">&nbsp;님 어서오세요!</div>
      </div>
      <div className="flex h-11 items-center justify-end gap-5">
        <LogoutIcon className="w-6 h-6 cursor-pointer" onClick={handleLogout} />
        <PersonIcon className="w-6 h-6" />
        <SettingIcon className="w-6 h-6" />
      </div>
    </div>
  );
};

export default Header;
