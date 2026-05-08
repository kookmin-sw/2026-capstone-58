import { create } from 'zustand';

interface CurrentVideo {
  videoId: string;
  title: string;
  thumbnailUrl: string;
  percentileScore: number;
  reason: string;
}

interface CurrentVideoStore {
  video: CurrentVideo | null;
  setVideo: (video: CurrentVideo) => void;
  clear: () => void;
}

const useCurrentVideoStore = create<CurrentVideoStore>(set => ({
  video: null,
  setVideo: video => set({ video }),
  clear: () => set({ video: null }),
}));

export default useCurrentVideoStore;
