import { useNavigate } from 'react-router-dom';
import useKeywordStore from '@/stores/useKeywordStore';

interface KeywordCardProps {
  animationKey: number;
}

const KeywordCard = ({ animationKey }: KeywordCardProps) => {
  const navigate = useNavigate();
  const selectedKeyword = useKeywordStore(s => s.selectedKeyword);
  const setSelectedKeyword = useKeywordStore(s => s.setSelectedKeyword);

  if (!selectedKeyword) return null;

  const formatValue = (value: number) => {
    if (value >= 10000) {
      return `${(value / 10000).toFixed(1)}만`;
    }
    return value.toLocaleString();
  };

  const handleClose = () => {
    setSelectedKeyword(null);
  };

  const handleRecommend = () => {
    navigate('/recommend', { state: { keyword: selectedKeyword.text } });
  };

  return (
    <div
      key={animationKey}
      className="relative flex flex-col w-80 p-6 gap-4 mr-30 rounded-2xl bg-white/80 backdrop-blur-md border border-[#8257B4]/30 shadow-lg animate-slide-in-right"
    >
      <button
        onClick={handleClose}
        className="absolute top-4 right-4 w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors"
        aria-label="닫기"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
      <div className="text-[#6B4EFF] typo-title1">{selectedKeyword.text}</div>
      <div className="flex flex-col gap-2">
        <div className="text-gray-500 typo-body5">검색량</div>
        <div className="text-black typo-title2">{formatValue(selectedKeyword.value)}</div>
      </div>
      <button
        onClick={handleRecommend}
        className="w-full py-3 bg-[#6B4EFF] text-white typo-body4-semibold rounded-xl hover:opacity-90 transition-opacity"
      >
        이 키워드로 영상 추천받기
      </button>
    </div>
  );
};

export default KeywordCard;
