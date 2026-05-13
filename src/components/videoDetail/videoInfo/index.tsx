import { useState } from 'react';
import ShareIcon from '@/assets/icons/share-icon.svg?react';
import ColumnLine from './columnLine.tsx';
import CircleProgress from '@/components/channel/algorithmScore/circleProgress';
import ViewsIcon from '@/assets/icons/score-icons/video-detail/views-icon.svg?react';
import CategoryIcon from '@/assets/icons/score-icons/video-detail/category-icon.svg?react';
import TimeIcon from '@/assets/icons/score-icons/video-detail/time-icon.svg?react';
import UploadIcon from '@/assets/icons/score-icons/video-detail/upload-icon.svg?react';
import BarGraphIcon from '@/assets/icons/score-icons/video-detail/bar-graph-icon.svg?react';
import RightIcon from '@/assets/icons/score-icons/video-detail/right-icon.svg?react';
import InfoIcon from '@/assets/icons/score-icons/video-detail/info-icon.svg?react';
import useCurrentVideoStore from '@/stores/useCurrentVideoStore';

const VideoInfo = () => {
  const [shared, setShared] = useState(false);
  const videoAnalysis = useCurrentVideoStore(s => s.videoAnalysis);
  const isLoading = useCurrentVideoStore(s => s.isLoading);

  const videoInfo = videoAnalysis?.videoInfo;
  const videoUrl = videoInfo ? `https://www.youtube.com/watch?v=${videoInfo.videoId}` : '';

  // 조회수 포맷팅 (154000 -> "154,000")
  const formatViewCount = (count: number) => {
    return count.toLocaleString();
  };

  // 업로드 날짜 포맷팅 (2024-03-15 -> "2024.03.15")
  const formatUploadDate = (date: string) => {
    return date.replace(/-/g, '.');
  };

  // 영상 시간 포맷팅 (743초 -> "12:23")
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleShare = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!videoInfo) return;

    if (navigator.share) {
      try {
        await navigator.share({ title: videoInfo.title, url: videoUrl });
        setShared(true);
        setTimeout(() => setShared(false), 2000);
      } catch {
        // 사용자가 공유 취소한 경우
      }
    } else {
      await navigator.clipboard.writeText(videoUrl);
      setShared(true);
      setTimeout(() => setShared(false), 2000);
    }
  };

  const showLoading = isLoading || !videoInfo;

  return (
    <div className="flex w-full justify-center items-center px-8 py-6 gap-7 bg-white rounded-xl border-[0.1px] border-[#8257B4]">
      <div className="w-107.5 shrink-0 aspect-video rounded-xl overflow-hidden">
        {videoInfo?.thumbnailUrl ? (
          <img
            src={videoInfo.thumbnailUrl}
            alt={videoInfo.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex w-full h-full items-center justify-center text-gray-400 typo-body2 bg-gray-100 animate-loading-pulse">
            썸네일이 표시됩니다.
          </div>
        )}
      </div>
      <div className="flex flex-col w-full gap-4 items-center justify-center">
        <div className="flex w-full justify-start items-center gap-2">
          <div className="text-black typo-title1">
            {showLoading ? (
              <span className="text-gray-400 animate-loading-pulse">
                영상 제목을 불러오는 중...
              </span>
            ) : (
              videoInfo.title
            )}
          </div>
          <ShareIcon
            onClick={handleShare}
            className={`w-5 h-5 cursor-pointer shrink-0 ${shared ? 'text-[#6B4EFF]' : 'text-[#0000004D] active:text-[#6B4EFF]'}`}
          />
        </div>
        <div className="flex w-full justify-start items-center gap-2.5">
          <div className="flex justify-center items-center gap-1">
            <ViewsIcon className="w-4 h-4" />
            <div className="text-black typo-body5">
              {showLoading ? (
                <span className="animate-loading-pulse">조회수 ---회</span>
              ) : (
                `조회수 ${formatViewCount(videoInfo.viewCount)}회`
              )}
            </div>
          </div>
          <ColumnLine />
          <div className="flex justify-center items-center gap-1">
            <UploadIcon className="w-4 h-4" />
            <div className="text-black typo-body5">
              {showLoading ? (
                <span className="animate-loading-pulse">----.--.-- 업로드</span>
              ) : (
                `${formatUploadDate(videoInfo.uploadDate)} 업로드`
              )}
            </div>
          </div>
          <ColumnLine />
          <div className="flex justify-center items-center gap-1">
            <CategoryIcon className="w-4 h-4" />
            <div className="text-black typo-body5">
              {showLoading ? (
                <span className="animate-loading-pulse">카테고리</span>
              ) : (
                videoInfo.category
              )}
            </div>
          </div>
          <ColumnLine />
          <div className="flex justify-center items-center gap-1">
            <TimeIcon className="w-4 h-4" />
            <div className="text-black typo-body5">
              {showLoading ? (
                <span className="animate-loading-pulse">--:--</span>
              ) : (
                formatDuration(videoInfo.durationSeconds)
              )}
            </div>
          </div>
        </div>
        <div className="flex w-full justify-start items-center gap-1.5">
          <div className="flex justify-center items-center gap-1 py-1 px-2 rounded-xl bg-[#F5EFFF]">
            <BarGraphIcon />
            <div className="text-[#634DCB] typo-body6">분석 기준</div>
          </div>
          <div className="text-black typo-body5">
            {showLoading ? (
              <span className="animate-loading-pulse">----.--.-- ~ 현재</span>
            ) : (
              `${formatUploadDate(videoInfo.uploadDate)} ~ 현재`
            )}
          </div>
          <RightIcon className="w-3 h-3" />
        </div>
        <div className="flex flex-col w-full px-4 py-3.5 justify-center items-center gap-1.5 self-stretch rounded-xl border-[0.5px] border-[#8257B4]">
          <div className="flex w-full justify-start items-center gap-1">
            <div className="text-black typo-body4-semibold">종합 점수</div>
            <InfoIcon className="w-3.5 h-3.5" />
          </div>
          <div className="flex w-full justify-center items-center gap-7">
            <CircleProgress score={showLoading ? 0 : videoInfo.score.overall} />
            <div className="w-0.5 h-40 bg-[#8257B433] self-stretch" />
            <div className="flex flex-col w-full justify-center items-center gap-2">
              <div className="w-full justify-start items-center text-black typo-body4-semibold">
                {showLoading ? (
                  <span className="animate-loading-pulse">상위 --% 영상입니다.</span>
                ) : (
                  `상위 ${videoInfo.score.topPercent}% 영상입니다.`
                )}
              </div>
              <div className="w-full jsutify-start items-center text-black typo-body5">
                {showLoading ? (
                  <span className="text-gray-400 animate-loading-pulse">
                    분석 결과를 불러오는 중입니다...
                  </span>
                ) : (
                  videoInfo.score.description
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoInfo;
