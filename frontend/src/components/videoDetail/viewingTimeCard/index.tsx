import { useState } from 'react';

interface ViewingTimeCardProps {
  isLoading?: boolean;
}

const ViewingTimeCard = ({ isLoading = false }: ViewingTimeCardProps) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  // 임시 데이터 (나중에 props나 store에서 받아올 예정)
  const totalDurationSeconds = 25 * 60; // 영상 전체 길이 (초 단위) - 25분

  // 5등분 데이터 (0분, 5분, 10분, 15분, 20분, 25분 시점의 유지율)
  const retentionData = [100, 85, 60, 50, 45, 43];

  const yLabels = ['0%', '25%', '50%', '75%', '100%'];

  // X축 라벨 5등분
  const segmentCount = retentionData.length - 1;
  const xLabels = retentionData.map((_, i) => {
    const seconds = (totalDurationSeconds / segmentCount) * i;
    const minutes = Math.floor(seconds / 60);
    return `${minutes}분`;
  });

  const formatTime = (index: number) => {
    const seconds = (totalDurationSeconds / segmentCount) * index;
    const min = Math.floor(seconds / 60);
    const sec = Math.round(seconds % 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
  };

  const getY = (percent: number) => {
    return 100 - percent;
  };

  const createPath = () => {
    const width = 100 / segmentCount;
    return retentionData
      .map((percent, i) => {
        const x = i * width;
        const y = getY(percent);
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  };

  const createAreaPath = () => {
    const width = 100 / segmentCount;
    const linePath = retentionData
      .map((percent, i) => {
        const x = i * width;
        const y = getY(percent);
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
    return `${linePath} L 100 100 L 0 100 Z`;
  };

  return (
    <div className="flex w-full h-full px-6 py-8 justify-center items-start gap-3.5 bg-white rounded-xl border-[0.1px] border-[#8257B4]">
      {/* 시청자 유지율 분석 영역 */}
      <div className="flex flex-col flex-1 justify-center items-center gap-5">
        <div className="flex w-full justify-start items-center text-black typo-body4-semibold">
          시청자 유지율 분석
        </div>
        {/* 그래프 영역 */}
        <div className="flex flex-col w-full gap-2">
          <div className="flex w-full">
            {/* Y축 라벨 */}
            <div className="flex flex-col justify-between h-40 pr-2">
              {[...yLabels].reverse().map((label, i) => (
                <div key={i} className="text-black typo-graph text-right">
                  {label}
                </div>
              ))}
            </div>
            {/* 그래프 */}
            <div className="flex-1 relative h-40">
              <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
                {/* Y축 가로 실선 (그리드) */}
                {[0, 25, 50, 75, 100].map((y, i) => (
                  <line
                    key={i}
                    x1="0"
                    y1={y}
                    x2="100"
                    y2={y}
                    stroke="#E0E0E0"
                    strokeWidth="0.5"
                    vectorEffect="non-scaling-stroke"
                  />
                ))}
                {/* Y축 */}
                <line
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="100"
                  stroke="black"
                  strokeWidth="1"
                  vectorEffect="non-scaling-stroke"
                />
                {/* X축 */}
                <line
                  x1="0"
                  y1="100"
                  x2="100"
                  y2="100"
                  stroke="black"
                  strokeWidth="1"
                  vectorEffect="non-scaling-stroke"
                />
                {/* 영역 채우기 */}
                <path d={createAreaPath()} fill="#9F8CFF33" />
                {/* 유지율 선 */}
                <path
                  d={createPath()}
                  fill="none"
                  stroke="#9F8CFF"
                  strokeWidth="2"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
              {/* 호버 영역 - 5등분 포인트별 */}
              {retentionData.map((percent, i) => {
                const xPercent = (i / segmentCount) * 100;
                const yPercent = getY(percent);
                return (
                  <div
                    key={i}
                    className="absolute w-4 h-full cursor-pointer"
                    style={{
                      left: `calc(${xPercent}% - 8px)`,
                      top: 0,
                    }}
                    onMouseEnter={() => setHoverIndex(i)}
                    onMouseLeave={() => setHoverIndex(null)}
                  >
                    {hoverIndex === i && (
                      <>
                        <div
                          className="absolute w-2 h-2 rounded-full bg-[#9F8CFF]"
                          style={{
                            left: '4px',
                            top: `${yPercent}%`,
                            transform: 'translate(-50%, -50%)',
                          }}
                        />
                        <div
                          className="absolute flex flex-col items-center px-3 py-2 rounded-xl text-black whitespace-nowrap z-10 border border-[#6B42FF]"
                          style={{
                            left: '50%',
                            top: `${yPercent}%`,
                            transform: 'translate(-50%, -120%)',
                            background: 'rgba(255, 255, 255, 0.85)',
                            backdropFilter: 'blur(27px)',
                          }}
                        >
                          <div className="typo-body5">평균 시청 지속 시간</div>
                          <div className="typo-body4-semibold">
                            {formatTime(i)} ({percent}%)
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          {/* X축 라벨 */}
          <div className="flex w-full justify-between pl-8">
            {xLabels.map((label, i) => (
              <div key={i} className="text-black typo-graph">
                {label}
              </div>
            ))}
          </div>
        </div>
      </div>
      {/* 주요 이탈 구간 */}
      <div className="flex flex-col w-52 shrink-0 justify-center items-start px-4.5 py-7 gap-4.5 bg-[#F5EFFF33] rounded-xl border-[0.1px] border-[#8257B4]">
        <div className="w-full justify-start items-center text-black typo-body4-semibold">
          주요 이탈 구간
        </div>
        {isLoading ? (
          <div className="text-gray-400 animate-loading-pulse typo-body5">
            이탈 구간을 분석하고 있습니다...
          </div>
        ) : (
          <>
            <div className="flex w-full justify-start items-center text-black typo-body4-semibold">
              0:11 ~ 0:25
            </div>
            <div className="w-full justify-start items-center text-black typo-body5">
              초반 후킹을 강화하면 더 많은 시청자를 붙잡을 수 있어요.
            </div>
            <div className="px-7 py-1 justify-center items-center text-[#8257B4] typo-body6 rounded-lg border border-[#8257B480] cursor-pointer hover:bg-[#8257B410]">
              구간 자세히 보기
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ViewingTimeCard;
