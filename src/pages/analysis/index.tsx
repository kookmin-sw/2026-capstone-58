import { useEffect, useState } from 'react';
import Header from '@/components/header';
import Footer from '@/components/footer';
import UserProfile from '@/components/channel/userProfile';
import AlgorithmScore from '@/components/channel/algorithmScore';
import SummaryChannel from '@/components/channel/summaryChannel';
import GuideChannel from '@/components/channel/guideChannel';
import VideoChannel from '@/components/channel/videoChannel';
import DetailAnalysis from '@/pages/analysis/detailAnalysis';
import { getChannelAnalysis } from '@/api/command';
import useChannelStore from '@/stores/useChannelStore';
import useCurrentVideoStore from '@/stores/useCurrentVideoStore';

const AnalysisPage = () => {
  const setData = useChannelStore(s => s.setData);
  const clearVideo = useCurrentVideoStore(s => s.clear);
  const [showDetail, setShowDetail] = useState(false);
  const [slideDirection, setSlideDirection] = useState<'left' | 'right'>('right');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getChannelAnalysis('https://www.youtube.com/@T1_Faker');
        setData(res);
      } catch (err) {
        console.error('채널 분석 요청 실패:', err);
      }
    };
    fetchData();
  }, [setData]);

  const handleVideoClick = () => {
    setSlideDirection('right');
    setShowDetail(true);
    window.scrollTo(0, 0);
  };

  const handleBack = () => {
    clearVideo();
    setSlideDirection('left');
    setShowDetail(false);
    window.scrollTo(0, 0);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      {!showDetail ? (
        <div
          key="list"
          className={`flex flex-col items-center pt-10 px-10 overflow-hidden ${slideDirection === 'left' ? 'animate-slide-in-left' : ''}`}
        >
          <div className="flex flex-col w-full justify-center items-center gap-7 pb-2.5 animate-fade-in-up">
            <UserProfile />
            <div className="w-full h-0.25 bg-[#A594F9]" />
          </div>
          <div
            className="flex w-full justify-center items-center gap-2 pb-2.5 animate-fade-in-up"
            style={{ animationDelay: '0.15s' }}
          >
            <AlgorithmScore />
            <SummaryChannel />
          </div>
          <div
            className="flex w-full justify-center items-center pb-2.5 animate-fade-in-up"
            style={{ animationDelay: '0.3s' }}
          >
            <GuideChannel />
          </div>
          <div
            className="flex w-full justify-center items-center pt-2.5 animate-fade-in-up"
            style={{ animationDelay: '0.45s' }}
          >
            <VideoChannel onVideoClick={handleVideoClick} />
          </div>
        </div>
      ) : (
        <div
          key="detail"
          className={`flex flex-col items-center overflow-hidden ${slideDirection === 'right' ? 'animate-slide-in-right' : ''}`}
        >
          <DetailAnalysis onBack={handleBack} />
        </div>
      )}
      <Footer />
    </div>
  );
};

export default AnalysisPage;
