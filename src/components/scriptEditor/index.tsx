interface ScriptEditorProps {
  script?: string;
}

const scriptEx = `안녕하세요! 다들 잘 주무셨나요? 오늘은 평범하지만, 제게는 특별한 일상을 공유해보려고 해요. 아침 햇살이 너무 좋아서, 커피 한잔으로 하루를 시작해봅시다. (커피 내리는 소리)

점심 메뉴는 간단하게 샌드위치를 만들어 먹었어요. 요즘 제가 빠져있는 소스를 곁들여서 먹으니까 정말 맛있네요! 이따 친구랑 공원에서 산책하기로 했는데 정말 기대되네요.

친구랑 즐거운 시간을 보내고 집에 돌아오니 어느덧 저녁이네요. 오늘 저녁은 제가 제일 좋아하는 김치볶음밥을 만들어 먹었어요. 맛있는 음식을 먹으면서 하루 마무리하니까 행복하네요.

오늘 하루도 수고 많으셨어요. 시청해주셔서 감사하고, 다음 영상에서 만나요! 안녕!`;

const scriptEditor = ({ script }: ScriptEditorProps) => {
  return (
    <div className="inline-flex w-full py-6 pl-6 pr-5 gap-5 rounded-xl bg-[#fff] border border-[#0000004F]">
      <div className="flex w-full flex-col gap-4">
        <div className="flex w-full typo-title-bold text-[#0A0A0A] items-stretch">AI 대본 초안</div>
        <div className="flex w-full h-full px-3 py-4 items-stretch rounded-xl bg-[#FAFAFA] border border-[#a1a1a163] text-black text-sm font-semibold whitespace-pre-line break-keep leading-6">
          {script ?? scriptEx}
        </div>
      </div>
      <div className="flex w-60 shrink-0 flex-col gap-4">
        <div className="flex w-full typo-title-bold text-[#0A0A0A] items-stretch">
          추천 영상 구조(타임라인)
        </div>
        <div className="flex w-full h-full px-3 py-4 items-stretch rounded-xl bg-[#FAFAFA] border border-[#a1a1a163] text-black text-sm font-semibold"></div>
      </div>
    </div>
  );
};

export default scriptEditor;
