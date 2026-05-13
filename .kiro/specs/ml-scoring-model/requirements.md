# Requirements Document

## Introduction

기존 YouTube 영상 점수 모델(VPS 백분위 × 0.60 + 참여율 백분위 × 0.25 + 좋아요율 백분위 × 0.15)의 수동 가중치를 ML/DL 기반으로 대체하여, 데이터 기반의 견고한(robust) 점수 모델을 구축한다. 현재 82,327개 영상, 1,309개 채널, 12개 카테고리 데이터를 활용하며, 기존 Lambda → S3 → crit-server 아키텍처와 호환되는 형태로 모델을 서빙한다.

## Glossary

- **Scoring_Model**: ML/DL 기반으로 영상의 성과 점수(0~100)를 산출하는 모델
- **Feature_Engineer**: 원시 영상/채널 데이터에서 모델 입력 피처를 생성하는 모듈
- **Model_Trainer**: 학습 데이터를 기반으로 Scoring_Model을 학습시키는 모듈
- **Model_Evaluator**: 학습된 모델의 성능을 검증하고 기존 모델과 비교하는 모듈
- **Model_Server**: 학습된 모델을 로드하여 점수 추론 요청에 응답하는 서빙 모듈
- **Comparison_Group**: 구독자 구간(S/M/L/XL) × 숏폼/롱폼 × 카테고리로 정의되는 비교 단위
- **VPS**: Views Per Subscriber. 구독자 대비 조회수 비율
- **Engagement_Rate**: (좋아요 + 댓글) / 조회수
- **Like_Rate**: 좋아요 / 조회수
- **Percentile_Table**: 각 Comparison_Group 내 지표별 백분위 분포 테이블 (S3 latest.json에 저장)
- **Training_Pipeline**: 데이터 수집 → 피처 엔지니어링 → 모델 학습 → 평가 → 배포의 전체 흐름
- **Baseline_Model**: 현재 수동 가중치 기반 선형 결합 모델 (60/25/15)
- **Champion_Model**: 초기 모델 선정 단계에서 평가 메트릭 기준 최고 성능으로 선정된 모델. 이후 재학습은 이 아키텍처로만 수행한다
- **Label**: 모델 학습을 위한 타겟 변수 (자기지도 학습 시 순위 기반 레이블 또는 기존 백분위 점수)

## Requirements

### Requirement 1: 피처 엔지니어링

**User Story:** As a 데이터 엔지니어, I want 원시 영상 데이터에서 ML 모델에 적합한 피처를 자동으로 생성하고 싶다, so that 모델이 다양한 신호를 활용하여 더 정확한 점수를 산출할 수 있다.

#### Acceptance Criteria

1. WHEN 영상 데이터가 입력되면, THE Feature_Engineer SHALL VPS, Engagement_Rate, Like_Rate의 원시값과 해당 Comparison_Group 내 백분위 값을 피처로 생성한다
2. WHEN 영상 데이터가 입력되면, THE Feature_Engineer SHALL 영상 길이(duration_sec), 업로드 후 경과일(days_since_upload), 구독자 수(subscriber_count)를 수치 피처로 포함한다
3. WHEN 영상 데이터가 입력되면, THE Feature_Engineer SHALL 구독자 구간(S/M/L/XL), 숏폼/롱폼 여부, 카테고리 ID를 범주형 피처로 인코딩한다
4. WHEN 수치 피처가 생성되면, THE Feature_Engineer SHALL 로그 변환(log1p) 또는 표준화(standardization)를 적용하여 스케일을 정규화한다
5. THE Feature_Engineer SHALL 피처 생성 로직을 재현 가능한 파이프라인으로 구현하여, 학습 시점과 추론 시점에 동일한 변환을 보장한다

### Requirement 2: 학습 레이블 생성

**User Story:** As a ML 엔지니어, I want 지도학습에 사용할 레이블을 데이터 기반으로 자동 생성하고 싶다, so that 수동 라벨링 없이 모델을 학습시킬 수 있다.

#### Acceptance Criteria

