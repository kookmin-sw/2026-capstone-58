import { useEffect } from 'react';
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
        <div className="flex flex-col justify-between items-center gap-5">
          <ImprovementPointCard />
          <RecommendActionCard />
        </div>
      </div>
      <RecommendContent />
    </div>
  );
};

export default DetailAnalysis;
