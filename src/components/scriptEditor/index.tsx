import useAIFormStore from '@/stores/useAIFormStore';

const formatScript = (text: string) => {
  return text.replace(/\[/g, '\n\n[').replace(/\]\s*/g, ']\n').trim();
};

const ScriptEditor = () => {
  const data = useAIFormStore(s => s.data);
  const script = data?.conceptSummary ?? '';

  return (
    <div className="inline-flex w-full py-6 pl-6 pr-5 gap-5 rounded-xl bg-[#fff] border border-[#0000004F]">
      <div className="flex flex-1 flex-col gap-4">
        <div className="flex w-full typo-title-bold text-[#0A0A0A] items-stretch">AI 대본 초안</div>
        <div className="flex w-full h-full px-3 py-4 items-stretch rounded-xl bg-[#FAFAFA] border border-[#a1a1a163] text-black text-sm font-semibold whitespace-pre-line break-keep leading-6">
          {script ? formatScript(script) : '검색 후 대본이 표시됩니다.'}
        </div>
      </div>
      <div className="flex w-60 shrink-0 flex-col gap-4">
        <div className="flex w-full typo-title-bold text-[#0A0A0A] items-stretch">
          추천 영상 구조(타임라인)
        </div>
        <div className="flex w-full h-full px-3 py-4 flex-col gap-2 rounded-xl bg-[#FAFAFA] border border-[#a1a1a163] text-black text-sm leading-6">
          <span className="text-gray-400">타임라인이 표시됩니다.</span>
        </div>
      </div>
    </div>
  );
};

export default ScriptEditor;
