import ReferenceItem from './referenceItem';
import useAIFormStore from '@/stores/useAIFormStore';

const CommendList = () => {
  const data = useAIFormStore(s => s.data);
  const videos = (data?.similarVideos ?? []).slice(0, 3);
  const creators = (data?.similarCreators ?? []).slice(0, 2);

  return (
    <div className="flex w-full h-full px-3 py-4 flex-col gap-3 rounded-xl bg-[#FAFAFA] border border-[#A594F9] leading-6">
      <div className="flex w-full gap-1.5 flex-col">
        <div className="flex w-full typo-body-bold text-black">영상 추천</div>
        <div className="flex w-full gap-1.5 flex-col">
          {videos.length > 0
            ? videos.map((v, i) => <ReferenceItem key={i} title={v.videoTitle} url={v.videoUrl} />)
            : [0, 1, 2].map(i => <ReferenceItem key={i} title="" url="" />)}
        </div>
      </div>
      <div className="flex w-full gap-1.5 flex-col">
        <div className="flex w-full typo-body-bold text-black">크리에이터 추천</div>
        <div className="flex w-full gap-1.5 flex-col">
          {creators.length > 0
            ? creators.map((c, i) => (
                <ReferenceItem key={i} title={c.creatorName} url={c.channelUrl} />
              ))
            : [0, 1].map(i => <ReferenceItem key={i} title="" url="" />)}
        </div>
      </div>
    </div>
  );
};

export default CommendList;
