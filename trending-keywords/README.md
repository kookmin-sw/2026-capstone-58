# YouTube 실시간 키워드 TOP 100

YouTube Data API v3를 활용하여 한국 인기 급상승 동영상에서 트렌드 키워드를 추출하는 AWS Lambda 서비스입니다.

## 아키텍처

```
API Gateway (HTTP GET /words)
    ↓
AWS Lambda (Python 3.14)
    ├── YouTube Data API → 인기 동영상 200개 수집
    ├── kiwipiepy 형태소 분석 → 명사 키워드 추출
    ├── 조회수 가중치 기반 TOP 100 산출
    └── S3에 words.json 저장 + JSON 응답 반환
```

## API 엔드포인트

```
GET https://t31dwqr9m5.execute-api.us-east-1.amazonaws.com/words
```

### 응답 형식

```json
[
  { "text": "게임", "value": 4422776 },
  { "text": "리그 오브 레전드", "value": 3071670 },
  { "text": "에스파", "value": 1940025 },
  ...
]
```

- `text`: 키워드
- `value`: 조회수 가중치 (해당 키워드가 등장한 동영상들의 조회수 합계)

## 키워드 추출 방식

1. YouTube Data API `videos.list(chart=mostPopular, regionCode=KR)`로 인기 동영상 최대 200개 수집
2. 각 동영상의 **제목 + 설명 + 태그**에서 텍스트 추출
3. **kiwipiepy** 형태소 분석기로 명사(NNG, NNP, NNB) 추출
4. 유튜브 보일러플레이트 불용어 필터링 (구독, 채널, 광고 등)
5. 키워드별로 등장한 동영상의 **조회수를 합산**하여 가중치 산출
6. 가중치 상위 100개를 반환

## AWS 리소스

| 리소스 | 이름 | 리전 |
|--------|------|------|
| Lambda | `pj-kmucd1-08-youtube-trending` | us-east-1 |
| S3 | `pj-kmucd1-08-s3-trending-keywords` | us-east-1 |
| API Gateway | `pj-kmucd1-08-youtube-trending-api` | us-east-1 |

### Lambda 환경 변수

| 변수 | 값 |
|------|-----|
| `YOUTUBE_API_KEY` | YouTube Data API v3 키 |
| `S3_BUCKET` | `pj-kmucd1-08-s3-trending-keywords` |
| `REGION_CODE` | `KR` (기본값) |
| `S3_KEY` | `words.json` (기본값) |

### Lambda 설정

- 런타임: Python 3.14
- 메모리: 1024MB
- 제한 시간: 120초
- IAM 역할: `SafeRole-pj-kmucd1-08`

## 프로젝트 구조

```
youtube-trending-keywords/
├── lambda_function.py   # Lambda 핸들러
├── Dockerfile           # 컨테이너 이미지 빌드용
├── requirements.txt     # kiwipiepy==0.23.1
├── deploy.sh            # 배포 스크립트
└── README.md
```

## 배포 방법

### 1. 패키지 빌드 (Docker 필요)

```bash
# Lambda 런타임과 동일한 환경에서 빌드
sudo docker run --rm --entrypoint "" -v "$PWD":/out public.ecr.aws/lambda/python:3.14 \
  bash -c "pip install kiwipiepy==0.23.1 -t /out/package --quiet"

sudo cp lambda_function.py package/
cd package && sudo zip -r -q ../lambda-deploy.zip . && cd ..
```

### 2. S3에 업로드 후 Lambda 코드 업데이트

```bash
aws s3 cp lambda-deploy.zip s3://pj-kmucd1-08-s3-trending-keywords/lambda-deploy.zip --region us-east-1
```

Lambda 콘솔 → 코드 탭 → S3 위치에서 업로드:
```
https://pj-kmucd1-08-s3-trending-keywords.s3.us-east-1.amazonaws.com/lambda-deploy.zip
```

## 사용 예시

### crit-server에서 1시간마다 호출

백엔드에서 스케줄러로 API를 주기적으로 호출하면 S3의 `words.json`이 갱신됩니다.

### S3에서 직접 읽기

```
s3://pj-kmucd1-08-s3-trending-keywords/words.json
```

## API 할당량

- `videos.list`: 호출당 1 unit (snippet + statistics)
- 1회 실행: 4 API 호출 = 4 units
- YouTube Data API 일일 기본 할당량: 10,000 units
- 1시간 간격 실행 시: 하루 96 units 소모
