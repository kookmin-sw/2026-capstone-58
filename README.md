# 🎬 CRIT Server

유튜브 채널 정보를 기반으로 AI가 콘텐츠 주제를 추천하고 영상 기획안 및 제목을 생성하는 Spring Boot 백엔드 서버입니다.
Google Gemini API와 YouTube Data API v3를 연동하여 채널 스타일을 분석하고 맞춤형 콘텐츠 전략을 제공합니다.

---

## 기술 스택

- **Java 17**
- **Spring Boot 4.0.3**
- **Spring Security + OAuth2 Client** — Google OAuth2 로그인 + JWT 인증
- **Google Gemini API** (gemini-3.1-flash-lite-preview) — 주제 추천 및 기획안 생성
- **Google Imagen 4** — AI 썸네일 이미지 생성
- **YouTube Data API v3** — 채널 정보 및 최신 영상 수집
- **AWS Bedrock (Claude Sonnet 4 Vision)** — 채널 썸네일 스타일 분석 + 채널 성장 가이드 생성
- **AWS S3** — 생성된 썸네일 이미지 저장
- **MySQL** — 데이터 저장 (JPA/Hibernate)
- **SpringDoc OpenAPI (Swagger UI)**
- **Lombok**
- **Gradle**

---

## 시작하기

### 사전 요구사항

- Java 17+
- MySQL
- Google Gemini API 키
- YouTube Data API v3 키
- Google OAuth2 Client ID/Secret (로그인 기능)
- AWS 계정 및 Bedrock 접근 권한 (EC2 IAM Role 또는 AWS CLI 설정)
- AWS S3 버킷
- GCP 서비스 계정 키 (Imagen 사용)

### 환경 설정

환경 변수 또는 `application-secret.yml`로 설정합니다. `.env.example` 파일을 참고하세요.

```properties
# Google APIs
GEMINI_API_KEY=your_gemini_api_key
YOUTUBE_API_KEY=your_youtube_api_key

# AWS
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
AWS_S3_BUCKET=your-s3-bucket-name

# GCP (Imagen)
GCP_KEY_PATH=./gcp-key/gcp-key.json

# Database
SPRING_DATASOURCE_URL=jdbc:mysql://localhost:3306/crit?useSSL=false&serverTimezone=Asia/Seoul
SPRING_DATASOURCE_USERNAME=root
SPRING_DATASOURCE_PASSWORD=your_password
```

OAuth2 client-id/secret, JWT secret 등은 `src/main/resources/application-secret.yml`에 설정합니다.

### 실행

```bash
# 포그라운드 실행
./gradlew bootRun

# 백그라운드 실행 (Cloud9 등 원격 환경)
nohup ./gradlew bootRun > server.log 2>&1 &
```

서버 기본 포트: **8080**

Swagger UI: `http://localhost:8080/swagger-ui.html`

---

## 🚀 개선된 알고리즘 (Improved Scoring Algorithm) — ⚠️ Deprecated

> **참고**: 이 알고리즘은 백분위 기반 점수 모델로 대체되었습니다. API 응답에서 `improvedVideoAnalysis`는 삭제되었으며, `percentileVideoAnalysis`와 `channelScore`가 사용됩니다.

### 개요

기존 알고리즘의 문제점을 해결하고 YouTube 성장을 원하는 사용자들을 위한 개선된 점수 계산 시스템입니다.

**기존 알고리즘의 문제점**:
- ❌ 대부분의 영상이 100점에 수렴 (점수 차별화 불가)
- ❌ 채널 성장 단계 미반영
- ❌ 실행 가능한 인사이트 부족

**개선 사항**:
- ✅ 다층 점수 시스템 (도달, 참여, 유지, 성장)
- ✅ 채널 단계별 동적 가중치
- ✅ 카테고리별 벤치마크
- ✅ 시간 가중치 (최신 영상 우대)
- ✅ 실행 가능한 인사이트 생성

### 점수 구성

```
┌─────────────────────────────────────────┐
│ 종합 성장 점수 (0~100)                  │
├─────────────────────────────────────────┤
│ 📈 도달 점수 (0~40): 조회수 평가        │
│ 💬 참여 점수 (0~30): 시청자 반응 평가   │
│ ⏱️  유지 점수 (0~20): 시청자 만족도     │
│ 🚀 성장 점수 (0~10): 채널 성장 기여도   │
└─────────────────────────────────────────┘
```

### 채널 단계별 가중치

