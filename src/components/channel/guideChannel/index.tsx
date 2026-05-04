import SpeechBubbleIcon from '@/assets/icons/score-icons/speech-bubble-icon.svg?react';
import GuideItem from './guideItem';

const defaultGuides = [
  { comment: '업로드 주기 늘리기', subcomment: '주 2회 업로드 시 성장률이 20% 높아져요!' },
  {
    comment: '총 영상 시간 늘리기',
    subcomment:
      '동일 카테고리 영상 대비 영상시간이 길어요\n너무 긴 영상은 시청 유지율을 떨어뜨려요',
  },
  {
    comment: '총 영상 시간 늘리기',
    subcomment:
      '동일 카테고리 영상 대비 영상시간이 길어요\n너무 긴 영상은 시청 유지율을 떨어뜨려요',
  },
];

const GuideChannel = () => {
  return (
    <div className="flex flex-col w-full px-7 py-6 gap-4 justify-center items-center rounded-xl border border-[#8257B4]">
      <div className="flex w-full gap-2 px-1.5 justify-start items-center">
        <SpeechBubbleIcon className="w-7 h-7" />
        <div className="flex w-full text-black typo-title1">
          이렇게 해보세요! name님 맞춤 CRiT 가이드
        </div>
      </div>
      <div className="flex w-full gap-8 justify-center items-center">
        {defaultGuides.map((guide, i) => (
          <GuideItem key={i} comment={guide.comment} subcomment={guide.subcomment} />
        ))}
      </div>
    </div>
  );
};

export default GuideChannel;
