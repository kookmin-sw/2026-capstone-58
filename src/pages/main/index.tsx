import { useEffect, useState } from 'react';
import Header from '@/components/header';
import Footer from '@/components/footer';
import Keywords from '@/components/keywordsContent/keywords';
import KeywordCard from '@/components/keywordsContent/keywordCard';
import useKeywordStore from '@/stores/useKeywordStore';

const Main = () => {
  const selectedKeyword = useKeywordStore(s => s.selectedKeyword);
  const setSelectedKeyword = useKeywordStore(s => s.setSelectedKeyword);
  const [animationKey, setAnimationKey] = useState(0);

  // 페이지 진입 시 선택된 키워드 초기화
  useEffect(() => {
    setSelectedKeyword(null);
  }, [setSelectedKeyword]);

  // 키워드가 바뀔 때마다 애니메이션 키 증가 (재실행용)
  useEffect(() => {
    if (selectedKeyword) {
      setAnimationKey(prev => prev + 1);
    }
  }, [selectedKeyword]);

  return (
    <div className="min-h-screen flex flex-col bg-linear-to-br from-[#F5EFFF] via-white to-[#E8F4F8] relative overflow-hidden">
      {/* 배경 장식 요소들 */}
      <div className="absolute top-20 left-10 w-72 h-72 bg-[#9F8CFF] rounded-full opacity-10 blur-3xl" />
      <div className="absolute top-40 right-20 w-96 h-96 bg-[#4ECDC4] rounded-full opacity-10 blur-3xl" />
      <div className="absolute bottom-40 left-1/4 w-80 h-80 bg-[#FF6B6B] rounded-full opacity-10 blur-3xl" />
      <div className="absolute bottom-20 right-10 w-64 h-64 bg-[#FFEAA7] rounded-full opacity-15 blur-3xl" />

      <Header />
      <div className="flex-1 flex flex-col w-full p-10 justify-center items-center relative z-10 gap-4 px-8">
        {/* 슬로건 */}
        <div className="flex flex-col items-center text-center">
          <div className="typo-title1">
            <span className="text-gray-500">트렌드를 읽고, 콘텐츠를 만들다 </span>
            <span className="text-[#6B4EFF]">단 하나의 시작, CRiT</span>
          </div>
          <div className="text-gray-600 typo-body4 mt-2">
            지금 뜨는 키워드로 주제를 추천받으세요.
          </div>
        </div>
        <div className="flex w-full justify-center items-center gap-8">
          <div className="transition-all duration-500">
            <Keywords isShifted={!!selectedKeyword} />
          </div>
          {selectedKeyword && (
            <div className="flex items-center justify-center shrink-0">
              <KeywordCard animationKey={animationKey} />
            </div>
          )}
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Main;
