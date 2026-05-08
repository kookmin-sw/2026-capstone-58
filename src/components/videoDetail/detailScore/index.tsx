import DetailScoreContainer from './detailScoreContainer';

interface DetailScoreProps {
  isLoading?: boolean;
}

const DetailScore = ({ isLoading = false }: DetailScoreProps) => {
  return (
    <div className="flex w-full gap-7 justify-center items-center">
      <DetailScoreContainer
        title="CTR (클릭률)"
        score={76}
        topPercent={5}
        avgDiff={3.2}
        content="클릭을 유도하는 썸네일과 제목이 효과적이었습니다."
        isLoading={isLoading}
      />
      <DetailScoreContainer
        title="시청 지속 시간"
        score={88}
        topPercent={20}
        avgDiff={3.2}
        content="클릭을 유도하는 썸네일과 제목이 효과적이었습니다."
        isLoading={isLoading}
      />
      <DetailScoreContainer
        title="추천 확장성"
        score={22}
        topPercent={87}
        avgDiff={-9.2}
        content="클릭을 유도하는 썸네일과 제목이 효과적이었습니다."
        isLoading={isLoading}
      />
    </div>
  );
};

export default DetailScore;
