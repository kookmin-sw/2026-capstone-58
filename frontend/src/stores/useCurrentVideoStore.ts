import { create } from 'zustand';
import type { VideoAnalysisResponse } from '@/api/command';

interface CurrentVideoStore {
  // 채널 분석 목록에서 선택한 기본 정보
  videoId: string | null;
  // API 응답 전체 데이터
  videoAnalysis: VideoAnalysisResponse | null;
  isLoading: boolean;
  setVideoId: (videoId: string) => void;
  setVideoAnalysis: (data: VideoAnalysisResponse) => void;
  setLoading: (loading: boolean) => void;
  clear: () => void;
}

const useCurrentVideoStore = create<CurrentVideoStore>(set => ({
  videoId: null,
  videoAnalysis: null,
  isLoading: false,
  setVideoId: videoId => set({ videoId }),
  setVideoAnalysis: data => set({ videoAnalysis: data }),
  setLoading: loading => set({ isLoading: loading }),
  clear: () => set({ videoId: null, videoAnalysis: null, isLoading: false }),
}));

export default useCurrentVideoStore;
