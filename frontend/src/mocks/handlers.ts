import { http, HttpResponse } from 'msw';
import { mockRecommendResponse, mockScriptResponse } from '@/mocks/data/recommendMock';
import { mockChannelAnalysisResponse } from '@/mocks/data/analysisMock';
import { mockVideoAnalysisResponse } from '@/mocks/data/videoAnalysisMock';

const SERVER_URL = import.meta.env.VITE_SERVER_URL;

export const handlers = [
  // POST /ai_recommend - AI 추천 주제 요청
  http.post(`${SERVER_URL}/ai_recommend`, () => {
    return HttpResponse.json(mockRecommendResponse, { status: 200 });
  }),

  // POST /ai_script - AI 제목/스크립트 요청
  http.post(`${SERVER_URL}/ai_script`, () => {
    return HttpResponse.json(mockScriptResponse, { status: 200 });
  }),

  // GET /analyze/channel - 채널 분석 요청
  http.get(`${SERVER_URL}/analyze/channel`, () => {
    return HttpResponse.json(mockChannelAnalysisResponse, { status: 200 });
  }),

  // GET /analyze/video/:videoId - 영상 상세 분석 요청
  http.get(`${SERVER_URL}/analyze/video/:videoId`, () => {
    return HttpResponse.json(mockVideoAnalysisResponse, { status: 200 });
  }),
];
