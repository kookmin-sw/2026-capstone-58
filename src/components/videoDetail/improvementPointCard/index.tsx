import SlackIcon from '@/assets/icons/score-icons/video-detail/slack-icon.svg?react';
import CardItem from '../cardItem';
import useCurrentVideoStore from '@/stores/useCurrentVideoStore';

const ImprovementPointCard = () => {
  const videoAnalysis = useCurrentVideoStore(s => s.videoAnalysis);
  const isLoading = useCurrentVideoStore(s => s.isLoading);

  const improvements = videoAnalysis?.improvements;
  const showLoading = isLoading || !improvements;

  // 기본 아이콘 타입 순환
  const iconTypes: ('Alarm' | 'Picture' | 'Camera')[] = ['Alarm', 'Picture', 'Camera'];

  return (
    <div className="flex flex-col w-full px-6 py-5 gap-4.5 justify-center items-center bg-white rounded-xl border-[0.1px] border-[#8257B4]">
      <div className="flex w-full justify-start items-center gap-1">
        <SlackIcon className="w-6 h-6" />
        <div className="text-[#6452CE] typo-body4-semibold">개선 포인트</div>
      </div>
      <div className="flex flex-col w-full justify-center items-center gap-5">
        {showLoading ? (
          <div className="text-gray-400 animate-loading-pulse typo-body5 py-4">
            개선 포인트를 분석하고 있습니다...
          </div>
        ) : improvements.length > 0 ? (
          improvements.map((point, index) => (
            <CardItem
              key={index}
              iconType={iconTypes[index % iconTypes.length]}
              title={point.title}
              comment={point.description}
            />
          ))
        ) : (
          <div className="text-gray-400 typo-body5 py-4">개선 포인트 데이터 없음</div>
        )}
      </div>
    </div>
  );
};

export default ImprovementPointCard;
