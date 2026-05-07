import useAIFormStore from '@/stores/useAIFormStore';

const Thumbnail = () => {
  const data = useAIFormStore(s => s.data);
  const thumbnailImage = data?.thumbnail?.thumbnailImage ?? '';
  const thumbnailGuide = data?.thumbnail?.thumbnailGuide ?? '';

  return (
    <div className="inline-flex w-full py-6 pl-6 pr-5 flex-col items-start gap-5 rounded-xl bg-[#fff] border border-[#A594F9]">
      <div className="flex w-full typo-title-bold text-[#0A0A0A] items-stretch">썸네일 가이드</div>
      <div className="flex w-full flex-col gap-4 items-center">
        <div className="w-[80%] aspect-video rounded-xl bg-[#FAFAFA] border border-[#A594F9] overflow-hidden">
          {thumbnailImage ? (
            <img src={thumbnailImage} alt="썸네일" className="w-full h-full object-cover" />
          ) : (
            <div className="flex w-full h-full items-center justify-center text-gray-400 typo-body2 animate-loading-pulse">
              썸네일이 표시됩니다.
            </div>
          )}
        </div>
        <div className="w-full px-3 py-3 rounded-lg typo-body4-semibold text-[#0A0A0A] whitespace-pre-line break-keep leading-6">
          {thumbnailGuide || (
            <span className="animate-loading-pulse text-gray-400">썸네일 가이드가 표시됩니다.</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default Thumbnail;
