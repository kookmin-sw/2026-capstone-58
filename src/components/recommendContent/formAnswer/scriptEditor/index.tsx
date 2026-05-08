import useAIFormStore from '@/stores/useAIFormStore';
import ReferenceList from '@/components/recommendContent/formAnswer/scriptEditor/referenceList';

const formatScript = (text: string) => {
  return text.replace(/\[/g, '\n\n[').replace(/\]\s*/g, ']\n').trim();
};

const ScriptEditor = () => {
  const data = useAIFormStore(s => s.data);
  const script = data?.conceptSummary ?? '';

  return (
    <div className="inline-flex w-full h-102 py-6 pl-6 pr-5 gap-5 rounded-xl bg-[#fff] border border-[#A594F9]">
      <div className="flex flex-1 flex-col gap-4 animate-fade-in-up">
        <div className="flex w-full typo-title-bold text-[#0A0A0A] items-stretch">AI 대본 초안</div>
        <div className="w-full h-full overflow-y-auto px-3 py-4 rounded-xl bg-[#FAFAFA] border border-[#A594F9] typo-body4-semibold text-black whitespace-pre-line break-keep leading-6 script-scroll">
          {script ? (
            formatScript(script)
          ) : (
            <span className="animate-loading-pulse text-gray-400">검색 후 대본이 표시됩니다.</span>
          )}
        </div>
      </div>
      <div
        className="flex w-70 shrink-0 flex-col gap-4 animate-fade-in-up"
        style={{ animationDelay: '0.15s' }}
      >
        <div className="flex w-full typo-title-bold text-[#0A0A0A] items-stretch">
          참고 영상 및 크리에이터 추천
        </div>
        <ReferenceList />
      </div>
    </div>
  );
};

export default ScriptEditor;
