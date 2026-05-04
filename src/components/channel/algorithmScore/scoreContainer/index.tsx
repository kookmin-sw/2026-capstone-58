import { useState } from 'react';
import GraphIcon from '@/assets/icons/score-icons/graph-icon.svg?react';
import TimerIcon from '@/assets/icons/score-icons/timer-icon.svg?react';
import CameraIcon from '@/assets/icons/score-icons/camera-icon.svg?react';
import ScheduleIcon from '@/assets/icons/score-icons/schedule-icon.svg?react';
import { getScoreColors } from '../scoreColors';

const iconMap: Record<string, React.FC<React.SVGProps<SVGSVGElement>>> = {
  '조회수 성장률': GraphIcon,
  '시청 유지율': TimerIcon,
  '업로드 빈도': CameraIcon,
  '콘텐츠 적합도': ScheduleIcon,
};

interface ScoreContainerProps {
  label: string;
  score: number;
  maxScore?: number;
  weight?: number;
  description?: string;
}

const ScoreContainer = ({
  label,
  score,
  maxScore = 100,
  weight,
  description,
}: ScoreContainerProps) => {
  const [hovered, setHovered] = useState(false);
  const percent = Math.min((score / maxScore) * 100, 100);
  const Icon = iconMap[label];
  const { fill, track } = getScoreColors(score);

  return (
    <div className="flex items-center gap-3 self-stretch">
      {Icon && <Icon className="w-6.5 h-6.5 shrink-0" />}
      <div
        className="relative flex w-22 shrink-0 text-sm font-medium leading-[140%] -tracking-wide text-black cursor-default"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        {label}
        {hovered && (weight !== undefined || description) && (
          <div className="absolute -top-14 left-0 px-3 py-2 rounded-lg bg-[#A594F9]/90 text-white text-xs font-medium whitespace-nowrap z-10 transition-all duration-200">
            {description && <div>{description}</div>}
            {weight !== undefined && <div>가중치: {weight}</div>}
          </div>
        )}
      </div>
      <div className="flex-1 h-2.5 rounded-full overflow-hidden" style={{ backgroundColor: track }}>
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${percent}%`, backgroundColor: fill }}
        />
      </div>
      <div className="w-8 text-right text-sm font-bold text-black">{score}</div>
    </div>
  );
};

export default ScoreContainer;
