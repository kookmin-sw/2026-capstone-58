import TriangleIcon from '@/assets/icons/score-icons/triangle-icon.svg?react';
import VideoIcon from '@/assets/icons/score-icons/video-icon.svg?react';
import CameraIcon from '@/assets/icons/score-icons/camera-icon.svg?react';
import TimerIcon from '@/assets/icons/score-icons/timer-icon.svg?react';
import GraphIcon from '@/assets/icons/score-icons/graph-icon.svg?react';

const iconMap: Record<string, React.FC<React.SVGProps<SVGSVGElement>>> = {
  '평균 조회수': VideoIcon,
  '업로드 빈도': CameraIcon,
  '평균 시청 지속 시간': TimerIcon,
  '구독자 증가수': GraphIcon,
};

interface SummaryContainerProps {
  label: string;
  value: number;
  changePercent: number;
}

const formatValue = (label: string, value: number): string => {
  switch (label) {
    case '평균 조회수':
      return value >= 10000 ? `${(value / 10000).toFixed(1)}만` : value.toLocaleString();
    case '업로드 빈도':
      return `주 ${value}회`;
    case '평균 시청 지속 시간': {
      const min = Math.floor(value / 60);
      const sec = Math.round(value % 60);
      return `${min}분 ${sec}초`;
    }
    case '구독자 증가수':
      return value >= 10000
        ? `+${(value / 10000).toFixed(1)}만 명`
        : `+${value.toLocaleString()} 명`;
    default:
      return String(value);
  }
};

const SummaryContainer = ({ label, value, changePercent }: SummaryContainerProps) => {
  const isUp = changePercent > 0;
  const isDown = changePercent < 0;
  const isNeutral = changePercent === 0;
  const Icon = iconMap[label];

  return (
    <div className="flex w-full h-full px-4 py-4.5 gap-4 rounded-xl bg-[#F5EFFF]">
      <div className="flex flex-col items-center justify-start">
        {Icon && <Icon className="w-8 h-8" />}
      </div>
      <div className="flex flex-1 flex-col justify-center items-start gap-2.5">
        <div className="flex w-full text-black text-sm font-medium leading-[140%] tracking-wide">
          {label}
        </div>
        <div className="flex w-full justify-between items-center">
          <div className="text-black text-xl font-semibold leading-[140%] tracking-wide">
            {formatValue(label, value)}
          </div>
          <div
            className={`flex px-2 py-1 w-13 gap-0.5 justify-center items-center rounded-xl ${isUp ? 'bg-[#DEF3E195]' : isDown ? 'bg-[#FFEFEF]' : 'bg-[#FFFCEF]'}`}
          >
            {isUp && <TriangleIcon className="w-2.5 h-2.5 text-[#5AC467]" />}
            {isDown && <TriangleIcon className="w-2.5 h-2.5 text-[#FF0000] rotate-180" />}
            <div
              className={`text-xs font-semibold ${isUp ? 'text-[#5AC467]' : isDown ? 'text-[#FF0000]' : 'text-[#FF9D00]'}`}
            >
              {isNeutral ? '보통' : `${Math.abs(changePercent)}%`}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SummaryContainer;
