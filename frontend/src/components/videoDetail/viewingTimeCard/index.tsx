import { useState } from 'react';
import useCurrentVideoStore from '@/stores/useCurrentVideoStore';

const ViewingTimeCard = () => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const videoAnalysis = useCurrentVideoStore(s => s.videoAnalysis);
  const isLoading = useCurrentVideoStore(s => s.isLoading);

  const audienceRetention = videoAnalysis?.audienceRetention;

  const sections = audienceRetention?.sections ?? [];
  const avgWatchSeconds = audienceRetention?.avgWatchSeconds;
  const mainDropOff = audienceRetention?.mainDropOffSegment;

  const showLoading = isLoading || sections.length === 0;

  // 유지율 데이터
  const retentionData = sections.map(s => s.retentionPercent);
  const xLabels = sections.map(s => s.label);

  const yLabels = ['0%', '25%', '50%', '75%', '100%'];
  const segmentCount = retentionData.length > 1 ? retentionData.length - 1 : 1;

  // 초를 "분:초" 형식으로 변환
  const formatSeconds = (seconds: number) => {
    const min = Math.floor(seconds / 60);
    const sec = Math.round(seconds % 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
  };

  // 평균 시청 시간 포맷 (초 -> "00분 00초")
  const formatAvgWatchTime = (seconds: number) => {
    const min = Math.floor(seconds / 60);
    const sec = Math.round(seconds % 60);
    return `${min}분 ${sec}초`;
  };

  const getY = (percent: number) => {
    return 100 - percent;
  };

  const createPath = () => {
    if (retentionData.length === 0) return '';
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
    if (retentionData.length === 0) return '';
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
              {showLoading ? (
                <div className="flex w-full h-full items-center justify-center text-gray-400 animate-loading-pulse typo-body5">
                  유지율 데이터를 불러오는 중...
                </div>
              ) : (
                <>
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
                  {/* 호버 영역 */}
                  {retentionData.map((percent, i) => {
                    const xPercent = (i / segmentCount) * 100;
                    const yPercent = getY(percent);
                    const section = sections[i];
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
                                {formatSeconds(section.timeSeconds)} ({percent}%)
                              </div>
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
            {showLoading ? (
              <div className="text-gray-400 animate-loading-pulse typo-graph">
                X축 라벨 대기중...
              </div>
            ) : (
              xLabels.map((label, i) => (
                <div key={i} className="text-black typo-graph">
                  {label}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
      {/* 주요 이탈 구간 */}
      <div className="flex flex-col w-52 shrink-0 justify-center items-start px-4.5 py-7 gap-4.5 bg-[#F5EFFF33] rounded-xl border-[0.1px] border-[#8257B4]">
        <div className="w-full justify-start items-center text-black typo-body4-semibold">
          주요 이탈 구간
        </div>
        {showLoading ? (
          <div className="text-gray-400 animate-loading-pulse typo-body5">
            이탈 구간을 분석하고 있습니다...
          </div>
        ) : (
          <>
            {/* 평균 시청 시간 */}
            {avgWatchSeconds !== undefined && avgWatchSeconds > 0 && (
              <div className="w-full text-[#6452CE] typo-body5">
                평균 시청 시간: {formatAvgWatchTime(avgWatchSeconds)}
              </div>
            )}
            <div className="flex w-full justify-start items-center text-black typo-body4-semibold">
              {mainDropOff
                ? `${formatSeconds(mainDropOff.startSeconds)} ~ ${formatSeconds(mainDropOff.endSeconds)}`
                : '이탈 구간 데이터 없음'}
            </div>
            <div className="w-full justify-start items-center text-black typo-body5">
              {mainDropOff?.description ?? '이탈 구간 설명 데이터 없음'}
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
