import SummaryContainer from './summaryContainer';
import useChannelStore from '@/stores/useChannelStore';

const SummaryChannel = () => {
  const data = useChannelStore(s => s.data);
  const summary = data?.summary;

  return (
    <div className="flex w-full px-2 py-4 flex-col justify-center items-center gap-2 rounded-xl border border-[#A594F9]">
      <div className="flex w-full h-7 px-3 typo-body1-medium text-black">나의 채널 요약</div>
      <div className="grid grid-cols-2 gap-4 w-full px-3 pb-4">
        <SummaryContainer
          label="평균 조회수"
          value={summary?.avgViewCount ?? 0}
          changePercent={summary?.avgViewCountChange ?? 0}
        />
        <SummaryContainer
          label="업로드 빈도"
          value={summary?.uploadFrequencyPerWeek ?? 0}
          changePercent={summary?.uploadFrequencyChange ?? 0}
        />
        <SummaryContainer
          label="평균 시청 지속 시간"
          value={summary?.avgWatchDurationSeconds ?? 0}
          changePercent={summary?.avgWatchDurationChange ?? 0}
        />
        <SummaryContainer
          label="구독자 증가수"
          value={summary?.subscriberChange ?? 0}
          changePercent={summary?.subscriberChangePercent ?? 0}
        />
      </div>
    </div>
  );
};

export default SummaryChannel;
