import { useState } from 'react';
import ReasonContainer from './reasonContainer';
import useCurrentVideoStore from '@/stores/useCurrentVideoStore';

const ViewGrowthCard = () => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const videoAnalysis = useCurrentVideoStore(s => s.videoAnalysis);
  const isLoading = useCurrentVideoStore(s => s.isLoading);

  const scoreBasis = videoAnalysis?.scoreBasis;
  const viewGrowthData = videoAnalysis?.viewGrowthData;
  const showLoading = isLoading || !viewGrowthData;

  // 데이터 변환 (API: views -> 그래프용)
  const videoData = viewGrowthData?.video?.map(d => d.views) ?? [];
  const avgData = viewGrowthData?.channelAvg?.map(d => d.avgViews) ?? [];
  const days = viewGrowthData?.video?.map(d => `${d.day + 1}일`) ?? [];

  // 데이터가 없으면 빈 그래프
  const hasData = videoData.length > 0 && avgData.length > 0;

  // Y축 자동 계산
  const dataMax = hasData ? Math.max(...videoData, ...avgData) : 100000;
  const getInterval = (max: number) => {
    if (max <= 100000) return 10000;
    if (max <= 500000) return 50000;
    if (max <= 1000000) return 100000;
    if (max <= 5000000) return 500000;
    return 1000000;
  };

  const interval = getInterval(dataMax);
  const maxValue = Math.ceil(dataMax / interval) * interval || 100000;
  const yLabelCount = maxValue / interval + 1;
  const yLabels = Array.from({ length: yLabelCount }, (_, i) => i * interval);

  const formatLabel = (value: number) => {
    if (value === 0) return '0';
    if (value >= 10000) return `${value / 10000}만`;
    return value.toLocaleString();
  };

  const getY = (value: number) => {
    return 100 - (value / maxValue) * 100;
  };

  const createPath = (data: number[]) => {
    if (data.length === 0) return '';
    const width = 100 / (data.length - 1);
    return data
      .map((value, i) => {
        const x = i * width;
        const y = getY(value);
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  };

  // 호버 시 표시할 값 포맷
  const formatValue = (value: number) => {
    if (value >= 10000) {
      return `${(value / 10000).toFixed(1)}만`;
    }
    return value.toLocaleString();
  };

  return (
    <div className="flex w-full px-6 py-6 justify-center items-start gap-4 bg-white rounded-xl border-[0.1px] border-[#8257B4]">
      <div className="flex flex-col w-full justify-center items-center gap-4">
        <div className="flex w-full justify-start items-center text-[#6452CE] typo-body4-semibold">
          점수 산정 근거
        </div>
        <div className="flex flex-col w-full justify-center items-center gap-2.5">
          {showLoading || !scoreBasis ? (
            <>
              <ReasonContainer isLoading />
              <ReasonContainer isLoading />
              <ReasonContainer isLoading />
            </>
          ) : scoreBasis.length > 0 ? (
            scoreBasis.map((comment, index) => <ReasonContainer key={index} comment={comment} />)
          ) : (
            <ReasonContainer comment="점수 산정 근거가 없습니다." />
          )}
        </div>
      </div>
      <div className="w-0.25 h-40 bg-[#8257B433]" />
      <div className="flex flex-col w-full justify-center items-center gap-6">
        <div className="flex w-full justify-start items-center gap-1">
          <div className="text-black typo-body4-semibold">조회수 성장 추이</div>
          <div className="text-[#8B8484] typo-body5">(업로드 후 7일)</div>
        </div>
        <div className="flex flex-col w-full gap-2.5">
          <div className="flex w-full justify-center items-center gap-4">
            <div className="flex items-center gap-1">
              <div className="w-3 h-0.5 bg-[#9F8CFF]" />
              <div className="text-[#8B8484] typo-body5">이 영상</div>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-0.5 bg-[#8B8484]" />
              <div className="text-[#8B8484] typo-body5">채널 평균</div>
            </div>
          </div>
          <div className="flex w-full">
            {/* Y축 라벨 */}
            <div className="flex flex-col justify-between h-32 pr-2">
              {[...yLabels].reverse().map((value, i) => (
                <div key={i} className="text-black typo-graph text-right">
                  {formatLabel(value)}
                </div>
              ))}
            </div>
            {/* 그래프 영역 */}
            <div className="flex-1 relative h-32">
              {showLoading ? (
                <div className="flex w-full h-full items-center justify-center text-gray-400 animate-loading-pulse typo-body5">
                  그래프 데이터를 불러오는 중...
                </div>
              ) : (
                <>
                  <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-full">
                    {/* Y축 가로 실선 (그리드) */}
                    {yLabels.map((_, i) => {
                      const y = (i / (yLabels.length - 1)) * 100;
                      return (
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
                      );
                    })}
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
                    {/* 채널 평균 선 (점선) */}
                    {hasData && (
                      <path
                        d={createPath(avgData)}
                        fill="none"
                        stroke="#8B8484"
                        strokeWidth="1"
                        strokeDasharray="4 2"
                        vectorEffect="non-scaling-stroke"
                      />
                    )}
                    {/* 이 영상 선 */}
                    {hasData && (
                      <path
                        d={createPath(videoData)}
                        fill="none"
                        stroke="#9F8CFF"
                        strokeWidth="2"
                        vectorEffect="non-scaling-stroke"
                      />
                    )}
                  </svg>
                  {/* 호버 영역 */}
                  {hasData &&
                    videoData.map((value, i) => {
                      const xPercent = (i / (videoData.length - 1)) * 100;
                      const yPercent = getY(value);
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
                                className="absolute px-2 py-1 rounded-xl text-black typo-body5 whitespace-nowrap z-10 border border-[#6B42FF]"
                                style={{
                                  left: '50%',
                                  top: `${yPercent}%`,
                                  transform: 'translate(-50%, -130%)',
                                  background: 'rgba(255, 255, 255, 0.85)',
                                  backdropFilter: 'blur(27px)',
                                }}
                              >
                                {formatValue(value)}
                              </div>
                            </>
                          )}
                        </div>
                      );
                    })}
                </>
              )}
            </div>
          </div>
          {/* X축 라벨 */}
          <div className="flex w-full justify-between pl-8">
            {showLoading
              ? ['1일', '2일', '3일', '4일', '5일', '6일', '7일'].map((day, i) => (
                  <div key={i} className="text-black typo-graph">
                    {day}
                  </div>
                ))
              : days.map((day, i) => (
                  <div key={i} className="text-black typo-graph">
                    {day}
                  </div>
                ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ViewGrowthCard;
