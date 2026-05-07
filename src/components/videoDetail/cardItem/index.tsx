import AlarmIcon from '@/assets/icons/score-icons/video-detail/purple-alarm-icon.svg?react';
import PictureIcon from '@/assets/icons/score-icons/video-detail/picture-icon.svg?react';
import CameraIcon from '@/assets/icons/score-icons/video-detail/camera-icon.svg?react';

interface CardItemProps {
  iconType: 'Alarm' | 'Picture' | 'Camera';
  title: string;
  comment: string;
}

const iconMap = {
  Alarm: AlarmIcon,
  Picture: PictureIcon,
  Camera: CameraIcon,
};

const CardItem = ({ iconType, title, comment }: CardItemProps) => {
  const Icon = iconMap[iconType];

  return (
    <div className="flex w-full px-5.5 py-4.5 justify-center items-start gap-2.5 bg-[#F5EFFF33] rounded-xl border-[0.1px] border-[#8257B4]">
      <div className="p-1 justify-center items-center bg-[#D9D2FF] rounded-md">
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex flex-col w-full justify-center items-center gap-1">
        <div className="w-full justify-start items-center text-black typo-body4-semibold">
          {title}
        </div>
        <div className="w-full justify-start items-center text-black typo-body5">{comment}</div>
      </div>
    </div>
  );
};

export default CardItem;
