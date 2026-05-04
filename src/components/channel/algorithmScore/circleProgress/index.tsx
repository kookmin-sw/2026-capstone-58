import { getScoreColors } from '../scoreColors';

interface CircleProgressProps {
  score: number;
  maxScore?: number;
  rank?: string;
}

const CircleProgress = ({ score, maxScore = 100, rank }: CircleProgressProps) => {
  const size = 160;
  const strokeWidth = 14;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const percent = score / maxScore;
  const offset = circumference * (1 - percent);
  const { fill, track } = getScoreColors(score);

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={track}
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={fill}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-4xl font-bold text-black">{score}</span>
        <span className="text-sm text-gray-400">/{maxScore}</span>
        {rank && (
          <span
            className="mt-1 px-2 py-0.5 rounded-full text-xs font-semibold"
            style={{ backgroundColor: track, color: fill }}
          >
            {rank}
          </span>
        )}
      </div>
    </div>
  );
};

export default CircleProgress;
