import VideoTitleItem from '@/components/videoTitle/videoTitleItem';
import useAIFormStore from '@/stores/useAIFormStore';

const VideoTitle = () => {
  const data = useAIFormStore(s => s.data);
  const titles = data?.suggestedTitles ?? [];

  return (
    <div className="inline-flex w-full py-6 pl-6 pr-5 flex-col items-start gap-5 rounded-xl bg-[#fff] border border-[#A594F9]">
      <div className="flex w-full typo-title-bold text-[#0A0A0A] items-stretch">AI 추천 제목</div>
      {titles.map((title, i) => (
        <VideoTitleItem key={i} title={title} />
      ))}
    </div>
  );
};

export default VideoTitle;