- **초기 채널** (0~1,000명): 참여도 40% > 도달 30%
- **성장 채널** (1,000~10,000명): 도달 40% > 참여 30%
- **성숙 채널** (10,000~100,000명): 도달 35% > 성장 30%
- **대형 채널** (100,000명+): 성장 40% > 도달 30%

### API 응답 예시

```json
{
  "improvedVideoAnalysis": [
    {
      "videoId": "...",
      "title": "영상 제목",
      "growthScore": 27,
      "reachScore": 33,
      "engagementScore": 30,
      "retentionScore": 20,
      "growthImpactScore": 10,
      "channelStage": "초기 채널",
      "insights": [
        "📌 조회수 개선 필요: SEO 최적화와 재생목록 활용을 고려하세요.",
        "✅ 참여도 우수: 시청자와의 상호작용이 잘 이루어지고 있습니다."
      ]
    }
  ]
}
```

### 상세 문서

- **[IMPROVED_ALGORITHM.md](docs/IMPROVED_ALGORITHM.md)** - 개선된 알고리즘 상세 설명
- **[ALGORITHM_COMPARISON.md](docs/ALGORITHM_COMPARISON.md)** - 기존 vs 개선 비교

---

## API

### 1. 유튜브 기반 주제 추천

채널 정보를 분석하여 AI가 다음 영상 주제 3개를 추천합니다.

```
POST /ai_recommend
Content-Type: application/json
```

#### Request Body

| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `requestURL` | String | ✅ | 유튜브 채널 URL | `https://youtube.com/@codingapple` |
| `keywords` | String | ✅ | 원하는 콘텐츠 키워드 | `유튜브 성장` |
| `category` | String | ✅ | 콘텐츠 카테고리 | `교육` |

```json
{
  "requestURL": "https://youtube.com/@codingapple",
  "keywords": "유튜브 성장",
  "category": "교육"
}
```

#### Response

`List<Map<String, String>>` — 추천 주제 3개

| 필드 | 설명 |
|------|------|
| `suggestedTitle` | 추천 영상 제목 |
| `conceptSummary` | 기획 의도 한 줄 요약 |

```json
[
  {
    "suggestedTitle": "유튜브 알고리즘이 좋아하는 영상 구조 3가지",
    "conceptSummary": "조회수를 높이는 영상 흐름을 실전 예시로 분석"
  },
  {
    "suggestedTitle": "구독자 1000명까지 가장 빠른 방법",
    "conceptSummary": "초기 채널 성장 전략을 단계별로 정리"
  },
  {
    "suggestedTitle": "썸네일 클릭률을 2배 올리는 디자인 법칙",
    "conceptSummary": "CTR을 높이는 썸네일 구성 요소 분석"
  }
]
```

---

### 2. 채널 분석

유튜브 채널을 분석합니다. 채널 ID, @handle, 채널 URL 모두 지원합니다. 30일 캐싱 적용.

```
GET /analyze/channel?channel={channel}
```

#### Request Params

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `channel` | String | 채널 ID, @handle, 또는 채널 URL | `@codingapple` 또는 `https://youtube.com/@codingapple` |

#### Response

```json
{
  "channel": {
    "channelId": "UCxxx",
    "name": "코딩애플",
    "profileImageUrl": "https://...",
    "subscriberCount": 441000
  },

  "channelScore": {
    "overall": 76,
    "topPercent": 24,
    "comment": "상위 24%에 위치한 채널이에요! 썸네일에 숫자와 질문형 제목을 활용하면 도달력을 더 높일 수 있습니다.",
    "factors": [
      { "name": "도달력", "score": 72, "weight": 60, "description": "구독자 대비 조회수" },
      { "name": "시청자 반응", "score": 78, "weight": 25, "description": "좋아요+댓글 비율" },
      { "name": "콘텐츠 만족도", "score": 80, "weight": 15, "description": "좋아요 비율" }
    ]
  },

  "summary": {
    "avgViewCount": 150000.0,
    "avgViewCountChange": 12.5,
    "uploadFrequencyPerWeek": 2.5,
    "uploadFrequencyChange": -8.3,
    "avgWatchDurationSeconds": null,
    "avgWatchDurationChange": null,
    "subscriberChange": 15000,
    "subscriberChangePercent": 3.5
  },

  "guides": [
    { "title": "업로드 주기 늘리기", "description": "주 2회 업로드 시 성장률이 20% 높아져요!" },
    { "title": "영상 길이 최적화", "description": "동일 카테고리 대비 영상이 길어요. 10분 이내로 줄이면 시청 유지율이 올라갈 수 있어요." },
    { "title": "시청자 반응 유도", "description": "댓글 유도 질문을 영상 중간에 넣어보세요." }
  ],

  "percentileVideoAnalysis": [
    {
      "videoId": "abc123",
      "title": "구글 신제품 때문에 완전히 멘탈이 나가버린 유저들",
      "thumbnailUrl": "https://...",
      "percentileScore": 84,
      "vpsScore": 88,
      "engagementScore": 77,
      "likeRateScore": 81,
      "isShort": false,
      "matched": true,
      "reason": "도달력이(가) 상위 12%로 뛰어나요. 시청자 반응을(를) 개선하면 점수가 올라갈 수 있어요."
    }
  ],

  "percentileDataCollectedAt": "2026-05-04T05:32:04+00:00"
}
```

