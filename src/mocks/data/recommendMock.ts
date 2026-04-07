// 첫 번째 API (/ai_recommend) 모킹 응답
export const mockRecommendResponse = [
  {
    suggestedTitle: '유튜브 알고리즘이 좋아하는 영상 구조 3가지',
    conceptSummary: '조회수를 높이는 영상 흐름을 실전 예시로 분석',
  },
  {
    suggestedTitle: '구독자 1000명까지 가장 빠른 방법',
    conceptSummary: '초기 채널 성장 전략을 단계별로 정리',
  },
  {
    suggestedTitle: '썸네일 클릭률을 2배 올리는 디자인 법칙',
    conceptSummary: 'CTR을 높이는 썸네일 구성 요소 분석',
  },
];

// 두 번째 API (/ai_script) 모킹 응답
export const mockScriptResponse = [
  {
    conceptSummary:
      "오프닝: '여러분 혹시 영상 올렸는데 조회수가 안 나온 적 있으시죠?' 로 공감 훅 시작...",
    suggestedTitles: [
      '유튜브 알고리즘이 좋아하는 영상 구조 3가지 (이것만 알면 조회수 달라짐)',
      '조회수 안 나오는 영상의 공통점 | 구조가 문제입니다',
      '유튜브 잘 되는 영상 vs 안 되는 영상 차이점 분석',
      '알고리즘 탈 수 있는 영상 만드는 법 (실전 비교)',
      '영상 구조만 바꿔도 조회수 2배 | 유튜브 성장 공식',
    ],
    thumbnail: {
      thumbnailImage:
        'https://www.shutterstock.com/ko/blog/wp-content/uploads/sites/17/2020/08/Youtube-thumbnail-banner.jpg?w=435&h=304&crop=1',
      thumbnailGuide: "밝은 배경에 큰 텍스트로 '3가지' 강조, 화살표 이미지로 상승 추세 표현",
    },
    similarVideos: [
      {
        videoUrl: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        videoTitle: '유튜브 조회수 늘리는 방법 TOP 5',
      },
      {
        videoUrl: 'https://www.youtube.com/watch?v=jNQXAC9IVRw',
        videoTitle: '영상 구조 분석 | 성공한 유튜버들의 공통점',
      },
      {
        videoUrl: 'https://www.youtube.com/watch?v=9bZkp7q19f0',
        videoTitle: '알고리즘 이해하고 영상 만들기',
      },
    ],
    similarCreators: [
      {
        channelUrl: 'https://www.youtube.com/channel/UCxxxxxx',
        creatorName: '유튜브 성장 전문가 채널',
      },
      {
        channelUrl: 'https://www.youtube.com/channel/UCyyyyyy',
        creatorName: '콘텐츠 기획 마스터',
      },
    ],
  },
];
