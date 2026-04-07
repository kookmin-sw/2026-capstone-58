import { create } from 'zustand';

interface AIFormData {
  conceptSummary: string;
  suggestedTitles: string[];
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
