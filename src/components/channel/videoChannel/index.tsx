import VideoItem from './videoItem';

const videoChannel = () => {
  return (
    <div className="flex flex-col w-full justify-center items-center">
      <div className="flex w-full justify-start">
        <div className="flex px-16 py-3 justify-center typo-body1-medium rounded-t-xl border border-[#F5EFFF] bg-[#F5EFFF]">
          내 영상
        </div>
        <div className="flex px-16 py-3 justify-center typo-body1-medium rounded-t-xl border border-[#F5EFFF]">
          비교
        </div>
      </div>
      <div className="flex w-full h-266 px-6 py-11 justify-center items-center rounded-tr-xl rounded-b-xl bg-[#F5EFFF]">
        <div className="flex flex-col w-full h-full overflow-y-auto gap-7.5 pr-4 script-scroll">
          <VideoItem
            title="외국 프로 선수에게 보여준 K-티모 맛"
            score={92}
            description="CTR 95점, 시청 지속 시간 88점, 추천 확장성 92점"
          />
          <VideoItem
            title="외국 프로 선수에게 보여준 K-티모 맛"
            score={32}
            description="CTR 95점, 시청 지속 시간 88점, 추천 확장성 92점"
          />
          <VideoItem
            title="외국 프로 선수에게 보여준 K-티모 맛"
            score={2}
            description="CTR 95점, 시청 지속 시간 88점, 추천 확장성 92점"
          />
          <VideoItem
            title="외국 프로 선수에게 보여준 K-티모 맛"
            score={92}
            description="CTR 95점, 시청 지속 시간 88점, 추천 확장성 92점"
          />
          <VideoItem
            title="외국 프로 선수에게 보여준 K-티모 맛"
            score={92}
            description="CTR 95점, 시청 지속 시간 88점, 추천 확장성 92점"
          />
        </div>
      </div>
    </div>
  );
};

export default videoChannel;