#### 응답 필드 설명

| 필드 | 설명 |
|------|------|
| **channel** | 채널 기본 정보 |
| **channelScore.overall** | 채널 종합 점수 (0~100, 영상 평균 백분위) |
| **channelScore.topPercent** | 상위 몇 % (100 - overall) |
| **channelScore.comment** | 데이터 기반 상태 + AI 생성 개선 조언 |
| **channelScore.factors** | 점수 구성 요인 3개 (도달력 60%, 시청자반응 25%, 만족도 15%) |
| **summary.avgViewCount** | 채널 전체 평균 조회수 |
| **summary.avgViewCountChange** | 이전 분석 대비 평균 조회수 변화율 (%, 첫 분석 시 null) |
| **summary.uploadFrequencyPerWeek** | 주당 업로드 빈도 |
| **summary.uploadFrequencyChange** | 이전 분석 대비 업로드 빈도 변화율 (%, 첫 분석 시 null) |
| **summary.avgWatchDurationSeconds** | 평균 시청 지속 시간 (Analytics API 연동 전 null) |
| **summary.avgWatchDurationChange** | 이전 분석 대비 시청 지속 시간 변화율 (%, 미구현 null) |
| **summary.subscriberChange** | 이전 분석 대비 구독자 증감 수 (첫 분석 시 null) |
| **summary.subscriberChangePercent** | 이전 분석 대비 구독자 증감률 (%, 첫 분석 시 null) |
| **guides** | AI 생성 채널 성장 가이드 3개 (Bedrock, 점수 데이터 기반) |
| **percentileVideoAnalysis** | 영상별 백분위 점수 + 구성 요인 + 이유 |
| **percentileVideoAnalysis[].reason** | 영상 점수에 대한 데이터 기반 설명 (템플릿) |
| **percentileDataCollectedAt** | 백분위 테이블 수집 일시 |

---

### 3. 영상 기획 및 제목 생성

채널 최신 영상을 직접 분석하여 발화자 말투와 스타일을 반영한 기획안과 추천 제목을 생성합니다.
또한 기획안과 유사한 영상 3개와 유사한 유튜버 2명을 자동으로 검색하여 제공합니다.

```
POST /ai_script
Content-Type: application/json
```

#### Request Body

| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `requestURL` | String | ✅ | 유튜브 채널 URL | `https://youtube.com/@codingapple` |
| `title` | String | ✅ | 선택한 추천 영상 제목 | `유튜브 알고리즘이 좋아하는 영상 구조` |
| `concept` | String | ✅ | 기획 컨셉 | `조회수를 높이는 영상 흐름 분석` |
| `keywords` | String | ✅ | 콘텐츠 키워드 | `유튜브 성장` |
| `category` | String | ✅ | 콘텐츠 카테고리 | `교육, IT` |
| `time` | int | ✅ | 목표 영상 길이 (분) | `5` |

```json
{
  "requestURL": "https://youtube.com/@codingapple",
  "title": "유튜브 알고리즘이 좋아하는 영상 구조 3가지",
  "concept": "조회수를 높이는 영상 흐름을 실전 예시로 분석",
  "keywords": "유튜브 성장",
  "category": "교육, IT",
  "time": 5
}
```

#### Response

`List<Map<String, Object>>` — 기획안, 추천 제목, 썸네일, 유사 영상/유튜버

