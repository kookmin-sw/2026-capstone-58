import SparkIcon from '@/assets/icons/score-icons/video-detail/sparkle-icon.svg?react';
import AICommentIcon from '@/assets/icons/score-icons/video-detail/ai-comment-icon.svg?react';

interface AISummaryCardProps {
  isLoading?: boolean;
  summary?: string;
}

const AISummaryCard = ({ isLoading = false, summary }: AISummaryCardProps) => {
  return (
    <div className="flex w-full px-6 py-6 justify-center items-start gap-1 bg-white rounded-xl border-[0.1px] border-[#8257B4]">
      <SparkIcon className="w-4 h-4" />
      <div className="flex w-full justify-center items-start gap-28">
        <div className="flex flex-col w-full justify-center items-start gap-6">
          <div className="w-full justify-start items-center text-[#6452CE] typo-body4-semibold">
            AI 한 줄 분석
          </div>
          <div className="w-full justify-start items-start text-black typo-body5">
            {isLoading ? (
              <span className="text-gray-400 animate-loading-pulse">
                AI가 영상을 분석하고 있습니다...
              </span>
            ) : (
              summary ||
              '클릭을 유도하는 썸네일과 제목 덕분에 유입이 높았고, 안정적인 시청 유지율로 추천 확장까지 잘 이루어진 영상입니다.'
            )}
          </div>
        </div>
        <AICommentIcon className="w-29 h-29" />
      </div>
    </div>
  );
};

export default AISummaryCard;
