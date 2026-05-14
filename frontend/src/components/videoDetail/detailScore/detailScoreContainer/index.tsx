import InfoIcon from '@/assets/icons/score-icons/video-detail/info-icon.svg?react';
import ClickIcon from '@/assets/icons/score-icons/video-detail/click-icon.svg?react';
import AlarmIcon from '@/assets/icons/score-icons/video-detail/orange-alarm-icon.svg?react';
import StarIcon from '@/assets/icons/score-icons/video-detail/star-icon.svg?react';

interface ScoreContainerProps {
  title: string;
  score?: number;
  topPercent?: number;
  avgDiff?: number;
  content?: string;
  isLoading?: boolean;
}

const titleConfig: Record<
  string,
  {
    Icon: React.FC<React.SVGProps<SVGSVGElement>>;
    bgColor: string;
    badgeBg: string;
    textColor: string;
    barFill: string;
    barTrack: string;
  }
> = {
  'CTR (클릭률)': {
    Icon: ClickIcon,
    bgColor: 'bg-[#DEF3E195]',
    badgeBg: 'bg-[#DEF3E195]',
    textColor: 'text-[#5AC467]',
    barFill: '#5AC467',
    barTrack: '#DEF3E1',
  },
  '시청 지속 시간': {
    Icon: AlarmIcon,
    bgColor: 'bg-[#FFFCEF]',
    badgeBg: 'bg-[#FFFCEF]',
    textColor: 'text-[#FF9D00]',
    barFill: '#FF9D00',
    barTrack: '#FFFCEF',
  },
  '추천 확장성': {
    Icon: StarIcon,
    bgColor: 'bg-[#FFEFEF]',
    badgeBg: 'bg-[#FFEFEF]',
    textColor: 'text-[#FF0000]',
    barFill: '#FF0000',
    barTrack: '#FFEFEF',
  },
};

const DetailScoreContainer = ({
  title,
  score = 0,
  topPercent = 0,
  avgDiff = 0,
  content,
  isLoading = false,
}: ScoreContainerProps) => {
  const config = titleConfig[title];
  const Icon = config.Icon;

  return (
    <div className="flex flex-col w-full px-8 py-7 gap-4 justify-start items-center rounded-xl bg-white border-[0.1px] border-[#8257B4]">
      <div className="flex w-full justify-start items-start gap-2 rounded-xl">
        <div className={`flex justify-center items-center p-3 rounded-xl ${config.bgColor}`}>
          <Icon className="w-7 h-7" />
        </div>
        <div className="flex flex-col w-full justify-center items-center gap-4 py-3 pr-3">
          <div className="flex w-full justify-start items-center gap-1">
            <div className="text-black typo-body4-semibold">{title}</div>
            <InfoIcon className="w-3.5 h-3.5" />
          </div>
          <div className="flex w-full justify-between items-end gap-5 self-stretch">
            <div className="flex justify-center items-center">
              {isLoading ? (
                <div className="text-gray-400 animate-loading-pulse typo-title1">--</div>
              ) : (
                <div className={`typo-title1 ${config.textColor}`}>{score}</div>
              )}
              <div className="typo-body2 text-black">&nbsp;/ 100</div>
            </div>
            <div
              className={`flex justify-center items-center px-3 py-1 rounded-xl ${config.badgeBg} ${config.textColor} typo-body6`}
            >
              {isLoading ? (
                <span className="animate-loading-pulse">계산 중</span>
              ) : (
                `상위 ${topPercent}%`
              )}
            </div>
          </div>
        </div>
      </div>
      <div className="w-full h-2 rounded-full" style={{ backgroundColor: config.barTrack }}>
        <div
          className="h-2 rounded-full transition-all duration-500"
          style={{ width: isLoading ? '0%' : `${score}%`, backgroundColor: config.barFill }}
        />
      </div>
      <div className="flex w-full justify-start items-center">
        <div
          className={`flex px-3 py-1 justify-center items-center rounded-xl ${config.bgColor} ${config.textColor} typo-body6`}
        >
          {isLoading ? (
            <span className="animate-loading-pulse">평균 대비 계산 중</span>
          ) : (
            `평균 대비 ${avgDiff >= 0 ? '+' : ''} ${avgDiff}%`
          )}
        </div>
      </div>
      <div className="flex w-full justify-start items-center text-black typo-body5">
        {isLoading ? (
          <span className="text-gray-400 animate-loading-pulse">
            분석 결과를 불러오는 중입니다...
          </span>
        ) : (
          content || ''
        )}
      </div>
    </div>
  );
};

export default DetailScoreContainer;
