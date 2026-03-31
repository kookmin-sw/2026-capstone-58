import { useState } from 'react';
import CheckIcon from '@/assets/icons/check-icon.svg?react';

interface CheckBoxProps {
  label: string;
  checked?: boolean;
  onChange?: (checked: boolean) => void;
}

const CheckBox = ({ label, checked: controlledChecked, onChange }: CheckBoxProps) => {
  const [internalChecked, setInternalChecked] = useState(false);
  const isChecked = controlledChecked ?? internalChecked;

  const handleClick = () => {
    const next = !isChecked;
    setInternalChecked(next);
    onChange?.(next);
  };

  return (
    <div
      onClick={handleClick}
      className="flex w-full h-12 px-3 items-center gap-3 rounded-lg border border-black/10 cursor-pointer"
    >
      <div
        className={`w-5 h-5 shrink-0 rounded-sm shadow-sm flex items-center justify-center ${
          isChecked ? 'border border-[#7C5CFF] bg-[#7C5CFF]' : 'border border-black/10 bg-[#FEF8FF]'
        }`}
      >
        {isChecked && <CheckIcon className="w-3 h-3 text-white" />}
      </div>
      <div className="flex w-48 h-6 items-center gap-2 shrink-0 typo-body text-[#0A0A0A] tracking-wide">
        {label}
      </div>
    </div>
  );
};

export default CheckBox;
