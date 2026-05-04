interface FormContainerProps {
  title: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
}

const FormContainer = ({ title, placeholder, value, onChange }: FormContainerProps) => {
  return (
    <div className="flex w-95 h-21 flex-col items-start gap-2 shrink-0">
      <div className="flex h-7 items-center gap-2 shrink-0 self-stretch">
        <div className="typo-body1-medium text-[#0A0A0A]">{title}</div>
      </div>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={e => onChange?.(e.target.value)}
        className="flex h-12 py-1 px-3 items-center shrink-0 self-stretch rounded-lg border border-transparent bg-[#FEF8FF] typo-body2 text-[#0A0A0A] placeholder:typo-body2 placeholder:text-[#0a0a0a89] outline-none"
      />
    </div>
  );
};

export default FormContainer;
