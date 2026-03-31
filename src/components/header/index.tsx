import { useState } from 'react';
import LogoutIcon from '@/assets/icons/logout-icon.svg?react';
import SettingIcon from '@/assets/icons/setting-icon.svg?react';
import CritLogo from '@/assets/icons/critLogo.svg?react';

const Header = () => {
  const [activeTab, setActiveTab] = useState<'recommend' | 'mypage'>('recommend');

  return (
    <div className="flex w-full h-27 justify-between border-b-2 border-black px-6.5">
      <div className="flex items-center gap-12.5">
        <CritLogo className="w-[159px] h-[77px]" />
        <div className="flex items-center gap-5">
          <div
            className="flex w-35 h-12.5 py-2.5 justify-center items-center cursor-pointer"
            onClick={() => setActiveTab('recommend')}
          >
            <div
              className={`flex justify-center ${activeTab === 'recommend' ? 'text-[#6B4EFF] typo-title-bold' : 'text-black typo-title'}`}
            >
              영상 추천
            </div>
          </div>
          <div
            className="flex w-35 h-12.5 py-2.5 justify-center items-center cursor-pointer"
            onClick={() => setActiveTab('mypage')}
          >
            <div
              className={`flex justify-center ${activeTab === 'mypage' ? 'text-[#6B4EFF] typo-title-bold' : 'text-black typo-title'}`}
            >
              마이페이지
            </div>
          </div>
        </div>
      </div>
      <div className="flex items-center justify-between gap-8">
        <LogoutIcon />
        <SettingIcon />
      </div>
    </div>
  );
};

export default Header;
