import { getScoreColors } from '@/components/channel/algorithmScore/scoreColors';

interface VideoItemProps {
  title: string;
  thumbnailUrl?: string;
  score: number;
  description: string;
}

const VideoItem = ({ title, thumbnailUrl, score, description }: VideoItemProps) => {
  const { fill } = getScoreColors(score);

  return (
    <div className="flex w-full px-7.5 py-6 gap-7.5 self-stretch rounded-xl bg-white border hover:bg-[#F3F0FF] active:bg-[#F3F0FF] border-[#A594F9] hover:border-[#6B42FF] active:border-[#6B42FF]">
      <div className="w-76 shrink-0 aspect-video rounded-lg overflow-hidden">
        {thumbnailUrl ? (
          <img src={thumbnailUrl} alt={title} className="w-full h-full object-cover" />
        ) : (
          <div className="flex w-full h-full items-center justify-center text-gray-400 typo-body2">
            썸네일이 표시됩니다.
          </div>
        )}
      </div>
      <div className="flex flex-col w-full py-3.5 gap-7.5 justify-center items-center">
        <div className="flex w-full justify-start text-black typo-title1">{title}</div>
        <div className="flex flex-col w-full gap-2.5 justify-center items-center">
          <div className="flex w-full justify-start items-center gap-0.5">
            <div className="typo-title1" style={{ color: fill }}>
              {score}
            </div>
            <div className="typo-body1-medium text-black">&nbsp;/ 100점</div>
          </div>
          <div className="flex w-full justify-start text-black typo-body3">{description}</div>
        </div>
      </div>
    </div>
  );
};

export default VideoItem;
