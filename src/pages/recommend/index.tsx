import { useState } from 'react';
import Header from '@/components/header';
import TabList from '@/components/recommendContent/tabList';
import FormList from '@/components/recommendContent/formList';
import FormAnswer from '@/components/recommendContent/formAnswer';
import FormSubject from '@/components/recommendContent/formSubject';

import Footer from '@/components/footer';

const RecommendPage = () => {
  const [showSubject, setShowSubject] = useState(false);
  const [showAnswer, setShowAnswer] = useState(false);

  const handleSearch = () => {
    setShowSubject(true);
    setShowAnswer(false);
  };

  const handleSelectSubject = () => {
    setShowAnswer(true);
  };

  return (
    <div>
      <Header />
      <div className="flex flex-col items-center px-40 gap-10">
        <div className="flex flex-col items-center mt-20 w-full mx-auto animate-fade-in-up">
          <div className="relative z-10 mb-[-32px]">
            <TabList tabs={['롱폼', '숏폼']} />
          </div>
          <FormList onSearch={handleSearch} />
        </div>
        {showSubject && (
          <div className="animate-fade-in-up">
            <FormSubject onSelect={handleSelectSubject} />
          </div>
        )}
        {showAnswer && (
          <div className="flex flex-col items-center self-stretch w-full mx-auto animate-fade-in-up">
            <FormAnswer />
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
};

export default RecommendPage;
