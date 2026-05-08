import CheckIcon from '@/assets/icons/score-icons/video-detail/check-icon.svg?react';

interface ReasonContainerProps {
  comment?: string;
  isLoading?: boolean;
}

const ReasonContainer = ({ comment, isLoading = false }: ReasonContainerProps) => {
  return (
    <div className="flex w-full justify-center items-center gap-3">
      <CheckIcon className="w-5 h-5" />
      <div className="flex w-full justify-start items-center text-black typo-body5">
        {isLoading ? (
          <span className="text-gray-400 animate-loading-pulse">분석 중입니다...</span>
        ) : (
          comment || ''
        )}
      </div>
    </div>
  );
};

export default ReasonContainer;
