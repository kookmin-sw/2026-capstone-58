import { useState, useRef, useEffect } from 'react';
import SubjectItem from '@/components/subjectItem';

interface FormSubjectProps {
  onSelect?: () => void;
}

const FormSubject = ({ onSelect }: FormSubjectProps) => {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const [contentHeight, setContentHeight] = useState<number | undefined>(undefined);

  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    }
  }, []);

  const handleClick = (index: number) => {
    setSelectedIndex(index);
    setCollapsed(true);
    onSelect?.();
  };

  return (
    <div className="flex w-250 py-14 px-8 flex-col justify-end items-center gap-10 rounded-xl bg-[#F7F6FB]">
      <div
        ref={contentRef}
        className="flex flex-col items-center gap-10 overflow-hidden transition-all duration-500 ease-in-out w-full"
        style={{ maxHeight: collapsed ? 0 : contentHeight, opacity: collapsed ? 0 : 1 }}
      >
        <div className="flex w-full justify-center typo-title-bold text-[#717171] text-center whitespace-pre-line">
          {
            '다음 영상으로 제작하기 좋은 콘텐츠 주제를 확인해보세요.\n관심 있는 주제를 클릭하면 상세 기획을 확인할 수 있습니다.'
          }
        </div>
        {[0, 1, 2].map(i => (
          <SubjectItem key={i} selected={selectedIndex === i} onClick={() => handleClick(i)} />
        ))}
      </div>
      {selectedIndex !== null && (
        <div className="flex w-full items-center relative">
          <div
            onClick={() => setCollapsed(!collapsed)}
            className="absolute right-0 flex items-center gap-1 cursor-pointer text-[#0a0a0a89] active:text-[#6B4EFF] typo-label"
          >
            <svg
              className="w-4 h-4 transition-transform duration-300"
              style={{ transform: collapsed ? 'rotate(0deg)' : 'rotate(180deg)' }}
              viewBox="0 0 16 16"
            >
              <path
                d="M4 6l4 4 4-4"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            {collapsed ? '펼치기' : '접기'}
          </div>
        </div>
      )}
    </div>
  );
};

export default FormSubject;
