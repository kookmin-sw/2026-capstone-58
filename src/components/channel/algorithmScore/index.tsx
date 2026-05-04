import CircleProgress from './circleProgress';
import ScoreContainer from './scoreContainer';
import BulbIcon from '@/assets/icons/score-icons/bulb-icon.svg?react';
import useChannelStore from '@/stores/useChannelStore';

const AlgorithmScore = () => {
  const data = useChannelStore(s => s.data);
  const score = data?.channelScore;
  const factors = score?.factors ?? [];

  return (
    <div className="flex w-full px-2 py-4 flex-col justify-center items-center gap-2 rounded-xl border border-[#A594F9] self-stretch">
      <div className="flex w-full h-7 px-3 typo-body1-medium text-black">알고리즘 점수</div>
      <div className="flex items-center gap-2 self-stretch">
        <div className="flex items-center justify-center p-3">
          <CircleProgress score={score?.overall ?? 0} rank={`상위 ${score?.topPercent ?? 0}%`} />
        </div>
        <div className="flex flex-col w-full justify-between items-start self-stretch">
          <div className="typo-body-bold leading-[140%] tracking-tight text-black">
            점수 구성 요인
          </div>
          <div className="flex flex-col items-center gap-2.5 self-stretch">
            {factors.length > 0 ? (
              factors.map((f, i) => (
                <ScoreContainer
                  key={i}
                  label={f.name}
                  score={f.score}
                  weight={f.weight}
                  description={f.description}
                />
              ))
            ) : (
              <div className="text-sm text-gray-400 py-4 animate-loading-pulse">
                점수 산정 중입니다...
              </div>
            )}
          </div>
          <div className="flex w-full px-4 py-2 gap-2.5 items-center self-stretch rounded-xl border border-[#A594F9]">
            <BulbIcon />
            <div className="flex flex-col">
              <div className="typo-body4-semibold text-black">
                {score?.comment ?? (
                  <span className="animate-loading-pulse">분석 결과가 표시됩니다.</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlgorithmScore;
