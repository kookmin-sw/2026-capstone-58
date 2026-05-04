import { useState } from 'react';

const steps = [0, 5, 10, 15, 20, 25, 30];

interface TimeSliderProps {
  defaultValue?: number;
  onChange?: (value: number) => void;
}

const TimeSlider = ({ defaultValue = 0, onChange }: TimeSliderProps) => {
  const [value, setValue] = useState(defaultValue);
  const [dragging, setDragging] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = Number(e.target.value);
    const snapped = steps.reduce((prev, curr) =>
      Math.abs(curr - raw) < Math.abs(prev - raw) ? curr : prev,
    );
    setValue(snapped);
    onChange?.(snapped);
  };

  const percent = (value / 30) * 100;

  return (
    <div className="relative w-120 flex flex-col">
      <div
        className={`absolute -top-8 px-3 py-1 rounded-md bg-[#A594F9]/80 text-white text-xs font-semibold transition-all duration-200 whitespace-nowrap ${dragging ? 'opacity-100 scale-100' : 'opacity-0 scale-90'}`}
        style={{ left: `calc(${percent}% - 16px)` }}
      >
        {value}분
      </div>
      <input
        type="range"
        min={0}
        max={30}
        step={5}
        value={value}
        onChange={handleChange}
        onMouseDown={() => setDragging(true)}
        onMouseUp={() => setDragging(false)}
        onTouchStart={() => setDragging(true)}
        onTouchEnd={() => setDragging(false)}
        className="w-full h-2 rounded-full appearance-none cursor-pointer
          [&::-webkit-slider-runnable-track]:rounded-full
          [&::-webkit-slider-runnable-track]:h-2
          [&::-webkit-slider-runnable-track]:bg-[#EAE0F4]
          [&::-webkit-slider-thumb]:appearance-none
          [&::-webkit-slider-thumb]:w-5
          [&::-webkit-slider-thumb]:h-5
          [&::-webkit-slider-thumb]:rounded-full
          [&::-webkit-slider-thumb]:bg-[#A594F9]
          [&::-webkit-slider-thumb]:-mt-1.5
          [&::-webkit-slider-thumb]:shadow-md"
      />
      <div className="flex w-full justify-between mt-2 px-1">
        {steps.map(s => (
          <span key={s} className="text-xs text-gray-500 w-5 text-center">
            {s}
          </span>
        ))}
      </div>
    </div>
  );
};

export default TimeSlider;
