import { useState } from 'react';
import Header from '@/components/header';
import TabList from '@/components/tabList';
import FormList from '@/components/formList.tsx';
import FormAnswer from '@/components/formAnswer.tsx';

const MainPage = () => {
  const [showAnswer, setShowAnswer] = useState(false);

  const handleSearch = () => {
    setShowAnswer(true);
  };

  return (
    <div>
      <Header />
      <div className="flex flex-col items-center w-270 mx-auto gap-9">
        <div className="flex flex-col items-center mt-20 w-full mx-auto">
          <div className="relative z-10 mb-[-32px]">
            <TabList tabs={['숏폼', '롱폼']} />
          </div>
          <FormList onSearch={handleSearch} />
        </div>
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
