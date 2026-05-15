import BoltIcon from '@/assets/icons/score-icons/video-detail/bolt-icon.svg?react';
import CardItem from '../cardItem';
import useCurrentVideoStore from '@/stores/useCurrentVideoStore';

const RecommendActionCard = () => {
  const videoAnalysis = useCurrentVideoStore(s => s.videoAnalysis);
  const isLoading = useCurrentVideoStore(s => s.isLoading);

  const recommendedActions = videoAnalysis?.recommendedActions;
  const showLoading = isLoading || !recommendedActions;

  return (
    <div className="flex flex-col w-full px-6 py-5 gap-4.5 justify-center items-center bg-white rounded-xl border-[0.1px] border-[#8257B4]">
      <div className="flex w-full justify-start items-center gap-1">
        <BoltIcon className="w-6 h-6" />
        <div className="text-[#6452CE] typo-body4-semibold">추천 액션</div>
      </div>
      <div className="flex flex-col w-full justify-center items-center gap-5">
        {showLoading ? (
          <div className="text-gray-400 animate-loading-pulse typo-body5 py-4">
            추천 액션을 생성하고 있습니다...
          </div>
        ) : recommendedActions.length > 0 ? (
          recommendedActions.map((action, index) => (
            <CardItem
              key={index}
              iconType="Camera"
              title={action.title}
              comment={action.description}
            />
          ))
        ) : (
          <div className="text-gray-400 typo-body5 py-4">추천 액션 데이터 없음</div>
        )}
      </div>
    </div>
  );
};

export default RecommendActionCard;
