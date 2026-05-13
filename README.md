# YouTube Data Collector & Scoring Model

YouTube Data API v3를 활용하여 카테고리별 채널/영상 데이터를 수집하고, 수집된 데이터를 기반으로 영상 성과 점수 모델을 도출하는 프로젝트.

## 배경

기존 CRIT 서버의 영상 점수 알고리즘은 AI가 임의로 설계한 공식을 사용했으며, 다음과 같은 문제가 있었다:

- 가중치에 데이터 근거가 없음
- 대부분의 영상이 100점에 수렴하여 차별화 불가
- 채널 규모, 영상 형식(숏폼/롱폼), 카테고리 차이를 반영하지 못함

이를 해결하기 위해 **실제 유튜브 데이터를 대량 수집**하고, 통계 분석을 통해 **데이터 기반 점수 모델**을 설계했다.

## 아키텍처

```
┌──────────────────────────────────────────────────────┐
│  데이터 파이프라인                                       │
│                                                      │
│  API Gateway (HTTP API)                              │
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
| API Gateway | HTTP API `/collect` | Lambda 트리거 |
| S3 | `pj-kmucd1-08-s3-data-collector` | 백분위 테이블 저장 |
| RDS | `pj-kmucd1-08-db` (crit DB) | crit-server 기존 DB |

### 설계 결정

- **Lambda + S3 구조를 선택한 이유**: Lambda에서 RDS에 직접 접근하려면 같은 VPC에 배치해야 하고, 외부 API(YouTube) 호출을 위해 NAT Gateway가 필요하여 비용이 발생한다. S3는 퍼블릭 서비스이므로 VPC 없이 접근 가능하다.
- **S3에 저장하는 데이터는 백분위 테이블(~90KB)**이며, 영상 원본 데이터(~33MB)는 저장하지 않는다. Lambda 메모리 안에서 수집→계산→결과만 저장.
- **날짜별 이력 보관**: 주기적 수집 시 트렌드 변화를 추적할 수 있다.

## 수집 전략

### API 쿼터 효율

YouTube Data API의 하루 쿼터는 10,000유닛이다. `search.list`(100유닛/회) 대신 `videos.list?chart=mostPopular`(1유닛/회)를 사용하여 쿼터 효율을 극대화했다.

| API | 비용 | 용도 |
|---|---|---|
| `videos.list(chart=mostPopular)` | 1유닛 | 카테고리별 인기 영상에서 채널 ID 추출 |
| `channels.list` | 1유닛 | 채널 메타 정보 (구독자 수, 총 조회수 등) |
| `playlistItems.list` | 1유닛 | 채널의 최근 영상 ID 목록 (최대 50개) |
| `videos.list(id=...)` | 1유닛 | 영상 상세 정보 50개 배치 조회 |

**채널 1개 수집 = 3유닛** (channels + playlistItems + videos)

### 채널 발견 방식

```
videos.list(chart=mostPopular, videoCategoryId=X, regionCode=KR, maxResults=50)
→ 인기 영상 최대 200개 (4페이지) → channelId 추출 → 중복 제거
→ 카테고리당 유니크 채널 60~200개 확보
```

`search.list` 방식 대비 **약 4배 저렴**하다.

### 수집 비용

| 범위 | 쿼터 | 소요 시간 |
|---|---|---|
| 1개 카테고리 (Gaming) | ~319유닛 | ~78초 |
| 12개 카테고리 전체 | ~5,100유닛 (51%) | ~15분 |

## 수집 결과 (2026-05-01 기준)

총 **82,327개 영상**, **1,309개 채널**, 12개 카테고리.

| 카테고리 | ID | 채널 | 영상 |
|---|---|---|---|
| Film & Animation | 1 | 200 | 9,615 |
| Autos & Vehicles | 2 | 199 | 9,653 |
| Music | 10 | 21 | 873 |
| Pets & Animals | 15 | 200 | 9,679 |
| Sports | 17 | 200 | 9,933 |
| Gaming | 20 | 101 | 5,042 |
| People & Blogs | 22 | 11 | 550 |
| Comedy | 23 | 200 | 9,841 |
| Entertainment | 24 | 200 | 9,760 |
| News & Politics | 25 | 96 | 4,800 |
| Howto & Style | 26 | 200 | 9,641 |
| Science & Technology | 28 | 60 | 3,000 |

- Travel & Events(19), Education(27)은 한국 리전 mostPopular에서 결과 0
- Music, People & Blogs는 소수 대형 채널에 인기 영상이 집중되어 채널 수가 적음

## 데이터 분석

### 상관관계 분석

`views_per_sub`(성공 지표)와 각 변수의 상관계수:

| 변수 | 상관계수 | 해석 |
|---|---|---|
| `log10(views)` | **+0.77** | 조회수가 높을수록 VPS 높음 |
| `log10(subs)` | **-0.62** | 구독자가 적을수록 VPS 높음 → 구간별 분리 필수 |
| `is_short` | **+0.31** | 숏폼이 VPS 높음 → 숏폼/롱폼 분리 필수 |
| `engagement_rate` | **-0.24** | 바이럴 영상은 참여율 낮음 (가벼운 시청) |
| `duration_sec` | -0.15 | 긴 영상일수록 VPS 낮음 |

### 숏폼 vs 롱폼

| 지표 | 숏폼 (56,593개) | 롱폼 (25,734개) | 배율 |
|---|---|---|---|
| 평균 VPS | 1.08x | 0.56x | **1.9x** |
| 평균 참여율 | 11.74% | 1.36% | **8.6x** |

숏폼과 롱폼은 성격이 완전히 다르므로 **분리 비교가 필수**다.

### 구독자 구간별 VPS 백분위

| 구독자 구간 | 10% | 50% (중앙값) | 90% |
|---|---|---|---|
| 0~50K | 0.47x | 4.00x | 75.89x |
| 50K~200K | 0.12x | 1.02x | 17.15x |
| 200K~500K | 0.04x | 0.37x | 3.37x |
| 500K~1M | 0.02x | 0.28x | 2.32x |
| 1M+ | 0.00x | 0.07x | 0.94x |

### 카테고리별 VPS 중앙값

| 카테고리 | VPS 중앙값 | 카테고리 | VPS 중앙값 |
|---|---|---|---|
| Music | 4.80x | Howto & Style | 0.96x |
| Film & Animation | 3.21x | Auto & Vehicles | 0.42x |
| People & Blogs | 1.84x | Science & Technology | 0.39x |
| Sports | 1.54x | Gaming | 0.35x |
| Entertainment | 1.16x | News & Politics | 0.02x |

카테고리 간 VPS 차이가 최대 240배. **카테고리별 분리 비교 필수**.

## 점수 모델

### 설계 원리

**"같은 조건의 영상들 중에서 이 영상이 상위 몇 %인가"**

비교 그룹 = `구독자 구간` × `숏폼/롱폼` × `카테고리`

각 그룹 내에서 백분위를 계산하여 0~100점을 부여한다.

### 점수 공식

```
점수 = VPS 백분위 × 0.40 + 채널평균대비 백분위 × 0.40 + 일평균조회수 백분위 × 0.20
```

| 지표 | 가중치 | 근거 |
|---|---|---|
| views_per_sub (VPS) 백분위 | 40% | 구독자 대비 조회수, 핵심 성과 지표 |
| vs_channel_avg 백분위 | 40% | 채널 평소 성적 대비 상대 성과, 채널 규모 독립적 |
| daily_views 백분위 | 20% | 시간 경과 보정된 절대 성과 |

> **변경 이유**: 기존 공식(VPS×60 + 참여율×25 + 좋아요율×15)은 VPS와 참여율이 음의 상관관계(-0.24)를 가져, 바이럴 영상(VPS 높음, 참여율 낮음)의 점수가 부당하게 깎이는 문제가 있었다. 새 공식은 서로 양의 상관관계를 가진 지표들로 구성하여 이 문제를 해결한다.

### 구독자 구간

| 구간 | 범위 |
|---|---|
| S | 0 ~ 50,000 |
| M | 50,000 ~ 200,000 |
| L | 200,000 ~ 500,000 |
| XL | 500,000+ |

### 백분위 테이블 구조

S3 `latest.json`에 저장되는 형식:

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
      "like_rate": [0.001, 0.002, ..., 0.05]
    }
  }
}
```