| 필드 | 타입 | 설명 |
|------|------|------|
| `conceptSummary` | String | 발화자 말투를 반영한 상세 기획안 (훅 → 전개 → 클라이맥스 → 마무리) |
| `suggestedTitles` | List\<String\> | AI 추천 제목 5개 |
| `thumbnail` | Object | 썸네일 정보 객체 |
| `thumbnail.thumbnailImage` | String | AI 생성 썸네일 S3 URL (생성 실패 시 필드 없음) |
| `thumbnail.thumbnailGuide` | String | 썸네일 구성 가이드 (색상, 레이아웃, 분위기 등) |
| `similarVideos` | List\<Object\> | 기획안과 유사한 영상 3개 |
| `similarVideos[].videoUrl` | String | 유사 영상 YouTube URL |
| `similarVideos[].videoTitle` | String | 유사 영상 제목 |
| `similarCreators` | List\<Object\> | 유사한 유튜버 2명 |
| `similarCreators[].channelUrl` | String | 유튜버 채널 URL |
| `similarCreators[].creatorName` | String | 유튜버 이름 |

```json
[
  {
    "conceptSummary": "오프닝: '여러분 혹시 영상 올렸는데 조회수가 안 나온 적 있으시죠?' 로 공감 훅 시작...",
    "suggestedTitles": [
      "유튜브 알고리즘이 좋아하는 영상 구조 3가지 (이것만 알면 조회수 달라짐)",
      "조회수 안 나오는 영상의 공통점 | 구조가 문제입니다",
      "유튜브 잘 되는 영상 vs 안 되는 영상 차이점 분석",
      "알고리즘 탈 수 있는 영상 만드는 법 (실전 비교)",
      "영상 구조만 바꿔도 조회수 2배 | 유튜브 성장 공식"
    ],
    "thumbnail": {
      "thumbnailImage": "https://pj-kmucd1-08-s3-thumbnails.s3.amazonaws.com/thumbnails/xxxx.png",
      "thumbnailGuide": "밝은 배경에 큰 텍스트로 '3가지' 강조, 화살표 이미지로 상승 추세 표현"
    },
    "similarVideos": [
      {
        "videoUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "videoTitle": "유튜브 조회수 늘리는 방법 TOP 5"
      },
      {
        "videoUrl": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "videoTitle": "영상 구조 분석 | 성공한 유튜버들의 공통점"
      },
      {
        "videoUrl": "https://www.youtube.com/watch?v=9bZkp7q19f0",
        "videoTitle": "알고리즘 이해하고 영상 만들기"
      }
    ],
    "similarCreators": [
      {
        "channelUrl": "https://www.youtube.com/channel/UCxxxxxx",
        "creatorName": "유튜브 성장 전문가 채널"
      },
      {
        "channelUrl": "https://www.youtube.com/channel/UCyyyyyy",
        "creatorName": "콘텐츠 기획 마스터"
      }
    ]
  }
]
```

---

## 내부 처리 흐름

### `/ai_recommend` 처리 흐름

```
1. 채널 URL → YoutubeAPIService.getData()
   ├── 채널 ID 추출 (@handle 또는 /channel/UC... 형식 지원)
   ├── 채널 기본 정보 조회 (채널명, 채널 설명)
   ├── 업로드 플레이리스트에서 최근 영상 10개 ID 수집
   └── 영상별 태그(빈도 집계), 토픽 카테고리, 제목 수집 → RecommendForm 반환

2. RecommendForm + category + keywords → GeminiService.recommendTopic()
   └── Gemini API 호출 → JSON 파싱 → List<Map<String, String>> 반환
```

### `/ai_script` 처리 흐름

```
1. 채널 URL → YoutubeAPIService.getData() → RecommendForm
2. 채널 URL → YoutubeAPIService.getLatestVideoUrl()
   └── 최근 10개 영상 중 10분 이하인 가장 최신 영상 URL 반환
3. RecommendForm + latestVideoUrl + ... → GeminiService.writeScript()
   ├── Gemini 멀티모달 API로 영상 직접 시청 분석
   └── 발화자 말투 파악 → 기획안 + 제목 5개 + 썸네일 가이드 생성
4. 썸네일 생성 (실패해도 나머지 응답은 정상 반환)
   ├── YoutubeAPIService.getRecentThumbnailImages() → 최신 썸네일 3개 다운로드
   ├── BedrockService.analyzeThumbnailsAndGeneratePrompt() → Claude Vision으로 스타일 분석 + Imagen 프롬프트 생성
   ├── ImagenService.generateThumbnail() → Imagen 4로 16:9 썸네일 이미지 생성
   └── S3Service.uploadBase64Image() → S3 업로드 후 URL 반환 → 응답에 thumbnail 객체 추가
5. 유사한 영상 3개 검색
   └── YoutubeAPIService.getSimilarVideos(concept, keywords)
       ├── 기획안 요약 + 키워드로 YouTube 검색
       └── 상위 3개 영상의 URL + 제목 반환
6. 유사한 유튜버 2명 검색
   └── YoutubeAPIService.getSimilarCreators(keywords, category)
       ├── 키워드 + 카테고리 + "creator"로 채널 검색
       └── 상위 2개 채널의 URL + 이름 반환
7. 최종 응답 구성
   └── conceptSummary + suggestedTitles + thumbnail + similarVideos + similarCreators
```

