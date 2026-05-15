import ContentItem from './contentItem';
import useCurrentVideoStore from '@/stores/useCurrentVideoStore';

const RecommendContent = () => {
  const isLoading = useCurrentVideoStore(s => s.isLoading);

  // 이 컴포넌트는 API 응답에 해당 데이터가 없음
  // 나중에 API에 추가되면 videoAnalysis에서 가져오면 됨

  return (
    <div className="flex flex-col w-full px-6 py-7 justify-center items-start gap-3.5 bg-white rounded-xl border-[0.1px] border-[#8257B4]">
      <div className="w-full justify-start items-center text-black typo-body4-semibold">
        이어서 만들면 좋은 콘텐츠
      </div>
      <div className="flex w-full justify-center items-center gap-5">
        {isLoading ? (
          <div className="flex w-full justify-center items-center py-8 text-gray-400 animate-loading-pulse typo-body5">
            추천 콘텐츠를 생성하고 있습니다...
          </div>
        ) : (
          <div className="flex w-full justify-center items-center py-8 text-gray-400 typo-body5">
            추천 콘텐츠 데이터 없음 (API 미구현)
          </div>
        )}
      </div>
    </div>
  );
};

export default RecommendContent;
