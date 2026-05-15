import { create } from 'zustand';

interface KeywordData {
  text: string;
  value: number;
}

interface KeywordStore {
  selectedKeyword: KeywordData | null;
  setSelectedKeyword: (keyword: KeywordData | null) => void;
}

const useKeywordStore = create<KeywordStore>(set => ({
  selectedKeyword: null,
  setSelectedKeyword: keyword => set({ selectedKeyword: keyword }),
}));

export default useKeywordStore;
