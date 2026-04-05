# 🎬 CRIT Server

유튜브 채널 정보를 기반으로 AI가 콘텐츠 주제를 추천하고 영상 기획안 및 제목을 생성하는 Spring Boot 백엔드 서버입니다.
Google Gemini API와 YouTube Data API v3를 연동하여 채널 스타일을 분석하고 맞춤형 콘텐츠 전략을 제공합니다.

---

## 기술 스택

- **Java 17**
- **Spring Boot 4.0.3**
- **Google Gemini API** (gemini-2.0-flash-lite-preview) — 주제 추천 및 기획안 생성
- **YouTube Data API v3** — 채널 정보 및 최신 영상 수집
- **SpringDoc OpenAPI (Swagger UI)**
- **Lombok**
- **Gradle**

---

## 시작하기

### 사전 요구사항

- Java 17+
- Google Gemini API 키
- YouTube Data API v3 키

### 환경 설정

`src/main/resources/application.properties`에 아래 값을 설정합니다.

```properties
gemini.api.key=YOUR_GEMINI_API_KEY
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

### 2. 영상 기획 및 제목 생성

채널 최신 영상을 직접 분석하여 발화자 말투와 스타일을 반영한 기획안과 추천 제목을 생성합니다.

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

`List<Map<String, Object>>` — 기획안 및 추천 제목

| 필드 | 타입 | 설명 |
|------|------|------|
| `conceptSummary` | String | 발화자 말투를 반영한 상세 기획안 (훅 → 전개 → 클라이맥스 → 마무리) |
| `suggestedTitles` | List\<String\> | AI 추천 제목 5개 |

```json
[
  {
    "conceptSummary": "오프닝: '여러분 혹시 영상 올렸는데 조회수가 안 나온 적 있으시죠?' 로 공감 훅 시작. 본론에서 알고리즘이 선호하는 영상 구조 3가지(초반 30초 집중, 중간 참여 유도, 마무리 CTA)를 실제 사례 비교로 설명. 마무리는 구독자에게 '댓글로 여러분 채널 고민 남겨주세요' 로 참여 유도.",
    "suggestedTitles": [
      "유튜브 알고리즘이 좋아하는 영상 구조 3가지 (이것만 알면 조회수 달라짐)",
      "조회수 안 나오는 영상의 공통점 | 구조가 문제입니다",
      "유튜브 잘 되는 영상 vs 안 되는 영상 차이점 분석",
      "알고리즘 탈 수 있는 영상 만드는 법 (실전 비교)",
      "영상 구조만 바꿔도 조회수 2배 | 유튜브 성장 공식"
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
   └── 발화자 말투 파악 → 기획안 + 제목 5개 생성
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

## 프로젝트 구조

```
src/main/java/com/capstone/crit/
├── controller/
│   └── MainController.java            # /ai_recommend, /ai_script 엔드포인트
├── service/
│   ├── GeminiService.java             # Google Gemini API 연동
│   ├── YoutubeAPIService.java         # YouTube Data API 연동
│   ├── BedrockService.java            # AWS Bedrock 연동 (미사용)
│   └── AIService.java                 # AI 서비스 인터페이스
├── form/
│   └── RecommendForm.java             # 채널 정보 객체
├── dto/
│   ├── AIRecommendRequestDto.java     # 주제 추천 요청 DTO
│   └── AIScriptRequestDto.java        # 기획 생성 요청 DTO
└── SwaggerConfig.java                 # Swagger 설정
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