---

## YouTube 채널 데이터 수집 방식

| 항목 | 수집 방법 | 설명 |
|------|-----------|------|
| 채널 ID | `channels?forHandle=` | @handle 형식 URL 지원 |
| 채널명 / 채널 설명 | `channels?part=snippet` | 기본 채널 정보 |
| 최근 영상 목록 | `playlistItems` (UC→UU 변환) | search API 대비 쿼터 100배 절약 |
| 태그 빈도 집계 | `videos?part=snippet` | 영상 10개 태그 빈도 내림차순 Top 20 |
| 토픽 카테고리 | `videos?part=topicDetails` | 중복 제거 후 수집 |
| 최신 영상 URL | `videos?part=contentDetails` | 10분 이하 영상 우선 반환 |

---

## DB 구조 (채널 분석 캐시)

### channel_cache

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | BIGINT | PK |
| `channel_id` | VARCHAR | 유튜브 채널 ID (unique) |
| `channel_name` | VARCHAR | 채널명 |
| `profile_image_url` | VARCHAR | 프로필 이미지 URL |
| `subscriber_count` | BIGINT | 현재 구독자 수 |
| `previous_subscriber_count` | BIGINT | 이전 캐시 시점 구독자 수 |
| `total_video_count` | BIGINT | 전체 영상 수 |
| `avg_view_count` | DOUBLE | 평균 조회수 |
| `previous_avg_view_count` | DOUBLE | 이전 캐시 시점 평균 조회수 |
| `upload_frequency_per_week` | DOUBLE | 주 업로드 빈도 |
| `previous_upload_frequency_per_week` | DOUBLE | 이전 캐시 시점 업로드 빈도 |
| `avg_watch_duration_seconds` | DOUBLE | 평균 시청 지속 시간 (미구현, null) |
| `percentile_score` | INT | 백분위 종합 점수 (이전 비교용) |
| `percentile_vps` | INT | 도달력 백분위 |
| `percentile_engagement` | INT | 시청자 반응 백분위 |
| `percentile_like_rate` | INT | 콘텐츠 만족도 백분위 |
| `guides_json` | TEXT | AI 생성 가이드 JSON 문자열 |
| `fetched_at` | DATETIME | 수집 시각 (캐시 만료 기준) |
| `fetched_at` | DATETIME | 수집 시각 (캐시 만료 기준) |

### video_cache

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | BIGINT | PK |
| `channel_id` | VARCHAR | 유튜브 채널 ID |
| `video_id` | VARCHAR | 유튜브 영상 ID |
| `title` | VARCHAR | 영상 제목 |
| `thumbnail_url` | VARCHAR | 썸네일 URL |
| `view_count` | BIGINT | 조회수 |
| `like_count` | BIGINT | 좋아요 수 |
| `comment_count` | BIGINT | 댓글 수 |
| `duration_seconds` | BIGINT | 영상 길이 (초) |
| `algorithm_score` | INT | 알고리즘 점수 (0~100) |
| `video_rank` | INT | 최신순 순위 (1~10) |
| `fetched_at` | DATETIME | 수집 시각 (캐시 만료 기준) |

> 테이블은 `spring.jpa.hibernate.ddl-auto=update` 설정으로 서버 시작 시 자동 생성/변경됩니다.

---

## YouTube API 사용량

YouTube Data API는 하루 **10,000 유닛** 무료 할당량이 있습니다.

### 캐시 미스 (최초 조회 or 30일 만료 시)

