# 🎬 CRIT Server

유튜브 채널 정보를 기반으로 AI가 콘텐츠 주제를 추천하고 영상 기획안을 생성하는 Spring Boot 백엔드 서버입니다.

---

## 📌 주요 기능

| 기능 | 엔드포인트 | 설명 |
|------|-----------|------|
| 유튜브 기반 주제 추천 | `POST /ai_recommend` | 채널 정보 + 키워드/카테고리를 기반으로 AI가 영상 주제 3개 추천 |
| 영상 기획 및 제목 생성 | `POST /ai_script` | 채널 최신 영상을 분석해 기획안 + 추천 제목 5개 생성 |

---

## 🛠 기술 스택

- **Java 17**
- **Spring Boot 4.0.3**
- **Gradle**
- **Google Gemini API** (콘텐츠 추천 및 기획안 생성)
- **YouTube Data API v3** (채널 정보 수집)
- **SpringDoc OpenAPI (Swagger)**

---

## 🚀 실행 방법

```bash
# 프로젝트 루트에서
./gradlew bootRun

# 백그라운드 실행 (Cloud9 등 원격 환경)
nohup ./gradlew bootRun > server.log 2>&1 &
```

서버 기본 포트: **8080**

---

## 📄 API 명세

Swagger UI: `http://localhost:8080/swagger-ui.html`

---

### POST `/ai_recommend`

유튜브 채널 URL을 기반으로 AI가 콘텐츠 주제 3개를 추천합니다.

**Request Body**
```json
{
  "requestURL": "https://youtube.com/@codingapple",
  "keywords": "유튜브 성장",
  "category": "교육"
}
```

**Response**
```json
[
  {
    "suggestedTitle": "영상 후보 제목",
    "conceptSummary": "기획 의도 한 줄"
  },
  ...
]
```

---

### POST `/ai_script`

채널 최신 영상을 분석하여 기획안과 추천 제목을 생성합니다.

**Request Body**
```json
{
  "requestURL": "https://youtube.com/@codingapple",
  "title": "추천 영상 제목",
  "concept": "기획 컨셉",
  "keywords": "유튜브 성장",
  "category": "교육, IT",
  "time": 5
}
```

**Response**
```json
[
  {
    "conceptSummary": "발화자 말투를 살린 기획안",
    "suggestedTitles": [
      "제목 1",
      "제목 2",
      "제목 3",
      "제목 4",
      "제목 5"
    ]
  }
]
```

---

## ⚙️ 환경 설정

`application.properties` 또는 `application.yml`에 아래 값을 설정하세요.

```properties
gemini.api.key=YOUR_GEMINI_API_KEY
```

> YouTube API Key는 현재 `YoutubeAPIService.java`에 하드코딩되어 있습니다. 환경 변수로 분리하는 것을 권장합니다.

---

## 📁 프로젝트 구조

```
src/main/java/com/capstone/crit/
├── controller/
│   └── MainController.java       # API 엔드포인트
├── service/
│   ├── GeminiService.java        # Gemini AI 연동
│   └── YoutubeAPIService.java    # YouTube Data API 연동
├── form/
│   └── RecommendForm.java        # 채널 정보 객체
├── dto/
│   ├── AIRecommendRequestDto.java
│   └── AIScriptRequestDto.java
└── SwaggerConfig.java            # Swagger 설정
```

---

## ⚠️ 알려진 이슈

- `/ai_script` 호출 시 `youtubeAPIService.getData()`가 중복 호출됨 → 추후 Redis 캐싱으로 개선 예정
- YouTube API Key가 소스코드에 하드코딩되어 있음 → 환경 변수 분리 필요
