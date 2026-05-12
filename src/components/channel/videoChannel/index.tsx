import VideoItem from './videoItem';
import useChannelStore from '@/stores/useChannelStore';
import useCurrentVideoStore from '@/stores/useCurrentVideoStore';

interface VideoChannelProps {
  onVideoClick?: () => void;
}

const VideoChannel = ({ onVideoClick }: VideoChannelProps) => {
  const data = useChannelStore(s => s.data);
  const setVideoId = useCurrentVideoStore(s => s.setVideoId);
  const videos = data?.percentileVideoAnalysis ?? [];

  const handleVideoClick = (video: (typeof videos)[0]) => {
    setVideoId(video.videoId);
    onVideoClick?.();
  };

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
          {videos.length > 0 ? (
            videos.map((v, i) => (
              <VideoItem
                key={i}
                title={v.title}
                thumbnailUrl={v.thumbnailUrl}
                score={v.percentileScore}
                description={v.reason}
                onClick={() => handleVideoClick(v)}
              />
            ))
          ) : (
            <div className="flex w-full h-full items-center justify-center text-gray-400 typo-body2 animate-loading-pulse">
              영상 데이터를 불러오는 중입니다...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoChannel;
