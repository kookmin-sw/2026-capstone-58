import { useState } from 'react';
import ShareIcon from '@/assets/icons/share-icon.svg?react';

interface ReferenceItemProps {
  title: string;
  url: string;
}

const ReferenceItem = ({ title, url }: ReferenceItemProps) => {
  const [shared, setShared] = useState(false);

  const handleShare = async (e: React.MouseEvent) => {
    e.stopPropagation();

    if (navigator.share) {
      try {
        await navigator.share({ title, url });
        setShared(true);
        setTimeout(() => setShared(false), 2000);
      } catch {
        // 사용자가 공유 취소한 경우
      }
    } else {
      await navigator.clipboard.writeText(url);
      setShared(true);
      setTimeout(() => setShared(false), 2000);
    }
  };

  const handleClick = () => {
    window.open(url, '_blank');
  };

  return (
    <div
      onClick={handleClick}
      className="flex py-2 px-3 items-center gap-3 self-stretch rounded-lg border border-[#A594F9] bg-white cursor-pointer hover:bg-[#FAFAFE] transition-colors"
    >
      <div className="flex-1 typo-label2 text-black truncate">{title}</div>
      <div
        onClick={handleShare}
        className={`flex items-center gap-1 shrink-0 cursor-pointer ${shared ? 'text-[#6B4EFF]' : 'text-[#0a0a0a89] active:text-[#6B4EFF]'}`}
      >
        {!shared && <ShareIcon className="w-3.5 h-3.5" />}
        <span className="typo-label">{shared ? '공유완료' : '공유'}</span>
      </div>
    </div>
  );
};

export default ReferenceItem;
