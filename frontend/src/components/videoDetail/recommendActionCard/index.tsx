import BoltIcon from '@/assets/icons/score-icons/video-detail/bolt-icon.svg?react';
import CardItem from '../cardItem';

interface RecommendAction {
  iconType: 'Alarm' | 'Picture' | 'Camera';
  title: string;
  comment: string;
}

interface RecommendActionCardProps {
  isLoading?: boolean;
  actions?: RecommendAction[];
}

const RecommendActionCard = ({ isLoading = false, actions }: RecommendActionCardProps) => {
  const defaultActions: RecommendAction[] = [
    {
      iconType: 'Camera',
      title: '비슷한 주제로 후속 영상 만들기',
      comment: '이 주제는 시청자 반응이 좋았어요.',
    },
    {
      iconType: 'Camera',
      title: 'Shorts로 재가공하기',
      comment: '핵심 장면을 shorts로 만들어 유입을 늘려보세요.',
    },
    {
      iconType: 'Camera',
      title: '썸네일 A/B 테스트 진행하기',
      comment: '다른 버전의 썸네일로 CTR을 더 높여보세요.',
    },
  ];

  const displayActions = actions || defaultActions;

  return (
    <div className="flex flex-col w-full px-6 py-5 gap-4.5 justify-center items-center bg-white rounded-xl border-[0.1px] border-[#8257B4]">
      <div className="flex w-full justify-start items-center gap-1">
        <BoltIcon className="w-6 h-6" />
        <div className="text-[#6452CE] typo-body4-semibold">추천 액션</div>
      </div>
      <div className="flex flex-col justify-center items-center gap-5">
        {isLoading ? (
          <div className="text-gray-400 animate-loading-pulse typo-body5 py-4">
            추천 액션을 생성하고 있습니다...
          </div>
        ) : (
          displayActions.map((action, index) => (
            <CardItem
              key={index}
              iconType={action.iconType}
              title={action.title}
              comment={action.comment}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default RecommendActionCard;
