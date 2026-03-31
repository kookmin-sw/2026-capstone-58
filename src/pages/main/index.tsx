import { useState } from 'react';
import Header from '@/components/header';
import TabList from '@/components/tabList';
import FormList from '@/components/formList';
import FormAnswer from '@/components/formAnswer';
import FormSubject from '@/components/formSubject';

const MainPage = () => {
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
      <div className="flex flex-col items-center w-270 mx-auto gap-10">
        <div className="flex flex-col items-center mt-20 w-full mx-auto">
          <div className="relative z-10 mb-[-32px]">
            <TabList tabs={['숏폼', '롱폼']} />
          </div>
          <FormList onSearch={handleSearch} />
        </div>
        {showSubject && <FormSubject onSelect={handleSelectSubject} />}
        {showAnswer && (
          <div className="flex flex-col items-center self-stretch w-full mx-auto">
            <FormAnswer />
          </div>
        )}
      </div>
    </div>
  );
};

export default MainPage;
