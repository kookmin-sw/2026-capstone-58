const defaultSubject = '봄맞이 캠퍼스 라이프 VLOG 🌸 벚꽃 구경 & 중간고사 스트레스 해소법';
const defaultContent = `만개한 캠퍼스의 벚꽃 풍경을 담고, 중간고사 기간 스트레스를 관리하며 즐겁게 보내는 대학생 공나의 일상을 공유하는 브이로그입니다.
추천 근거: 현재 날짜는 3월 말로, 벚꽃 시즌과 함께 대학생들의 중간고사 기간이 다가오고 있어 시의성이 높고, 캠퍼스 라이프에 대한 관심이 많을 시기입니다.`;

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
      className={`flex w-234 h-40 py-6 px-8 flex-col justify-between items-start rounded-xl border cursor-pointer transition-all duration-200
        ${
          selected
            ? 'border-[#6B4EFF] bg-[#F3F0FF] shadow-md'
            : 'border-[#A594F9] bg-white hover:bg-[#FAFAFE]'
        }`}
    >
      <div className="typo-title-bold text-[#0A0A0A]">{subject ?? defaultSubject}</div>
      <div className="typo-body text-[#717171] whitespace-pre-line">
        {subjectContent ?? defaultContent}
      </div>
    </div>
  );
};

export default SubjectItem;
