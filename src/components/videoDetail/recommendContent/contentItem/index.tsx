import BulbIcon from '@/assets/icons/score-icons/video-detail/purple-bulb-icon.svg?react';

interface ContentItemProps {
  title: string;
  minExpectedViews: number;
  maxExpectedViews: number;
}

const ContentItem = ({ title, minExpectedViews, maxExpectedViews }: ContentItemProps) => {
  return (
    <div className="flex flex-col w-full px-5.5 py-4.5 justify-center items-center gap-3 rounded-xl border-[0.5px] border-[#8257B4]">
      <div className="flex w-full justify-between items-center gap-2">
        <div className="flex justify-start items-start gap-2.5">
          <BulbIcon />
          <div className="flex flex-col gap-1.5 w-full justify-center items-center">
            <div className="w-40 justify-start items-center text-black typo-body4-semibold">
              {title}
            </div>
            <div className="w-full justify-start items-center text-black typo-body5">
              예상 조회수 {minExpectedViews}만 ~ {maxExpectedViews}만
            </div>
          </div>
        </div>
        <div className="px-4.5 py-1 justify-center items-center rounded-xl border-[0.5px] border-[#8257B4] shadow-[0_1px_4px_0_rgba(0,0,0,0.25)] text-[#4F378A] typo-body6 shrink-0">
          아이디어
        </div>
      </div>
      <div className="px-23 py-1 justify-center items-center rounded-xl border-[0.5px] border-[#8257B4] shadow-[0_1px_4px_0_rgba(0,0,0,0.25)] text-[#4F378A] typo-body6">
        영상 추천
      </div>
    </div>
  );
};

export default ContentItem;
