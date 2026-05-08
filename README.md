# CRIT - 유튜브 크리에이터 AI 분석 플랫폼

## 1. 프로젝트 소개

CRIT는 유튜브 크리에이터를 위한 AI 기반 채널 분석 및 콘텐츠 기획 플랫폼입니다.

실제 유튜브 데이터 82,000개 이상의 영상을 수집·분석하여 **데이터 기반 백분위 점수 모델**을 구축하고, AI(Claude, Gemini)를 활용한 콘텐츠 추천 및 기획안 생성 기능을 제공합니다.

### 주요 기능

- **채널 분석**: 구독자 구간 × 숏폼/롱폼 × 카테고리별 백분위 기반 점수 산출
- **AI 주제 추천**: 채널 특성과 트렌드를 반영한 다음 영상 주제 3개 추천
- **AI 기획안 생성**: 영상 분석 기반 기획안 + 제목 5개 + 썸네일 가이드
- **트렌드 키워드**: 실시간 유튜브 인기 동영상 기반 TOP 100 키워드 추출

### 점수 모델

기존 알고리즘의 "대부분 100점 수렴" 문제를 해결하기 위해, **"같은 조건의 영상들 중 상위 몇 %인가"**를 계산하는 백분위 방식을 채택했습니다.

```
비교 그룹 = 구독자 구간(S/M/L/XL) × 숏폼/롱폼 × 카테고리
점수 = VPS 백분위 × 0.60 + 참여율 백분위 × 0.25 + 좋아요율 백분위 × 0.15
```

## 2. 소개 영상

> 추후 추가 예정

## 3. 팀 소개

| 이름 | 역할 | GitHub |
|------|------|--------|
| 이재원 | Backend / Data Pipeline | [@2wodnjs7](https://github.com/2wodnjs7) |
| (팀원 추가) | Frontend | |

## 4. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite + TailwindCSS)                      │
│  - 채널 분석 대시보드                                         │
│  - AI 추천/기획 폼                                           │
│  - 트렌드 키워드 워드클라우드                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  Backend (Spring Boot 4.0.3 / Java 17)                      │
│  - YouTube Data API v3 연동                                  │
│  - AWS Bedrock (Claude) - 가이드/코멘트 생성                   │
│  - Google Gemini - 주제 추천/기획안                            │
│  - Google Imagen 4.0 - 썸네일 생성                            │
│  - S3 백분위 테이블 기반 점수 계산                               │
│  - Google OAuth2 + JWT 인증                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  Data Pipeline (AWS Lambda)                                  │
│                                                              │
│  ┌─ data-collector ─────────────────────────────────┐        │
│  │  YouTube 카테고리별 채널/영상 대량 수집              │        │
│  │  → 백분위 테이블 계산 → S3 저장                    │        │
│  └──────────────────────────────────────────────────┘        │
│                                                              │
│  ┌─ trending-keywords ──────────────────────────────┐        │
│  │  인기 동영상 200개 → 형태소 분석 → TOP 100 키워드   │        │
│  │  → S3 저장 + API 응답                             │        │
│  └──────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  AWS Infrastructure                                          │
│  - EC2: Backend + Frontend 호스팅                             │
│  - RDS (MySQL): 사용자, 캐시, 로그                             │
│  - S3: 백분위 테이블, 키워드 데이터, 썸네일                      │
│  - API Gateway: Lambda 트리거                                 │
└──────────────────────────────────────────────────────────────┘
```

## 5. 기술 스택

| 분류 | 기술 |
|------|------|
| Frontend | React 19, TypeScript, Vite 8, TailwindCSS 4, Zustand, Axios |
| Backend | Spring Boot 4.0.3, Java 17, JPA, Spring Security, OAuth2 |
| AI/ML | AWS Bedrock (Claude 3.5 Sonnet), Google Gemini 3.1, Google Imagen 4.0 |
| Data | YouTube Data API v3, kiwipiepy (형태소 분석) |
| Infra | AWS EC2, RDS (MySQL), S3, Lambda, API Gateway |
| DevOps | Gradle, pnpm, Git Subtree |

## 6. 프로젝트 구조

```
2026-capstone-58/
├── frontend/              # React 프론트엔드
│   ├── src/
│   │   ├── pages/         # 페이지 (분석, 추천, 로그인)
│   │   ├── components/    # UI 컴포넌트
│   │   ├── stores/        # Zustand 상태 관리
│   │   ├── api/           # API 호출
│   │   └── mocks/         # MSW 목 데이터
│   └── package.json
├── backend/               # Spring Boot 백엔드
│   ├── src/main/java/com/capstone/crit/
│   │   ├── controller/    # REST API 컨트롤러
│   │   ├── service/       # 비즈니스 로직
│   │   ├── entity/        # JPA 엔티티
│   │   ├── repository/    # 데이터 접근
│   │   └── security/      # OAuth2 + JWT
│   └── build.gradle
├── data-collector/        # YouTube 데이터 수집 Lambda
│   ├── lambda_function.py # 수집 → 백분위 계산 → S3 저장
│   ├── collect.py         # 로컬 수집 모듈
│   └── collect_all.py     # 전체 카테고리 일괄 수집
├── trending-keywords/     # 트렌드 키워드 추출 Lambda
│   └── lambda_function.py # 인기 동영상 → 키워드 TOP 100
└── README.md
```

## 7. 설치 및 실행

### 사전 요구사항

- Java 17+
- Node.js 22+ / pnpm
- MySQL 8+
- YouTube Data API v3 키
- AWS 계정 (Bedrock, S3 접근)

### Backend

```bash
cd backend
cp .env.example api_env/.env
# api_env/.env에 실제 값 설정

./gradlew bootRun
# http://localhost:8080
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev --host
# http://localhost:5173
```

### Data Collector (로컬 실행)

```bash
cd data-collector
pip install requests python-dotenv
cp .env.example .env
# .env에 YOUTUBE_API_KEY 설정

python3 collect.py "@channelhandle"       # 단일 채널
python3 collect_all.py 20 28              # 특정 카테고리
```

### Trending Keywords (Lambda 배포)

```bash
cd trending-keywords
./deploy.sh
```

## 8. API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/analyze/channel?channel=@handle` | 채널 종합 분석 |
| POST | `/ai_recommend` | AI 주제 추천 |
| POST | `/ai_script` | AI 기획안 생성 |
| GET | `(API Gateway)/collect` | 데이터 수집 트리거 |
| GET | `(API Gateway)/words` | 트렌드 키워드 TOP 100 |

## 9. 수집 데이터 규모

- 총 172,543개 영상 / 3,612개 채널 / 14개 카테고리
- 백분위 그룹 112개 (구독자 구간 × 숏폼/롱폼 × 카테고리)
- 점수 분포: 정규분포에 가까움 (40~60점 구간 32.3%)
