import SummaryContainer from './summaryContainer';

const SummaryChannel = () => {
  return (
    <div className="flex w-full px-2 py-4 flex-col justify-center items-center gap-2 rounded-xl border border-[#8257B4]">
      <div className="flex w-full h-7 px-3 typo-body1-medium text-black">나의 채널 요약</div>
      <div className="grid grid-cols-2 gap-4 w-full px-3 pb-4">
        <SummaryContainer label="평균 조회수" value={134000} changePercent={3.2} />
        <SummaryContainer label="업로드 빈도" value={1.8} changePercent={0} />
        <SummaryContainer label="평균 시청 지속 시간" value={208} changePercent={3.2} />
        <SummaryContainer label="구독자 증가수" value={24000} changePercent={3.2} />
      </div>
    </div>
  );
};

export default SummaryChannel;
