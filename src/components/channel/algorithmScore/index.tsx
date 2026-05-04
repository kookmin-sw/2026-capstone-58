import CircleProgress from './circleProgress';
import ScoreContainer from './scoreContainer';
import BulbIcon from '@/assets/icons/score-icons/bulb-icon.svg?react';

const AlgorithmScore = () => {
  return (
    <div className="flex w-full px-2 py-4 flex-col justify-center items-center gap-2 rounded-xl border border-[#8257B4] self-stretch">
      <div className="flex w-full h-7 px-3 typo-body1-medium text-black">알고리즘 점수</div>
      <div className="flex items-center gap-2 self-stretch">
        <div className="flex items-center justify-center p-3">
          <CircleProgress score={80} rank="상위 42%" />
        </div>
        <div className="flex flex-col w-full gap-2.5 items-start self-stretch">
          <div className="typo-body-bold leading-[140%] tracking-tight text-black">
            점수 구성 요인
          </div>
          <div className="flex flex-col items-center gap-2.5 self-stretch">
            <ScoreContainer label="조회수 성장률" score={79} />
            <ScoreContainer label="시청 유지율" score={65} />
            <ScoreContainer label="업로드 빈도" score={30} />
            <ScoreContainer label="콘텐츠 적합도" score={82} />
          </div>
          <div className="flex w-full px-4 py-2 gap-2.5 items-center self-stretch rounded-xl border border-[#8257B4]">
            <BulbIcon />
            <div className="flex flex-col">
              <div className="typo-body4-semibold text-black">지난 분석 대비 n점 상승했어요!</div>
              <div className="typo-body4-semibold text-black">
                꾸준한 업로드가 도움이 되고 있어요
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlgorithmScore;
