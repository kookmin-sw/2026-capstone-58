import { useEffect, useState } from 'react';
import ArrowLeftIcon from '@/assets/icons/score-icons/video-detail/arrow-left-icon.svg?react';
import VideoInfo from '@/components/videoDetail/videoInfo';
import DetailScore from '@/components/videoDetail/detailScore';
import AISummaryCard from '@/components/videoDetail/aiSummaryCard';
import ViewGrowthCard from '@/components/videoDetail/viewGrowthCard';
import ViewingTimeCard from '@/components/videoDetail/viewingTimeCard';
import ImprovementPointCard from '@/components/videoDetail/improvementPointCard';
import RecommendActionCard from '@/components/videoDetail/recommendActionCard';
import RecommendContent from '@/components/videoDetail/recommendContent';
import useCurrentVideoStore from '@/stores/useCurrentVideoStore';
import { getVideoAnalysis } from '@/api/command';

interface DetailAnalysisProps {
  onBack: () => void;
}

const DetailAnalysis = ({ onBack }: DetailAnalysisProps) => {
  const videoId = useCurrentVideoStore(s => s.videoId);
  const setVideoAnalysis = useCurrentVideoStore(s => s.setVideoAnalysis);
  const setLoading = useCurrentVideoStore(s => s.setLoading);

  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [isSubmitted, setIsSubmitted] = useState(false);

  useEffect(() => {
    const fetchVideoAnalysis = async () => {
      if (!videoId) return;
      setLoading(true);
      try {
        const res = await getVideoAnalysis(videoId);
        setVideoAnalysis(res);
      } catch (err) {
        console.error('영상 분석 요청 실패:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchVideoAnalysis();
  }, [videoId, setVideoAnalysis, setLoading]);

  const handleSubmitRating = () => {
    if (rating === 0) return;
    setIsSubmitted(true);
  };

  return (
    <div className="flex flex-col w-full items-center gap-6 p-10 bg-[#F5EFFF] animate-slide-in-right">
      <div
        className="flex w-full justify-start items-center gap-2 cursor-pointer hover:opacity-70"
        onClick={onBack}
      >
        <ArrowLeftIcon className="w-5 h-5" />
        <div className="text-black typo-body3">분석 목록으로 돌아가기</div>
      </div>
      <div className="flex flex-col w-full justify-center items-center gap-4">
        <VideoInfo />
      </div>
      <DetailScore />
      <div className="flex w-full justify-center items-stretch gap-4">
        <div className="flex flex-col w-full justify-start items-center gap-5">
          <AISummaryCard />
          <ViewGrowthCard />
          <ViewingTimeCard />
        </div>
        <div className="flex flex-col w-[30%] justify-start items-center gap-5">
          <ImprovementPointCard />
          <RecommendActionCard />
          {/* 만족도 평가 */}
          <div className="flex flex-col flex-1 w-full px-6 py-5 gap-4 justify-center items-center bg-white rounded-xl border-[0.1px] border-[#8257B4]">
            <div className="text-[#6452CE] typo-body4-semibold">분석 결과가 만족스러우신가요?</div>
            {isSubmitted ? (
              <div className="flex flex-col items-center gap-2 animate-fade-in">
                <div className="text-[#5AC467] typo-body4-semibold">제출이 완료되었습니다!</div>
                <div className="text-gray-500 typo-body5">소중한 피드백 감사합니다 ✨</div>
              </div>
            ) : (
              <>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map(star => (
                    <svg
                      key={star}
                      className={`w-8 h-8 cursor-pointer transition-all duration-200 ${
                        star <= (hoverRating || rating)
                          ? 'text-[#FFD700] scale-110'
                          : 'text-gray-300'
                      }`}
                      fill="currentColor"
                      viewBox="0 0 24 24"
                      onMouseEnter={() => setHoverRating(star)}
                      onMouseLeave={() => setHoverRating(0)}
                      onClick={() => setRating(star)}
                    >
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                  ))}
                </div>
                <button
                  onClick={handleSubmitRating}
                  disabled={rating === 0}
                  className={`px-6 py-2 rounded-lg typo-body5 transition-all duration-200 ${
                    rating > 0
                      ? 'bg-[#D9D2FF] text-white hover:bg-[#6B42FF] active:bg-[#C4B8FF] cursor-pointer'
                      : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  제출하기
                </button>
              </>
            )}
          </div>
        </div>
      </div>
      <RecommendContent />
    </div>
  );
};

export default DetailAnalysis;
