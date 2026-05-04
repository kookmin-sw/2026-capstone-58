interface SubjectItemProps {
  subject?: string;
  subjectContent?: string;
  selected?: boolean;
  onClick?: () => void;
}

const SubjectItem = ({ subject, subjectContent, selected, onClick }: SubjectItemProps) => {
  return (
    <div
      onClick={onClick}
      className={`flex w-234 py-6 px-8 flex-col items-start gap-3 rounded-xl border cursor-pointer transition-all duration-200
        ${
          selected
            ? 'border-[#6B4EFF] bg-[#F3F0FF] shadow-md'
            : 'border-[#A594F9] bg-white hover:bg-[#FAFAFE]'
        }`}
    >
      {subject && <div className="typo-title-bold text-[#0A0A0A]">{subject}</div>}
      {subjectContent && (
        <div className="typo-body2 text-[#717171] whitespace-pre-line">{subjectContent}</div>
      )}
    </div>
  );
};

export default SubjectItem;
