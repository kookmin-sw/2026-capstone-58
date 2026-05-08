import SlackIcon from '@/assets/icons/score-icons/video-detail/slack-icon.svg?react';
import CardItem from '../cardItem';

interface ImprovementPoint {
  iconType: 'Alarm' | 'Picture' | 'Camera';
  title: string;
  comment: string;
}

interface ImprovementPointCardProps {
  isLoading?: boolean;
  points?: ImprovementPoint[];
}

const ImprovementPointCard = ({ isLoading = false, points }: ImprovementPointCardProps) => {
  const defaultPoints: ImprovementPoint[] = [
    {
      iconType: 'Alarm',
      title: '초반 10초 후킹이 약해요',
      comment: '11초~25초 구간에서 이탈률이 평균보다 높습니다.',
    },
    {
      iconType: 'Picture',
      title: '썸네일에 핵심 메시지가 더 명확할 수 있어요.',
      comment: '현재 썸네일 대비 클릭률을 더 끌어올릴 여지가 있어요.',
    },
  ];

  const displayPoints = points || defaultPoints;

  return (
    <div className="flex flex-col w-full px-6 py-5 gap-4.5 justify-center items-center bg-white rounded-xl border-[0.1px] border-[#8257B4]">
      <div className="flex w-full justify-start items-center gap-1">
        <SlackIcon className="w-6 h-6" />
        <div className="text-[#6452CE] typo-body4-semibold">개선 포인트</div>
      </div>
      <div className="flex flex-col justify-center items-center gap-5">
        {isLoading ? (
          <div className="text-gray-400 animate-loading-pulse typo-body5 py-4">
            개선 포인트를 분석하고 있습니다...
          </div>
        ) : (
          displayPoints.map((point, index) => (
            <CardItem
              key={index}
              iconType={point.iconType}
              title={point.title}
              comment={point.comment}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default ImprovementPointCard;
