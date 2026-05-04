import { useState } from 'react';

interface TabListProps {
  tabs: string[];
  defaultTab?: number;
  onChange?: (index: number) => void;
}

const TabList = ({ tabs, defaultTab = 0, onChange }: TabListProps) => {
  const [activeIndex, setActiveIndex] = useState(defaultTab);

  const handleClick = (index: number) => {
    setActiveIndex(index);
    onChange?.(index);
  };

  return (
    <div className="relative flex w-155 h-16 px-4 py-0.5 justify-center items-center rounded-xl opacity-90 bg-[#6B4EFF]">
      <div
        className="absolute w-72 h-11 rounded-xl bg-white transition-transform duration-300 ease-in-out"
        style={{ transform: `translateX(${activeIndex === 0 ? '-50%' : '50%'})` }}
      />
      {tabs.map((tab, index) => (
        <div
          key={index}
          onClick={() => handleClick(index)}
          className={`relative z-10 flex w-73 h-15 justify-center items-center rounded-xl cursor-pointer transition-colors duration-300
            ${activeIndex === index ? 'typo-title-bold text-[#6B4EFF]' : 'typo-body1-medium text-white'}`}
        >
          {tab}
        </div>
      ))}
    </div>
  );
};

export default TabList;
