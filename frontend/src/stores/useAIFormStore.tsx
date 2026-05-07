import { create } from 'zustand';

interface SimilarVideo {
  videoUrl: string;
  videoTitle: string;
}

interface SimilarCreator {
  channelUrl: string;
  creatorName: string;
}

interface AIFormData {
  conceptSummary: string;
  suggestedTitles: string[];
  thumbnail: {
    thumbnailImage: string;
    thumbnailGuide: string;
  };
  similarVideos: SimilarVideo[];
  similarCreators: SimilarCreator[];
}

interface AIFormStore {
  data: AIFormData | null;
  setData: (data: AIFormData) => void;
  clear: () => void;
}

const useAIFormStore = create<AIFormStore>(set => ({
  data: null,
  setData: data => set({ data }),
  clear: () => set({ data: null }),
}));

export default useAIFormStore;
