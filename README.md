# 🎬 CRIT Server

유튜브 채널 정보를 기반으로 AI가 콘텐츠 주제를 추천하고 영상 기획안 및 제목을 생성하는 Spring Boot 백엔드 서버입니다.
Google Gemini API와 YouTube Data API v3를 연동하여 채널 스타일을 분석하고 맞춤형 콘텐츠 전략을 제공합니다.

---

## 기술 스택

- **Java 17**
- **Spring Boot 4.0.3**
- **Google Gemini API** (gemini-2.0-flash-lite-preview) — 주제 추천 및 기획안 생성
- **Google Imagen 4** — AI 썸네일 이미지 생성
- **YouTube Data API v3** — 채널 정보 및 최신 영상 수집
- **AWS Bedrock (Claude Sonnet 4 Vision)** — 채널 썸네일 스타일 분석
- **AWS S3** — 생성된 썸네일 이미지 저장
- **SpringDoc OpenAPI (Swagger UI)**
- **Lombok**
- **Gradle**

---

## 시작하기

### 사전 요구사항

- Java 17+
- Google Gemini API 키
- YouTube Data API v3 키
- AWS 계정 및 Bedrock 접근 권한 (EC2 IAM Role 또는 AWS CLI 설정)
- AWS S3 버킷
- GCP 서비스 계정 키 (Imagen 사용)

### 환경 설정

`src/main/resources/application.properties`에 아래 값을 설정합니다.

```properties
gemini.api.key=YOUR_GEMINI_API_KEY
aws.region=us-east-1
aws.bedrock.model-id=anthropic.claude-3-haiku-20240307-v1:0
aws.s3.bucket=YOUR_S3_BUCKET_NAME
gcp.key-path=/path/to/gcp-key.json
```

> ⚠️ YouTube API Key는 현재 `YoutubeAPIService.java`에 하드코딩되어 있습니다. 추후 환경 변수로 분리가 필요합니다.

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

채널 ID로 유튜브 채널을 분석합니다. 30일 캐싱 적용.

```
GET /analyze/channel?channelId={channelId}
```

#### Request Params

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `channelId` | String | 유튜브 채널 ID | `UCSLrpBAzr-ROVGHQ5EmxnUg` |

> 채널 ID 조회: `https://www.googleapis.com/youtube/v3/channels?part=id&forHandle={handle}&key={API_KEY}`

#### Response

| 필드 | 설명 |
|------|------|
| `channel.name` | 채널명 |
| `channel.subscriberCount` | 구독자 수 |
| `channel.profileImageUrl` | 프로필 이미지 URL |
| `algorithmScore` | 채널 알고리즘 점수 (0~100) |
| `summary.avgViewCount` | 평균 조회수 |
| `summary.uploadFrequencyPerWeek` | 주 업로드 빈도 |
| `summary.avgWatchDurationSeconds` | 평균 시청 지속 시간 (Analytics API 연동 전 null) |
| `summary.subscriberGrowthRate` | 구독자 성장률 (%) |
| `guides` | AI 생성 채널 방향 가이드 (title + description) |
| `recentVideos` | 최신 영상 10개 (videoId, title, thumbnailUrl, algorithmScore) |

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
| `previous_subscriber_count` | BIGINT | 이전 캐시 시점 구독자 수 (성장률 계산용) |
| `total_video_count` | BIGINT | 전체 영상 수 |
| `avg_view_count` | DOUBLE | 평균 조회수 |
| `upload_frequency_per_week` | DOUBLE | 주 업로드 빈도 |
| `avg_watch_duration_seconds` | DOUBLE | 평균 시청 지속 시간 (Analytics API 연동 전 null) |
| `guides_json` | TEXT | AI 생성 가이드 JSON 문자열 |
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
├── service/
│   ├── GeminiService.java             # Google Gemini API 연동
│   ├── YoutubeAPIService.java         # YouTube Data API 연동
│   ├── ChannelAnalyzeService.java     # 채널 분석 (캐싱 + 점수 계산 + 가이드 생성)
│   ├── BedrockService.java            # AWS Bedrock Claude — 썸네일 분석 + 가이드 생성
│   ├── ImagenService.java             # Google Imagen 4 — 썸네일 이미지 생성
│   ├── S3Service.java                 # AWS S3 — 썸네일 이미지 업로드
│   └── AIService.java                 # AI 서비스 인터페이스
├── entity/
│   ├── ApiLog.java
│   ├── RecommendLog.java
│   ├── ScriptLog.java
│   ├── ChannelCache.java              # 채널 캐시 (30일)
│   └── VideoCache.java                # 영상 캐시 (30일)
├── repository/
│   ├── ApiLogRepository.java
│   ├── RecommendLogRepository.java
│   ├── ScriptLogRepository.java
│   ├── ChannelCacheRepository.java
│   └── VideoCacheRepository.java
├── form/
│   └── RecommendForm.java
├── dto/
│   └── TrendRequest.java
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

## ⚠️ 알려진 이슈 및 개선 예정

- `/ai_script` 호출 시 `youtubeAPIService.getData()`가 중복 호출됨 → Redis 캐싱으로 개선 예정
- YouTube API Key가 소스코드에 하드코딩되어 있음 → 환경 변수 분리 필요
- Gemini 모델 ID `gemini-3.1-flash-lite-preview` → 최신 모델로 업데이트 필요

---

## 변경 이력

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
