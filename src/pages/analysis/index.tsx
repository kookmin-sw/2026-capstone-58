import Header from '@/components/header';
import Footer from '@/components/footer';
import UserProfile from '@/components/channel/userProfile';
import AlgorithmScore from '@/components/channel/algorithmScore';
import SummaryChannel from '@/components/channel/summaryChannel';
import GuideChannel from '@/components/channel/guideChannel';
import VideoChannel from '@/components/channel/videoChannel';

const AnalysisPage = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex flex-col items-center pt-10 px-10">
        <div className="flex flex-col w-full justify-center items-center gap-7 pb-2.5 animate-fade-in-up">
          <UserProfile />
          <div className="w-full h-0.25 bg-[#8257B4]" />
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
          className="flex w-full justify-center items-center pb-2.5 animate-fade-in-up"
          style={{ animationDelay: '0.45s' }}
        >
          <VideoChannel />
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default AnalysisPage;