1. THE Model_Trainer SHALL 각 Comparison_Group 내에서 VPS 기준 순위를 산출하고, 이를 0~100 범위의 연속 점수로 변환하여 학습 레이블로 사용한다
2. WHEN 학습 레이블이 생성되면, THE Model_Trainer SHALL 레이블 분포가 균등(uniform)에 가까운지 검증하고, 특정 구간에 80% 이상 집중되면 경고를 출력한다
3. WHERE 대안 레이블 전략이 설정된 경우, THE Model_Trainer SHALL 다중 지표 가중 순위(VPS, Engagement_Rate, Like_Rate의 학습된 가중치 기반)를 레이블로 사용한다

### Requirement 3: 모델 학습

**User Story:** As a ML 엔지니어, I want 다양한 ML/DL 모델을 학습하고 비교하고 싶다, so that 최적의 모델 구조와 하이퍼파라미터를 데이터 기반으로 선택할 수 있다.

#### Acceptance Criteria

1. THE Model_Trainer SHALL 초기 모델 선정(Model Selection) 단계에서 다음 후보를 모두 학습하고 비교한다: (a) 선형 회귀 기반 가중치 최적화, (b) Random Forest, (c) Gradient Boosting (XGBoost 또는 LightGBM), (d) 상위 모델들의 앙상블(Stacking 또는 Weighted Average)
2. WHERE 딥러닝 옵션이 활성화된 경우, THE Model_Trainer SHALL MLP(Multi-Layer Perceptron) 모델을 초기 선정 후보에 추가로 포함한다
3. WHEN 초기 모델 선정이 완료되면, THE Model_Trainer SHALL 평가 메트릭 기준 최고 성능 모델(개별 또는 앙상블)을 최종 모델(Champion Model)로 선정하고, 이후 재학습 시에는 Champion Model 아키텍처만 학습한다
4. WHEN 모델 학습 시, THE Model_Trainer SHALL 데이터를 학습(70%) / 검증(15%) / 테스트(15%)로 분할하되, 같은 채널의 영상이 서로 다른 분할에 포함되지 않도록 채널 단위로 분할한다
5. WHEN 모델 학습 시, THE Model_Trainer SHALL Comparison_Group별로 최소 20개 이상의 샘플이 있는 그룹만 학습에 포함한다
6. THE Model_Trainer SHALL 학습된 모델의 가중치, 하이퍼파라미터, 학습 메트릭, 선정된 Champion Model 정보를 JSON 형식으로 저장한다

### Requirement 4: 모델 평가 및 비교

**User Story:** As a ML 엔지니어, I want ML 모델의 성능을 Baseline_Model과 정량적으로 비교하고 싶다, so that 새 모델이 실제로 개선되었는지 객관적으로 판단할 수 있다.

#### Acceptance Criteria

1. THE Model_Evaluator SHALL 테스트 세트에서 MAE(Mean Absolute Error), RMSE, Spearman 순위 상관계수를 산출한다
2. THE Model_Evaluator SHALL Baseline_Model(수동 가중치 60/25/15)과 동일한 테스트 세트에서 동일 메트릭을 산출하여 비교 리포트를 생성한다
3. WHEN 모델 평가가 완료되면, THE Model_Evaluator SHALL 점수 분포 히스토그램을 생성하여 정규분포에 가까운지 검증한다
4. WHEN 모델 평가가 완료되면, THE Model_Evaluator SHALL 점수 구간별(0~20, 20~40, 40~60, 60~80, 80~100) 평균 VPS를 산출하여 단조 증가 여부를 검증한다
5. IF 새 모델의 Spearman 순위 상관계수가 Baseline_Model보다 낮으면, THEN THE Model_Evaluator SHALL 경고를 출력하고 배포를 차단한다

### Requirement 5: 모델 서빙 및 배포

**User Story:** As a 백엔드 개발자, I want 학습된 ML 모델을 기존 crit-server 아키텍처와 호환되는 형태로 서빙하고 싶다, so that 기존 시스템을 최소한으로 변경하면서 ML 모델을 적용할 수 있다.

