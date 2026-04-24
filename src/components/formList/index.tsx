import { useState, useRef, useEffect } from 'react';
import FormContainer from '@/components/formContainer';
import CheckBox from '@/components/checkBox';
import TimeSlider from '@/components/timeSlider';
import { postRecommend } from '@/api/command';
import useRecommendStore from '@/stores/useRecommendStore';
import { useShallow } from 'zustand/react/shallow';

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
  const [keyword, setKeyword] = useState('');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [time, setTime] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');
  const contentRef = useRef<HTMLDivElement>(null);
  const [contentHeight, setContentHeight] = useState<number | undefined>(undefined);
  const { setRecommendations, setFormInput } = useRecommendStore(
    useShallow(s => ({
      setRecommendations: s.setRecommendations,
      setFormInput: s.setFormInput,
    })),
  );

  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    }
  }, []);

  const handleCategoryToggle = (category: string, checked: boolean) => {
    setSelectedCategories(prev =>
      checked ? [...prev, category] : prev.filter(c => c !== category),
    );
  };

  const handleSearch = async () => {
    const missing: string[] = [];
    if (!keyword.trim()) missing.push('Keyword');
    if (!youtubeUrl.trim()) missing.push('YouTube URL');
    if (selectedCategories.length === 0) missing.push('Category');
    if (time === 0) missing.push('Time');

    if (missing.length > 0) {
      setErrorMsg(`${missing.join(', ')}을(를) 입력해주세요.`);
      return;
    }

    setErrorMsg('');
    setCollapsed(true);
    setSearched(true);

    try {
      const res = await postRecommend({
        requestURL: youtubeUrl,
        keywords: keyword,
        category: `{${selectedCategories.join(', ')}}`,
      });
      setRecommendations(res);
      setFormInput({
        requestURL: youtubeUrl,
        keywords: keyword,
        category: `{${selectedCategories.join(', ')}}`,
        time,
      });
    } catch (err) {
      console.error('추천 요청 실패:', err);
    }

    onSearch?.();
  };

  return (
    <div className="flex w-250 pt-18 pb-12 px-8 flex-col justify-end items-center gap-10 rounded-xl bg-[#F5EFFF]">
      <div
        ref={contentRef}
        className="flex flex-col overflow-hidden transition-all duration-500 ease-in-out gap-4"
        style={{ maxHeight: collapsed ? 0 : contentHeight, opacity: collapsed ? 0 : 1 }}
      >
        <div className="flex justify-center w-full typo-title text-[#717171] text-center whitespace-pre-line">
          {
            '원하는 키워드와 채널 정보를 입력하면\nAI가 트렌드와 채널 데이터를 분석해 맞춤 콘텐츠 아이디어를 추천합니다.'
          }
        </div>
        <div className="flex w-234 py-9 px-8 flex-col justify-center items-center gap-6 rounded-xl border border-black/10 bg-white">
          <div className="flex pb-14 pl-6 pr-4 flex-col items-start gap-12">
            <div className="flex w-196 h-21 justify-center items-start gap-6">
              <FormContainer
                title="Keyword"
                placeholder="예) 여행브이로그 / 다이어트 식단"
                value={keyword}
                onChange={setKeyword}
              />
              <FormContainer
                title="YouTube URL"
                placeholder="예) https://youtube.com/@channel"
                value={youtubeUrl}
                onChange={setYoutubeUrl}
              />
            </div>
            <div className="flex w-196 flex-col items-start gap-4">
              <div className="typo-title text-[#0A0A0A]">Category</div>
              <div className="h-78 self-stretch grid grid-cols-3 gap-4 content-start">
                {categories.map(category => (
                  <CheckBox
                    key={category}
                    label={category}
                    onChange={checked => handleCategoryToggle(category, checked)}
                  />
                ))}
              </div>
            </div>
            <div className="flex w-196 flex-col items-start gap-4">
              <div className="typo-title text-[#0A0A0A]">Time</div>
              <TimeSlider onChange={setTime} />
            </div>
          </div>
        </div>
      </div>
      <div className="flex w-full items-center relative">
        {errorMsg && <div className="absolute left-0 text-sm text-red-500">{errorMsg}</div>}
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
