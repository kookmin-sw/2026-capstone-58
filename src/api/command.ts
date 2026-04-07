import api from './axios';

// ===== Request Types =====

interface RecommendRequest {
  requestURL: string;
  keywords: string;
  category: string;
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

interface ScriptRequest {
  requestURL: string;
  keywords: string;
  category: string;
  time: number;
  title: string;
  concept: string;
}

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
