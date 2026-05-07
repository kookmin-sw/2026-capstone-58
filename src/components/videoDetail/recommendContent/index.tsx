import ContentItem from './contentItem';

interface RecommendContentItem {
  title: string;
  minExpectedViews: number;
  maxExpectedViews: number;
}

interface RecommendContentProps {
  isLoading?: boolean;
  contents?: RecommendContentItem[];
}

const RecommendContent = ({ isLoading = false, contents }: RecommendContentProps) => {
  const defaultContents: RecommendContentItem[] = [
    {
      title: '외국 프로 선수에게 한국 서버를 시켜봤다.',
      minExpectedViews: 12,
      maxExpectedViews: 18,
    },
    { title: 'K-티모 말고 K-야스오를 보여준다면?', minExpectedViews: 9, maxExpectedViews: 15 },
    { title: '외국인이 본 한국 롤 문화 반응', minExpectedViews: 8, maxExpectedViews: 13 },
  ];

  const displayContents = contents || defaultContents;

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
          displayContents.map((content, index) => (
            <ContentItem
              key={index}
              title={content.title}
              minExpectedViews={content.minExpectedViews}
              maxExpectedViews={content.maxExpectedViews}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default RecommendContent;
