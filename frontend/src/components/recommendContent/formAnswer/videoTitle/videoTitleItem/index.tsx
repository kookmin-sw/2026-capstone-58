import { useState } from 'react';
import CopyIcon from '@/assets/icons/copy-icon.svg?react';
import RefreshIcon from '@/assets/icons/refresh-icon.svg?react';

interface VideoTitleProps {
  title: string;
  onRegenerate?: () => void;
}

const VideoTitle = ({ title, onRegenerate }: VideoTitleProps) => {
  const [copied, setCopied] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(title);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRegenerate = () => {
    setRegenerating(true);
    onRegenerate?.();
    setTimeout(() => setRegenerating(false), 2000);
  };

  return (
    <div className="flex py-3 px-4 justify-end items-center gap-10 self-stretch rounded-xl border border-[#A594F9] bg-[#FAFAFA]">
      <div className="w-64 typo-body4-semibold text-black whitespace-pre-line">
        {title ? (
          title.replace(/\(/g, '\n(')
        ) : (
          <span className="text-gray-400 animate-loading-pulse">제목을 생성하고 있습니다...</span>
        )}
      </div>
      <div className="flex w-17 h-12 justify-end flex-col">
        <div
          onClick={handleCopy}
          className={`flex justify-end items-center gap-1.5 cursor-pointer ${copied ? 'text-[#6B4EFF]' : 'text-[#0a0a0a89] active:text-[#6B4EFF]'}`}
        >
          {!copied && <CopyIcon className="w-4 h-4" />}
          <div className="typo-label">{copied ? '복사완료' : '복사'}</div>
        </div>
        <div
          onClick={handleRegenerate}
          className={`flex justify-end items-center gap-1.5 cursor-pointer ${regenerating ? 'text-[#6B4EFF]' : 'text-[#0a0a0a89] active:text-[#6B4EFF]'}`}
        >
          <RefreshIcon className={`w-4 h-4 ${regenerating ? 'animate-spin' : ''}`} />
          <div className="typo-label">{regenerating ? '생성 중' : '다시생성'}</div>
        </div>
      </div>
    </div>
  );
};

export default VideoTitle;