| API 호출 | 방식 | 유닛 |
|---------|------|------|
| 채널 정보 조회 (`channels?part=snippet,statistics`) | - | 3 유닛 |
| 최신 영상 ID 조회 (`playlistItems`) | UC→UU 변환 | 1 유닛 |
| 영상 상세 조회 (`videos?part=snippet,statistics,contentDetails`) | - | 3 유닛 |
| **합계** | | **7 유닛 / 1회** |

### 캐시 히트 (30일 이내 재조회 시)

| 항목 | 유닛 |
|------|------|
| YouTube API 호출 | **0 유닛** |
| Bedrock 호출 | 없음 (guidesJson 캐시) |

> 하루 10,000 유닛 기준으로 캐시 미스 시 약 **1,428회** 채널 분석 가능

---

## 프로젝트 구조

```
src/main/java/com/capstone/crit/
├── controller/
│   ├── MainController.java            # /ai_recommend, /ai_script 엔드포인트
│   └── AnalyzeController.java         # /analyze/channel 엔드포인트
├── security/
│   ├── SecurityConfig.java            # Spring Security + CORS 설정
│   ├── CustomOAuth2UserService.java   # Google OAuth2 로그인 처리
│   ├── OAuth2SuccessHandler.java      # 로그인 성공 → YouTube 채널 수집 + JWT 발급
│   ├── JwtTokenProvider.java          # JWT 생성/검증
│   └── JwtAuthenticationFilter.java   # 요청별 JWT 인증 필터
├── service/
│   ├── GeminiService.java             # Google Gemini API 연동
│   ├── YoutubeAPIService.java         # YouTube Data API 연동
│   ├── ChannelAnalyzeService.java     # 채널 분석 (캐싱 + 점수 계산 + 가이드 생성)
│   ├── ImprovedScoringService.java    # 개선된 다층 점수 시스템
│   ├── PercentileScoringService.java  # 백분위 기반 점수 계산 (S3 연동)
│   ├── BedrockService.java            # AWS Bedrock Claude — 썸네일 분석 + 가이드 생성
│   ├── ImagenService.java             # Google Imagen 4 — 썸네일 이미지 생성
│   ├── S3Service.java                 # AWS S3 — 썸네일 이미지 업로드
│   └── AIService.java                 # AI 서비스 인터페이스
├── entity/
│   ├── User.java                      # 유저 (Google OAuth2 + YouTube 채널 정보)
│   ├── ApiLog.java
│   ├── RecommendLog.java
│   ├── ScriptLog.java
│   ├── ChannelCache.java              # 채널 캐시 (30일)
│   └── VideoCache.java                # 영상 캐시 (30일)
├── repository/
│   ├── UserRepository.java
│   ├── ApiLogRepository.java
│   ├── RecommendLogRepository.java
│   ├── ScriptLogRepository.java
│   ├── ChannelCacheRepository.java
│   └── VideoCacheRepository.java
├── form/
│   └── RecommendForm.java
├── dto/
│   └── TrendRequest.java
├── CorsConfig.java
└── SwaggerConfig.java
```

### RecommendForm 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `title` | String | 채널명 |
| `description` | String | 채널 설명 |
| `tags` | List\<String\> | 빈도순 상위 20개 태그 |
| `topicCategories` | List\<String\> | Wikipedia 기반 토픽 카테고리 URL 목록 |
| `recentTitles` | List\<String\> | 최근 영상 제목 목록 |

---

## 📊 백분위 기반 점수 모델 (Percentile Scoring)

### 개요

89,000개 이상의 실제 유튜브 영상 데이터(14개 카테고리, 1,900+ 채널)를 수집·분석하여 만든 **데이터 기반 점수 모델**. 기존 AI 임의 공식 대신, 같은 조건의 영상들 중 상위 몇 %인지를 점수로 반환한다.

### 아키텍처

```
┌─ 데이터 파이프라인 ──────────────────────────────────┐
│  API Gateway POST /collect                          │
│       ↓                                             │
│  Lambda (Python 3.14)                               │
│   ├ YouTube API 수집 (mostPopular + search fallback)│
│   ├ 백분위 테이블 계산                                 │
│   └ S3 저장 (latest.json)                            │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─ crit-server ───────────────────────────────────────┐
│  PercentileScoringService                           │
│   ├ 서버 시작 시 S3에서 latest.json 로드              │
│   ├ 1시간마다 자동 갱신 (@Scheduled)                  │
│   └ score() → 백분위 조회 → 점수 반환                 │
└─────────────────────────────────────────────────────┘
```

### 점수 공식

