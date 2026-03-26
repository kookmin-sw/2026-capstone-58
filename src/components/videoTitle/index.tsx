import VideoTitleItem from '@/components/videoTitle/videoTitleItem';

const videoTitle = () => {
  return (
    <div className="inline-flex w-full py-6 pl-6 pr-5 flex-col items-start gap-5 rounded-xl bg-[#fff] border border-[#0000004F]">
      <div className="flex w-full typo-title-bold text-[#0A0A0A] items-stretch">AI 추천 제목</div>
      <VideoTitleItem title="최종 합격..💥 출근 전 일상 브이로그 (평균 조회수 상승: +22%)" />
      <VideoTitleItem title="[vlog] 갓생사는 직장인 일상 브이로그 ⏰ (예상 클릭률: 10.5%)" />
      <VideoTitleItem title="회사 들어간지 2주차 신입의 브이로그 💦 (예상 시청 지속 시간: 4:30)" />
    </div>
  );
};

export default videoTitle;
