import SpeechBubbleIcon from '@/assets/icons/score-icons/speech-bubble-icon.svg?react';
import GuideItem from './guideItem';
import useChannelStore from '@/stores/useChannelStore';

const GuideChannel = () => {
  const data = useChannelStore(s => s.data);
  const guides = data?.guides ?? [];

  return (
    <div className="flex flex-col w-full px-7 py-6 gap-4 justify-center items-center rounded-xl border border-[#A594F9]">
      <div className="flex w-full gap-2 px-1.5 justify-start items-center">
        <SpeechBubbleIcon className="w-7 h-7" />
        <div className="flex w-full text-black typo-title1">
          이렇게 해보세요! {data?.channel?.name ?? 'name'}님 맞춤 CRiT 가이드
        </div>
      </div>
      <div className="flex w-full gap-8 justify-center items-center">
        {guides.length > 0 ? (
          guides.map((guide, i) => (
            <GuideItem key={i} comment={guide.title} subcomment={guide.description} />
          ))
        ) : (
          <div className="text-sm text-gray-400 py-4 animate-loading-pulse">
            가이드 준비 중입니다...
          </div>
        )}
      </div>
    </div>
  );
};

export default GuideChannel;