```
점수 = 도달력(VPS) 백분위 × 0.60 + 시청자반응(참여율) 백분위 × 0.25 + 콘텐츠만족도(좋아요율) 백분위 × 0.15
```

| 요인 | 가중치 | 상관계수 | 설명 |
|------|--------|---------|------|
| 도달력 (views_per_sub) | 60% | +0.78 | 구독자 대비 조회수 |
| 시청자 반응 (engagement_rate) | 25% | -0.16 | (좋아요+댓글) / 조회수 |
| 콘텐츠 만족도 (like_rate) | 15% | -0.14 | 좋아요 / 조회수 |

가중치는 82,000개 영상 데이터의 상관관계 분석에서 도출.

### 비교 그룹

`구독자 구간` × `숏폼/롱폼` × `카테고리`

| 구독자 구간 | 범위 |
|---|---|
| S | 0 ~ 50,000 |
| M | 50,000 ~ 200,000 |
| L | 200,000 ~ 500,000 |
| XL | 500,000+ |

숏폼/롱폼 기준: 영상 길이 60초

### 점수 해석

| 점수 | 의미 |
|------|------|
| 90점 | 같은 조건에서 상위 10% |
| 75점 | 상위 25% |
| 50점 | 중간 |
| 25점 | 하위 25% |

### 코멘트 생성

- **1줄 (데이터 기반)**: "상위 24%에 위치한 채널이에요! 지난 분석 대비 3점 상승했어요."
- **2줄 (AI 생성, Bedrock)**: 약점 개선을 위한 구체적 행동 조언

### 가이드 생성

Bedrock AI가 채널 데이터(구독자, 업로드 빈도, 평균 조회수, 영상 길이, 점수 요인)를 기반으로 **정확히 3개**의 구체적 성장 가이드를 생성.

### 관련 프로젝트

