import VideoTitle from '@/components/videoTitle';
import Thumbnail from '@/components/thumbnail';
import ScriptEditor from '../scriptEditor';

const formAnswer = () => {
  return (
    <div className="flex w-250 pt-12 py-22 px-11 flex-col justify-start items-center gap-10 rounded-xl bg-[#F5EFFF]">
      <div className="flex w-full h-6 typo-h1 text-[#0A0A0A]">영상 기획 카드</div>
      <div className="flex w-full gap-4 justify-start">
        <VideoTitle />
        <Thumbnail />
      </div>
      <div className="flex w-full h-6 typo-h1 text-[#0A0A0A]">스크립트 에디터</div>
      <div className="flex w-full justify-start">
        <ScriptEditor />
      </div>
    </div>
  );
};

export default formAnswer;
