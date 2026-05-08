// Analysis 페이지 Mock 데이터

export const mockChannelAnalysisResponse = {
  channel: {
    handle: '@t1_faker',
    profileImageUrl: '',
    channelId: 'UCpJw2H9KKqwCCGQKRh1Bf2w',
    name: 'T1 Faker',
    subscriberCount: 2110000,
  },
  channelScore: {
    overall: 68,
    topPercent: 32,
    comment:
      '시청자 반응과 만족도가 높은 점에 비해 도달력이 상대적으로 부족한 것이 종합 점수를 낮추고 있습니다.',
    factors: [
      {
        score: 56,
        name: '도달력',
        description: '구독자 대비 조회수',
        weight: 60,
      },
      {
        score: 84,
        name: '시청자 반응',
        description: '좋아요+댓글 비율',
        weight: 25,
      },
      {
        score: 87,
        name: '콘텐츠 만족도',
        description: '좋아요 비율',
        weight: 15,
      },
    ],
  },
  summary: {
    avgViewCount: 314881.03507565334,
    avgViewCountChange: 2.3,
    uploadFrequencyPerWeek: 3.0,
    uploadFrequencyChange: -3.0,
    avgWatchDurationSeconds: null,
    avgWatchDurationChange: null,
    subscriberChange: null,
    subscriberChangePercent: null,
  },
  guides: [
    {
      description:
        '현재 평균 영상 길이가 9분인데, 7~10분 사이로 최적화하면 영상 도달력과 조회수가 15% 이상 증가할 것으로 예상됩니다.',
      title: '조회수 향상을 위한 영상 길이 조정',
    },
    {
      description:
        '현재 채널의 콘텐츠 만족도 점수가 50점이므로, 유사 주제의 영상 외에도 게임 튜토리얼, 챔피언 리뷰 등 새로운 유형의 영상을 시도해 보세요. 이를 통해 시청자층을 다양화하고 콘텐츠 만족도를 25% 이상 높일 수 있습니다.',
      title: '영상 콘텐츠 다각화',
    },
    {
      description:
        '현재 채널의 도달력 점수가 50점이므로, 영상 자막 작성과 눈길을 끄는 썸네일 제작을 통해 구독자 확보에 힘써보세요. 이를 통해 월 구독자 증가율을 30% 이상 달성할 수 있습니다.',
      title: '구독자 확보를 위한 자막 및 썸네일 개선',
    },
  ],
  percentileVideoAnalysis: [
    {
      videoId: 'VXEXCOUOOBM',
      title: '너 뭐 하는 애니?',
      thumbnailUrl: '',
      percentileScore: 51,
      reason:
        '콘텐츠 만족도이(가) 상위 7%로 뛰어나요. 도달력을(를) 개선하면 점수가 올라갈 수 있어요.',
    },
    {
      videoId: 'IT0mlafrYEM',
      title: '매혹',
      thumbnailUrl: '',
      percentileScore: 65,
      reason:
        '시청자 반응이(가) 상위 6%로 뛰어나요. 도달력을(를) 개선하면 점수가 올라갈 수 있어요.',
    },
    {
      videoId: 'Ia5dP5DTR-8',
      title: '수상할 정도로 카직스를 잘하는',
      thumbnailUrl: '',
      percentileScore: 61,
      reason:
        '콘텐츠 만족도이(가) 상위 14%로 뛰어나요. 도달력을(를) 개선하면 점수가 올라갈 수 있어요.',
    },
    {
      videoId: 'adhfGPYJFtk',
      title: '증바람',
      thumbnailUrl: '',
      percentileScore: 72,
      reason: '콘텐츠 만족도이(가) 상위 26%로 뛰어나요. 전반적으로 균형 잡힌 성과를 보이고 있어요.',
    },
    {
      videoId: 'k5UC25k6cK4',
      title: '5년 만에 페이커 손에 쥐어진 총검',
      thumbnailUrl: '',
      percentileScore: 75,
      reason: '콘텐츠 만족도이(가) 상위 15%로 뛰어나요. 전반적으로 균형 잡힌 성과를 보이고 있어요.',
    },
    {
      videoId: '9-i2b4aCxLQ',
      title: '화제의 페이커 암베사 정글 챌린지',
      thumbnailUrl: '',
      percentileScore: 58,
      reason:
        '콘텐츠 만족도이(가) 상위 11%로 뛰어나요. 도달력을(를) 개선하면 점수가 올라갈 수 있어요.',
    },
    {
      videoId: 'Z7l05JEefxw',
      title: '현준이 교육 들어갑니다',
      thumbnailUrl: '',
      percentileScore: 73,
      reason: '콘텐츠 만족도이(가) 상위 10%로 뛰어나요. 전반적으로 균형 잡힌 성과를 보이고 있어요.',
    },
    {
      videoId: 'JnnmPHpAbg0',
      title: '신을 뵙습니다',
      thumbnailUrl: '',
      percentileScore: 74,
      reason: '콘텐츠 만족도이(가) 상위 14%로 뛰어나요. 전반적으로 균형 잡힌 성과를 보이고 있어요.',
    },
    {
      videoId: 'pkVtkP-TFuw',
      title: '두바이 쫀득 구체',
      thumbnailUrl: '',
      percentileScore: 73,
      reason: '콘텐츠 만족도이(가) 상위 14%로 뛰어나요. 전반적으로 균형 잡힌 성과를 보이고 있어요.',
    },
    {
      videoId: 'EBO3CWo-81A',
      title: '페즈리얼 많이 세다, 자기 전에 생각 많이 날거야',
      thumbnailUrl: '',
      percentileScore: 76,
      reason: '콘텐츠 만족도이(가) 상위 17%로 뛰어나요. 전반적으로 균형 잡힌 성과를 보이고 있어요.',
    },
  ],
  percentileDataCollectedAt: '2026-05-04T05:32:04.674274+00:00',
};
