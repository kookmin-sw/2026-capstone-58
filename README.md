# YouTube Data Collector & Percentile Scoring

YouTube Data API v3를 활용하여 카테고리별 채널/영상 데이터를 수집하고, 백분위 기반 점수 모델을 위한 테이블을 생성하는 프로젝트.

## 아키텍처

```
┌──────────────────────────────────────────────────────┐
│  데이터 파이프라인                                       │
│                                                      │
│  EventBridge Schedule (주 1회)                        │
│       │                                              │
│       ▼                                              │
│  Lambda (Python 3.14)                                │
│   ├→ YouTube Data API v3 수집 (카테고리별 인기 채널)      │
│   ├→ 백분위 테이블 계산                                  │
│   └→ S3 저장                                          │
│       ├ latest.json           ← crit-server가 읽음    │
│       ├ percentiles/{날짜}.json ← 이력 보관             │
│       └ summaries/{날짜}.json   ← 카테고리 요약 통계      │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  crit-server (Spring Boot)                           │
│                                                      │
│  요청 → S3에서 latest.json 읽기 → 백분위 조회 → 점수 반환  │
└──────────────────────────────────────────────────────┘
```

### AWS 리소스

| 서비스 | 리소스 | 용도 |
|---|---|---|
| Lambda | `youtube-data-collector` | 수집 + 백분위 계산 |
| EventBridge | Schedule (주 1회) | Lambda 트리거 |
| S3 | `pj-kmucd1-08-s3-data-collector` | 백분위 테이블 저장 |

## 점수 모델

### 설계 원리

**"같은 조건의 영상들 중에서 이 영상이 상위 몇 %인가"**

비교 그룹 = `구독자 구간` × `숏폼/롱폼` × `카테고리`

### 점수 공식

```
점수 = VPS 백분위 × 0.40 + 채널평균대비 백분위 × 0.40 + 일평균조회수 백분위 × 0.20
```

| 지표 | 가중치 | 설명 |
|---|---|---|
| views_per_sub (VPS) | 40% | 구독자 대비 조회수 |
| vs_channel_avg | 40% | 채널 평소 성적 대비 상대 성과 |
| daily_views | 20% | 업로드 후 경과일 대비 조회수 (시간 보정) |

### 구독자 구간

| 구간 | 범위 |
|---|---|
| S | 0 ~ 50,000 |
| M | 50,000 ~ 200,000 |
| L | 200,000 ~ 500,000 |
| XL | 500,000+ |

숏폼/롱폼 기준: 영상 길이 60초

### latest.json 구조

```json
{
  "collected_at": "2026-05-04T04:07:03+00:00",
  "total_channels": 105,
  "total_videos": 5200,
  "groups": 14,
  "tables": {
    "L_0_28": {
      "sample_count": 320,
      "vps": [0.001, 0.003, ..., 9.5],
      "engagement": [0.001, 0.002, ..., 0.08],
      "like_rate": [0.001, 0.002, ..., 0.05],
      "vs_channel_avg": [0.01, ..., 47.2],
      "daily_views": [0.5, ..., 47583713.6]
    }
  }
}
```

키 형식: `{구독자구간}_{숏폼여부}_{카테고리ID}` (예: `L_0_28` = 구독자 200K~500K, 롱폼, SciTech)

## 수집 전략

### API 쿼터 효율

YouTube Data API의 하루 쿼터는 10,000유닛. `search.list`(100유닛/회) 대신 `videos.list?chart=mostPopular`(1유닛/회)를 사용.

| API | 비용 | 용도 |
|---|---|---|
| `videos.list(chart=mostPopular)` | 1유닛 | 카테고리별 인기 영상에서 채널 ID 추출 |
| `channels.list` | 1유닛 | 채널 메타 정보 |
| `playlistItems.list` | 1유닛 | 채널의 최근 영상 ID 목록 |
| `videos.list(id=...)` | 1유닛 | 영상 상세 정보 50개 배치 조회 |

### 수집 비용

| 범위 | 쿼터 | 소요 시간 |
|---|---|---|
| 1개 카테고리 | ~319유닛 | ~78초 |
| 14개 카테고리 전체 | ~5,100유닛 (51%) | ~15분 |

## Lambda 배포

### 배포 파일

Lambda에 올릴 파일:
- `lambda_function.py`
- `youtube_api.py`

### 환경변수

| 키 | 값 |
|---|---|
| `YOUTUBE_API_KEY` | YouTube Data API v3 키 |
| `S3_BUCKET` | `pj-kmucd1-08-s3-data-collector` |

### Lambda 설정

| 항목 | 값 |
|---|---|
| 런타임 | Python 3.14 |
| 핸들러 | `lambda_function.lambda_handler` |
| 타임아웃 | 15분 |
| 메모리 | 512MB |

### EventBridge Schedule (주 1회, 3분할)

| 이름 | cron | Input |
|------|------|------|
| weekly-collect-1 | `cron(0 3 ? * MON *)` | `{"categories":["1","2","10","15","17"]}` |
| weekly-collect-2 | `cron(5 3 ? * MON *)` | `{"categories":["19","20","22","23","24"]}` |
| weekly-collect-3 | `cron(10 3 ? * MON *)` | `{"categories":["25","26","27","28"]}` |

### S3 저장 구조

```
pj-kmucd1-08-s3-data-collector/
├── latest.json              ← crit-server가 읽는 최신 백분위
├── percentiles/
│   └── {YYYYMMDD}.json      ← 이력
└── summaries/
    └── {YYYYMMDD}.json      ← 카테고리별 요약 통계
```

## 로컬 개발

### 환경 설정

```bash
cp .env.example .env
# .env에 YOUTUBE_API_KEY 설정
pip install -r requirements.txt
```

### 단일 채널 수집

```bash
python3 collect.py "https://www.youtube.com/@codingapple"
python3 collect.py "@channelhandle"
```

### 전체 카테고리 수집

```bash
python3 collect_all.py          # 전체
python3 collect_all.py 20 28    # 특정 카테고리만
```

## 프로젝트 구조

```
crit-data-collector/
├── lambda_function.py      # Lambda 함수 (수집 → 백분위 계산 → S3 저장)
├── youtube_api.py          # YouTube API 공통 모듈
├── collect.py              # 로컬 수집 (단일 채널)
├── collect_all.py          # 로컬 전체 카테고리 수집
├── requirements.txt        # Python 의존성
└── .gitignore
```

## 카테고리 ID 참조

| ID | 카테고리 | ID | 카테고리 |
|---|---|---|---|
| 1 | Film & Animation | 22 | People & Blogs |
| 2 | Autos & Vehicles | 23 | Comedy |
| 10 | Music | 24 | Entertainment |
| 15 | Pets & Animals | 25 | News & Politics |
| 17 | Sports | 26 | Howto & Style |
| 19 | Travel & Events | 27 | Education |
| 20 | Gaming | 28 | Science & Technology |
