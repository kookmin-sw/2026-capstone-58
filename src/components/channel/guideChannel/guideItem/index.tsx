import CommentIcon from '@/assets/icons/score-icons/comment-icon.svg?react';

interface GuideItemProps {
  comment: string;
  subcomment: string;
}

const GuideItem = ({ comment, subcomment }: GuideItemProps) => {
  return (
    <div className="flex w-full px-5 py-5 justify-start items-start gap-2.5 self-stretch rounded-xl bg-[#F5EFFF]">
      <CommentIcon />
      <div className="flex w-full flex-col gap-1">
        <div className="flex w-full justify-start text-black typo-body4-semibold">{comment}</div>
        <div className="flex w-full justify-start text-black typo-body5">{subcomment}</div>
      </div>
    </div>
  );
};

export default GuideItem;