키 형식: `{구독자구간}_{숏폼여부}_{카테고리ID}` (예: `L_0_28` = 구독자 200K~500K, 롱폼, SciTech)

### 점수 분포 (검증)

82,327개 영상에 점수를 부여한 결과:

```
 0~20점:  8.6%  ██████████████
20~40점: 23.6%  ██████████████████████████████████████
40~60점: 32.3%  █████████████████████████████████████████████████████
60~80점: 27.6%  █████████████████████████████████████████████
80~100점:  7.9%  █████████████
```

정규분포에 가까운 분포. 기존 알고리즘의 "100점 수렴" 문제 해결.

### 점수 검증 — 점수와 실제 성과의 관계

| 점수 구간 | 평균 VPS | 평균 조회수 |
|---|---|---|
| 0~20점 | 0.30x | 26,381 |
| 20~40점 | 0.99x | 65,719 |
| 40~60점 | 6.76x | 289,570 |
| 60~80점 | 106.4x | 1,441,870 |
| 80~100점 | 65.7x | 2,350,594 |

점수가 높을수록 실제 성과가 단조 증가하여 모델의 유효성이 검증됨.

## Lambda 배포

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

### API Gateway

| 항목 | 값 |
|---|---|
| 타입 | HTTP API |
| 메서드 | POST |
| 경로 | `/collect` |

