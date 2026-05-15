// 영상 상세 분석 Mock 데이터

export const mockVideoAnalysisResponse = {
  videoInfo: {
    videoId: 'dQw4w9WgXcQ',
    title: '구글 신제품 때문에 완전히 멘탈이 나가버린 유저들',
    thumbnailUrl: 'https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg',
    viewCount: 185000,
    uploadDate: '2024-03-15',
    category: '과학/기술',
    durationSeconds: 743,
    score: {
      overall: 82,
      topPercent: 18,
      description: '이 영상은 클릭률과 시청 유지율이 높아 추천 확장성이 우수한 콘텐츠입니다.',
    },
  },
  factors: [
    {
      name: 'CTR',
      score: 76,
      topPercent: 24,
      changePercent: 52.5,
      description:
        '클릭을 유도하는 썸네일 구성 덕분에, 알고리즘 노출이 실질적인 시청자 유입으로 이어지고 있습니다.',
    },
    {
      name: '시청 지속 시간',
      score: 88,
      topPercent: 12,
      changePercent: 18.3,
      description:
        '높은 시청 유지율을 보이고 있으며, 콘텐츠의 흐름과 편집이 시청자를 효과적으로 붙잡고 있습니다.',
    },
    {
      name: '추천 확장성',
      score: 22,
      topPercent: 78,
      changePercent: -55.0,
      description:
        '아직 알고리즘의 선택을 많이 받지 못하고 있으니, CTR부터 개선해 노출당 클릭을 높이는 것이 추천 확장성을 끌어올리는 첫 번째 단계입니다.',
    },
  ],
  audienceRetention: {
    sections: [
      { timeSeconds: 0, label: '0분', retentionPercent: 100.0 },
      { timeSeconds: 148, label: '2분', retentionPercent: 84.2 },
      { timeSeconds: 297, label: '4분', retentionPercent: 71.5 },
      { timeSeconds: 446, label: '7분', retentionPercent: 58.3 },
      { timeSeconds: 594, label: '9분', retentionPercent: 44.1 },
      { timeSeconds: 743, label: '12분', retentionPercent: 30.2 },
    ],
    avgWatchSeconds: 257,
    mainDropOffSegment: {
      startSeconds: 11,
      endSeconds: 25,
      description: '초반 후킹을 강화하면 더 많은 시청자를 붙잡을 수 있어요.',
    },
  },
  insight:
    '클릭을 유도하는 썸네일과 제목 덕분에 유입이 높았고, 안정적인 시청 유지율로 추천 확장까지 잘 이루어진 영상입니다.',
  improvements: [
    {
      title: '초반 10초 후킹 강화',
      description: '11초~25초 구간에서 이탈률이 평균보다 높습니다.',
    },
    {
      title: '썸네일 메시지 명확화',
      description: '현재 썸네일 대비 클릭률을 더 끌어올릴 여지가 있어요.',
    },
  ],
  recommendedActions: [
    {
      title: '비슷한 주제로 후속 영상 만들기',
      description: '이 주제는 시청자 반응이 좋아요.',
    },
    {
      title: 'Shorts로 재가공하기',
      description: '핵심 장면을 Shorts로 만들어 유입을 늘려보세요.',
    },
    {
      title: '썸네일 A/B 테스트 진행하기',
      description: '다른 버전의 썸네일로 CTR을 더 높여보세요.',
    },
  ],
  scoreBasis: [
    'CTR이 채널 평균(6.1%) 대비 3.2% 높습니다. (9.3%)',
    '평균 시청 지속 시간이 채널 평균(3:41) 대비 36초 더 깁니다.(4:17).',
    '업로드 후 24시간 동안 조회수 성장률이 채널 평균 대비 18% 높습니다.',
  ],
  viewGrowthData: {
    video: [
      { day: 0, views: 52000 },
      { day: 1, views: 98000 },
      { day: 2, views: 130000 },
      { day: 3, views: 152000 },
      { day: 4, views: 163000 },
      { day: 5, views: 171000 },
      { day: 6, views: 185000 },
    ],
    channelAvg: [
      { day: 0, avgViews: 31000 },
      { day: 1, avgViews: 58000 },
      { day: 2, avgViews: 79000 },
      { day: 3, avgViews: 94000 },
      { day: 4, avgViews: 104000 },
      { day: 5, avgViews: 111000 },
      { day: 6, avgViews: 117000 },
    ],
  },
};