- [crit-data-collector](https://github.com/AWS-Capstone8/crit-data-collector) — 데이터 수집 Lambda + 점수 모델 분석

---

## ⚠️ 알려진 이슈 및 개선 예정

- `/ai_script` 호출 시 `youtubeAPIService.getData()`가 중복 호출됨 → Redis 캐싱으로 개선 예정

---

## 변경 이력

### 2026-05-04
- **백분위 기반 점수 모델 추가 및 API 응답 재설계**
  - `PercentileScoringService` 추가: S3에서 백분위 테이블 로드 + 점수 계산
  - 89,000개 실제 영상 데이터 기반, 구독자 구간 × 숏폼/롱폼 × 카테고리별 분리 비교
  - 1시간마다 S3에서 최신 테이블 자동 갱신 (`@Scheduled`)
  - `ChannelAnalyzeService` 전면 수정
    - `algorithmScore`, `recentVideos`, `improvedVideoAnalysis` 삭제
    - `channelScore` 추가: 종합 점수 + 상위 % + AI 코멘트 + 구성 요인 3개
    - `summary` 개선: 이전 분석 대비 변화율 (avgViewCountChange, uploadFrequencyChange, subscriberChange, subscriberChangePercent)
    - `guides` 개선: Bedrock AI가 점수 데이터 기반으로 정확히 3개 가이드 생성
    - `percentileVideoAnalysis` 추가: 영상별 백분위 점수 + 구성 요인 + 이유(reason)
  - `ChannelCache` 엔티티 확장: 백분위 점수 4개 + 이전 평균조회수/업로드빈도 저장
  - `VideoCache` 엔티티: `categoryId` 필드 추가
  - `CritApplication`에 `@EnableScheduling` 추가
  - `application.properties`에 `aws.s3.scoring-bucket` 설정 추가
  - `build.gradle`에 .env 자동 로드 로직 추가

### 2026-04-24
- **개선된 YouTube 성장 중심 알고리즘 추가**
  - `ImprovedScoringService` 추가: 다층 점수 시스템 구현
    - 도달 점수 (0~40): 로그 스케일 조회수 평가
    - 참여 점수 (0~30): 카테고리별 벤치마크 기반 상대 참여도 평가
    - 유지 점수 (0~20): 댓글/좋아요 비율로 시청자 만족도 추정
    - 성장 점수 (0~10): 채널 성장에 대한 영상의 기여도 평가
  - 채널 단계별 동적 가중치 적용
    - 초기 채널 (0~1,000명): 참여도 40% 중심
    - 성장 채널 (1,000~10,000명): 도달 40% 중심
    - 성숙 채널 (10,000~100,000명): 성장 30% 중심
    - 대형 채널 (100,000명+): 성장 40% 중심
  - 카테고리별 벤치마크 (교육, 엔터테인먼트, 게임, 뷰티, 음악, 기술, 일상)
  - 시간 가중치: 최신 영상에 1.0~1.3배 가중치 부여
  - 실행 가능한 인사이트 자동 생성
  - `ChannelAnalyzeService` 수정: `improvedVideoAnalysis` 필드 추가
    - 각 영상별 상세 점수 및 인사이트 제공
  - 문서 추가
    - `docs/IMPROVED_ALGORITHM.md`: 알고리즘 상세 설명
    - `docs/ALGORITHM_COMPARISON.md`: 기존 vs 개선 비교
    - `docs/IMPLEMENTATION_GUIDE.md`: 구현 가이드
  - README 업데이트: 개선된 알고리즘 섹션 추가

### 2026-04-23
- **채널 분석 페이지 API 추가** (`GET /analyze/channel`)
  - `ChannelCache` 엔티티 추가: 채널 기본 정보 + 통계 (30일 캐싱)
  - `VideoCache` 엔티티 추가: 최신 영상 10개 정보 + 알고리즘 점수 (30일 캐싱)
  - `ChannelCacheRepository`, `VideoCacheRepository` 추가
  - `ChannelAnalyzeService` 추가
    - YouTube Data API로 채널/영상 데이터 수집
    - 30일 캐싱 정책 적용 (재요청 시 DB에서 반환, 만료 시 YouTube API 재호출)
    - 영상 알고리즘 점수 계산 (조회수 비율 + 인게이지먼트율 + 영상 길이 보너스)
    - 구독자 성장률 계산 (이전 캐시 구독자 수 vs 현재 비교)
    - Bedrock Claude로 채널 방향 가이드 AI 생성
  - `AnalyzeController` 추가: `GET /analyze/channel?channelId=` 엔드포인트
  - `BedrockService.invokeModelPublic()` 추가
  - `application.properties`에 `youtube.api.key` 설정 추가
  - AWS RDS MySQL 연동 (엔드포인트: `pj-kmucd1-08-db.cj24wem202yj.us-east-1.rds.amazonaws.com`)



### 2026-04-07
- **유사 영상/유튜버 검색 API 호출 방식 개선**
  - `YoutubeAPIService.getSimilarVideos()` 수정: RestTemplate → HttpURLConnection 변경
  - `YoutubeAPIService.getSimilarCreators()` 수정: RestTemplate → HttpURLConnection 변경
  - 이유: RestTemplate의 HTTPS 연결 문제로 인한 0개 결과 반환 → HttpURLConnection으로 안정적인 API 호출 구현
  - 결과: YouTube API 검색 결과 정상 반환 확인 ✅

### 2026-04-06
- **유사 영상/유튜버 검색 기능 추가** (`POST /ai_script` 응답에 `similarVideos`, `similarCreators` 추가)
  - `YoutubeAPIService.getSimilarVideos()` 추가: 기획안과 유사한 영상 3개 검색 (URL + 제목)
  - `YoutubeAPIService.getSimilarCreators()` 추가: 유사한 유튜버 2명 검색 (채널 URL + 이름)
  - `MainController.AIScript()` 수정: 응답에 `similarVideos`, `similarCreators` 필드 포함
  - 응답 구조: `thumbnail` 객체로 썸네일 정보 통합 (thumbnailImage + thumbnailGuide)
  - README 업데이트: 새로운 기능 및 응답 구조 문서화

### 2026-04-05
- **썸네일 자동 생성 기능 추가** (`POST /ai_script` 응답에 `thumbnailImage` 추가)
  - `YoutubeAPIService.getRecentThumbnailImages()` 추가: 채널 최신 썸네일 3개 수집
  - `BedrockService.analyzeThumbnailsAndGeneratePrompt()` 추가: Claude Sonnet 4 Vision으로 썸네일 스타일 분석 및 Imagen 프롬프트 생성
  - `ImagenService` 추가: GCP 서비스 계정 JWT 인증 후 Imagen 4로 16:9 썸네일 이미지 생성
  - `S3Service` 추가: 생성된 이미지를 S3에 업로드 후 URL 반환
  - `build.gradle`에 S3, WebFlux, JJWT 의존성 추가
  - `application.properties`에 `aws.s3.bucket`, `gcp.key-path` 설정 추가