### 호출 방법

```bash
# 전체 카테고리 수집
curl -X POST https://{api-id}.execute-api.us-east-1.amazonaws.com/collect

# 특정 카테고리만
curl -X POST https://{api-id}.execute-api.us-east-1.amazonaws.com/collect \
  -d '{"categories": ["20", "28"]}'
```

### S3 저장 구조

```
pj-kmucd1-08-s3-data-collector/
├── latest.json              ← crit-server가 읽는 최신 백분위
├── percentiles/
│   ├── 20260501.json        ← 이력 (트렌드 변화 추적)
│   └── 20260504.json
└── summaries/
    ├── 20260501.json        ← 카테고리별 요약 통계
    └── 20260504.json
```

## 로컬 개발

### 환경 설정

```bash
cp .env.example .env
# .env에 YOUTUBE_API_KEY 설정
pip install requests python-dotenv
```

### 단일 채널 수집 (로컬)

```bash
python3 collect.py "https://www.youtube.com/@codingapple"
python3 collect.py "@channelhandle"
```

### 전체 카테고리 수집 (로컬)

```bash
python3 collect_all.py          # 전체
python3 collect_all.py 20 28    # 특정 카테고리만
```

### 카테고리 ID 참조

| ID | 카테고리 | ID | 카테고리 |
|---|---|---|---|
| 1 | Film & Animation | 22 | People & Blogs |
| 2 | Autos & Vehicles | 23 | Comedy |
| 10 | Music | 24 | Entertainment |
| 15 | Pets & Animals | 25 | News & Politics |
| 17 | Sports | 26 | Howto & Style |
| 19 | Travel & Events | 27 | Education |
| 20 | Gaming | 28 | Science & Technology |

## 프로젝트 구조

```
youtube-data-collector/
├── youtube_api.py          # YouTube API 공통 모듈 (채널/영상 조회, 유틸)
├── lambda_function.py      # Lambda 함수 (수집 → 백분위 계산 → S3 저장)
├── collect.py              # 로컬 수집 모듈 (파생 지표 계산, CSV 저장)
├── collect_all.py          # 로컬 전체 카테고리 일괄 수집
├── train.py                # ML 점수 모델 학습 스크립트
├── feature_config.json     # 피처 설정 (수치/범주형 피처 정의)
├── channels.json           # 수동 채널 목록 (선택)
├── requirements.txt        # Python 의존성
├── src/                    # ML 모듈
│   ├── feature_engineer.py # 피처 엔지니어링 (백분위 조회, 스케일링, One-Hot)
│   ├── label_generator.py  # 레이블 생성 (Comparison Group 내 순위 기반)
│   ├── model_trainer.py    # 다중 모델 학습 및 Champion 선정
│   ├── model_evaluator.py  # 모델 평가 (MAE, RMSE, Spearman, 단조 증가)
│   ├── model_server.py     # 모델 추론 서빙 (폴백 포함)
│   └── training_pipeline.py # 재학습 파이프라인 (성능 하락 감지, 롤백)
├── models/                 # 학습된 모델 아티팩트
│   ├── champion_model.joblib
│   ├── champion_meta.json
│   ├── scaler_params.json
│   ├── percentile_tables.json
│   ├── selection_report.json
│   └── versions/           # 모델 버전 이력
├── tests/                  # 단위/통합 테스트
├── data/                   # 로컬 수집 CSV 데이터 (git 제외)
├── .env                    # 환경변수 (git 제외)
└── .gitignore
```

## 향후 과제

- [ ] crit-server에서 S3 백분위 테이블 읽어서 점수 계산 서비스 구현
- [ ] EventBridge 스케줄로 주기적 자동 수집 (3~7일 간격)
- [ ] 시간 가중치 추가 (최신 영상에 보너스)
- [ ] 가중치 튜닝 (교차 검증)
- [ ] Travel & Events, Education 카테고리 보완
- [ ] 백분위 이력 기반 트렌드 변화 분석 API
