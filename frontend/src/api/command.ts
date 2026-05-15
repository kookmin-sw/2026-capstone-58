import api from './axios';

// ===== Request Types =====

interface RecommendRequest {
  requestURL: string;
  keywords: string;
  category: string;
}

interface ScriptRequest {
  requestURL: string;
  keywords: string;
  category: string;
  time: number;
  title: string;
  concept: string;
}

// ===== Response Types =====

export interface VideoAnalysisResponse {
  videoInfo: {
    videoId: string;
    title: string;
    thumbnailUrl: string;
    viewCount: number;
    uploadDate: string;
    category: string;
    durationSeconds: number;
    score: {
      overall: number;
      topPercent: number;
      description: string;
    };
  };
  factors: {
    name: string;
    score: number;
    topPercent?: number;
    changePercent?: number;
    description: string;
  }[];
  audienceRetention: {
    sections: {
      timeSeconds: number;
      label: string;
      retentionPercent: number;
    }[];
    avgWatchSeconds: number;
    mainDropOffSegment: {
      startSeconds: number;
      endSeconds: number;
      description: string;
    };
  };
  insight: string;
  improvements: {
    title: string;
    description: string;
  }[];
  recommendedActions: {
    title: string;
    description: string;
  }[];
  scoreBasis: string[];
  viewGrowthData: {
    video: {
      day: number;
      views: number;
    }[];
    channelAvg: {
      day: number;
      avgViews: number;
    }[];
  };
}

// ===== API Functions =====

// POST /ai_recommend - AI 추천 주제 요청
export const postRecommend = async (data: RecommendRequest) => {
  const response = await api.post('/ai_recommend', null, {
    params: {
      requestURL: data.requestURL,
      keywords: data.keywords,
      category: data.category,
    },
  });
  return response.data;
};

// POST /ai_script - AI 제목/스크립트 요청
export const postScript = async (data: ScriptRequest) => {
  const response = await api.post('/ai_script', null, {
    params: {
      requestURL: data.requestURL,
      title: data.title,
      concept: data.concept,
      keywords: data.keywords,
      category: data.category,
      time: data.time,
    },
  });
  return response.data;
};

// GET /analyze/channel - 채널 분석 요청
export const getChannelAnalysis = async (channel: string) => {
  const response = await api.get('/analyze/channel', {
    params: { channel },
  });
  return response.data;
};

// GET /analyze/video/{videoId} - 영상 상세 분석 요청
export const getVideoAnalysis = async (videoId: string): Promise<VideoAnalysisResponse> => {
  const response = await api.get(`/analyze/video/${videoId}`);
  return response.data;
};
