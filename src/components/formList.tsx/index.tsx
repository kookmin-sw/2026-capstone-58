import { useState, useRef, useEffect } from 'react';
import FormContainer from '@/components/formContainer.tsx';
import CheckBox from '@/components/checkBox.tsx';

const categories = [
  'Games',
  'Cooking',
  'Reading',
  'Travel',
  'Music',
  'Movies',
  'Sports',
  'Health & Wellness',
  'Technology',
  'Family & Friends',
  'News & Current Events',
  'History',
  'Arts & Crafts',
  'Nature',
];

interface FormListProps {
  onSearch?: () => void;
}

const FormList = ({ onSearch }: FormListProps) => {
  const [collapsed, setCollapsed] = useState(false);
  const [searched, setSearched] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const [contentHeight, setContentHeight] = useState<number | undefined>(undefined);

  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    }
  }, []);

  const handleSearch = () => {
    setCollapsed(true);
    setSearched(true);
    onSearch?.();
  };

  return (
    <div className="flex w-250 pt-18 pb-12 px-8 flex-col justify-end items-center gap-10 rounded-xl bg-[#F7F6FB]">
      <div
        ref={contentRef}
        className="overflow-hidden transition-all duration-500 ease-in-out"
        style={{ maxHeight: collapsed ? 0 : contentHeight, opacity: collapsed ? 0 : 1 }}
      >
        <div className="flex w-234 py-9 px-8 flex-col justify-center items-center gap-6 rounded-xl border border-black/10 bg-white">
          <div className="flex pb-14 pl-6 pr-4 flex-col items-start gap-12">
            <div className="flex w-196 h-21 justify-center items-start gap-6">
              <FormContainer title="Keyword" placeholder="예) 여행브이로그 / 다이어트 식단" />
              <FormContainer title="YouTube URL" placeholder="예) https://youtube.com/@channel" />
            </div>
            <div className="flex w-196 flex-col items-start gap-4">
              <div className="flex w-196 flex-col items-start gap-4">
                <div className="typo-title text-[#0A0A0A]">Category</div>
                <div className="h-78 self-stretch grid grid-cols-3 gap-4 content-start">
                  {categories.map(category => (
                    <CheckBox key={category} label={category} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="flex w-full items-center relative">
        <div
          onClick={handleSearch}
          className="flex py-2.5 px-5 mx-auto justify-center items-center gap-2.5 rounded-lg bg-[#7C5CFF] active:bg-[#6344DD] typo-title text-white text-center tracking-widest cursor-pointer"
        >
          {searched ? '다시 검색' : '검색'}
        </div>
        {searched && (
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
        )}
      </div>
    </div>
  );
};

export default FormList;
