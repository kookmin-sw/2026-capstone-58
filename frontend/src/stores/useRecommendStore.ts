import { create } from 'zustand';

interface RecommendItem {
  suggestedTitle: string;
  conceptSummary: string;
}

interface FormInput {
  requestURL: string;
  keywords: string;
  category: string;
  time: number;
}

interface TitleItem {
  [key: string]: unknown;
}

interface RecommendStore {
  // 폼 입력값
  formInput: FormInput;
  setFormInput: (data: FormInput) => void;

  // 추천 주제 (1차 API)
  recommendations: RecommendItem[];
  setRecommendations: (data: RecommendItem[]) => void;

  // 추천 제목 (2차 API)
  titles: TitleItem[];
  setTitles: (data: TitleItem[]) => void;

  clear: () => void;
}

const useRecommendStore = create<RecommendStore>(set => ({
  formInput: { requestURL: '', keywords: '', category: '', time: 0 },
  setFormInput: data => set({ formInput: data }),

  recommendations: [],
  setRecommendations: data => set({ recommendations: data }),

  titles: [],
  setTitles: data => set({ titles: data }),

  clear: () =>
    set({
      recommendations: [],
      titles: [],
      formInput: { requestURL: '', keywords: '', category: '', time: 0 },
    }),
}));

export default useRecommendStore;
