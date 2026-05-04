import { create } from 'zustand';

interface Channel {
  channelId: string;
  name: string;
  profileImageUrl: string;
  subscriberCount: number;
}

interface ScoreFactor {
  name: string;
  score: number;
  weight: number;
  description: string;
}

interface ChannelScore {
  overall: number;
  topPercent: number;
  comment: string;
  factors: ScoreFactor[];
}

interface Summary {
  avgViewCount: number;
  avgViewCountChange: number;
  uploadFrequencyPerWeek: number;
  uploadFrequencyChange: number;
  avgWatchDurationSeconds: number | null;
  avgWatchDurationChange: number | null;
  subscriberChange: number;
  subscriberChangePercent: number;
}

interface Guide {
  title: string;
  description: string;
}

interface PercentileVideo {
  videoId: string;
  title: string;
  thumbnailUrl: string;
  percentileScore: number;
  reason: string;
}

interface ChannelData {
  channel: Channel;
  channelScore: ChannelScore;
  summary: Summary;
  guides: Guide[];
  percentileVideoAnalysis: PercentileVideo[];
  percentileDataCollectedAt: string;
}

interface ChannelStore {
  data: ChannelData | null;
  setData: (data: ChannelData) => void;
  clear: () => void;
}

const useChannelStore = create<ChannelStore>(set => ({
  data: null,
  setData: data => set({ data }),
  clear: () => set({ data: null }),
}));

export default useChannelStore;