#### Acceptance Criteria

1. THE Model_Server SHALL 학습된 모델 아티팩트를 S3에 저장하고, crit-server가 읽을 수 있는 형태로 제공한다
2. WHEN 영상 점수 요청이 들어오면, THE Model_Server SHALL 영상의 원시 데이터(조회수, 좋아요, 댓글, 구독자수, 영상길이, 카테고리, 숏폼여부)를 입력받아 0~100 범위의 점수를 반환한다
3. THE Model_Server SHALL 추론 시 Percentile_Table을 참조하여 해당 Comparison_Group 내 백분위 피처를 실시간으로 계산한다
4. WHEN 모델 추론 시, THE Model_Server SHALL 단일 영상 점수 계산을 200ms 이내에 완료한다
5. IF 모델 로드에 실패하면, THEN THE Model_Server SHALL Baseline_Model(수동 가중치)로 폴백하여 점수를 반환한다

### Requirement 6: 모델 재학습 파이프라인

**User Story:** As a ML 엔지니어, I want 새로운 데이터가 수집될 때 모델을 자동으로 재학습하고 싶다, so that 모델이 최신 트렌드를 반영하여 점수의 정확도를 유지할 수 있다.

#### Acceptance Criteria

1. WHEN 새로운 수집 데이터가 S3에 저장되면, THE Training_Pipeline SHALL 기존 데이터와 병합하여 Champion Model 아키텍처로만 재학습을 트리거한다
2. WHEN 재학습이 완료되면, THE Training_Pipeline SHALL 새 모델과 기존 배포 모델의 성능을 비교하고, 새 모델이 우수할 경우에만 배포한다
3. THE Training_Pipeline SHALL 모델 버전을 관리하여, 이전 버전으로 롤백할 수 있도록 한다
4. IF 재학습 중 오류가 발생하면, THEN THE Training_Pipeline SHALL 기존 모델을 유지하고 오류 로그를 기록한다
5. WHERE Champion Model의 성능이 3회 연속 하락하면, THE Training_Pipeline SHALL 전체 모델 재선정(초기 선정 프로세스 재실행)을 권고하는 알림을 출력한다

### Requirement 7: 견고성(Robustness) 보장

**User Story:** As a 서비스 운영자, I want 점수 모델이 이상치(outlier)와 데이터 편향에 강건하게 동작하길 원한다, so that 극단적인 영상 데이터에도 안정적인 점수를 제공할 수 있다.

#### Acceptance Criteria

1. WHEN 입력 피처에 극단적 이상치(해당 Comparison_Group 내 상위/하위 1% 밖)가 포함되면, THE Scoring_Model SHALL 클리핑(clipping) 또는 윈저화(winsorization)를 적용하여 점수 왜곡을 방지한다
2. THE Scoring_Model SHALL 출력 점수를 0~100 범위로 제한하며, 범위를 벗어나는 예측값은 경계값으로 클리핑한다
3. WHEN Comparison_Group의 샘플 수가 20개 미만이면, THE Scoring_Model SHALL 상위 그룹(구독자 구간만 다른 그룹)의 모델을 사용하여 점수를 산출한다
4. THE Scoring_Model SHALL 교차 검증(5-fold) 결과에서 fold 간 성능 편차(MAE 기준)가 평균의 20% 이내임을 보장한다
5. WHEN 새로운 카테고리 또는 구독자 구간의 데이터가 추가되면, THE Scoring_Model SHALL 기존 그룹의 점수에 영향을 주지 않고 새 그룹을 독립적으로 처리한다


## References

- 프로젝트 README.md — 기존 점수 모델 공식, 데이터 분석 결과, 아키텍처, 수집 전략 등 전체 컨텍스트
- lambda_function.py — 현재 백분위 계산 및 S3 저장 로직
- youtube_api.py — YouTube API 수집 모듈 구조
- 기존 데이터 분석 (README 내 상관관계 분석, 숏폼/롱폼 비교, 구독자 구간별 VPS 백분위) — 피처 선정 및 Comparison Group 설계 근거
