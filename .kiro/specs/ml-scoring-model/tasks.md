# Implementation Plan: ML Scoring Model

## Overview

기존 수동 가중치 기반 점수 모델(60/25/15)을 ML 기반으로 대체하는 구현 계획. Python으로 6개 핵심 모듈(Feature Engineer, Label Generator, Model Trainer, Model Evaluator, Model Server, Training Pipeline)을 구현하고, Hypothesis 기반 Property-Based Testing으로 17개 정확성 속성을 검증한다.

## Tasks

- [x] 1. 프로젝트 구조 및 공통 설정
  - [x] 1.1 프로젝트 디렉토리 구조 생성 및 의존성 설정
    - `src/` 디렉토리 하위에 모듈 파일 생성 (`feature_engineer.py`, `label_generator.py`, `model_trainer.py`, `model_evaluator.py`, `model_server.py`, `training_pipeline.py`)
    - `tests/` 디렉토리 생성 및 `conftest.py` 작성 (공통 fixture 정의)
    - `requirements.txt` 작성: numpy, pandas, scikit-learn, xgboost, lightgbm, hypothesis, pytest, moto, joblib, scipy, boto3
    - `feature_config.json`, `scaler_params.json` 초기 스키마 파일 생성
    - _Requirements: 1.5, 3.6_

- [x] 2. Feature Engineer 구현
  - [x] 2.1 FeatureEngineer 클래스 핵심 구현
    - `FeatureEngineer.__init__`: 백분위 테이블 및 스케일러 파라미터 로드
    - `transform`: 단일 영상 → 27차원 피처 벡터 변환 (수치 9개 + 범주형 One-Hot 18개)
    - `transform_batch`: 영상 리스트 → DataFrame 변환
    - VPS, Engagement Rate, Like Rate 원시값 및 백분위 계산
    - duration_sec, days_since_upload, subscriber_count 수치 피처 포함
    - sub_tier(S/M/L/XL) One-Hot, is_short Binary, category_id One-Hot 인코딩
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 2.2 스케일링 및 이상치 처리 구현
    - `fit_scalers`: 학습 데이터 기반 스케일러 파라미터 fit 및 JSON 저장
    - 수치 피처에 log1p 변환 적용
    - `clip_outliers`: Comparison Group 내 상위/하위 1% 윈저화(winsorization) 적용
    - 학습/추론 동일 변환 보장 (scaler_params.json 기반)
    - _Requirements: 1.4, 1.5, 7.1_

  - [ ]* 2.3 Property 1 테스트: 피처 완전성 (Feature Completeness)
    - **Property 1: 피처 완전성**
    - Hypothesis로 유효한 영상 데이터를 생성하여 transform 결과가 항상 27차원이고 모든 필수 피처를 포함하는지 검증
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [ ]* 2.4 Property 2 테스트: 수치 변환 단조 증가 (Numeric Transform Monotonicity)
    - **Property 2: 수치 변환 단조 증가**
    - 임의의 두 양수 a < b에 대해 log1p(a) < log1p(b) 검증
    - **Validates: Requirements 1.4**

  - [ ]* 2.5 Property 3 테스트: 피처 변환 일관성 (Feature Transform Consistency)
    - **Property 3: 피처 변환 일관성**
    - transform(single) == transform_batch([single])[0] 및 반복 호출 동일 결과 검증
    - **Validates: Requirements 1.5**

  - [ ]* 2.6 Property 14 테스트: 이상치 클리핑 범위 보장 (Outlier Clipping Range Guarantee)
    - **Property 14: 이상치 클리핑 범위 보장**
    - clip_outliers 적용 후 모든 값이 [1%, 99%] 경계 내에 있는지 검증
    - **Validates: Requirements 7.1**

- [x] 3. Label Generator 구현
  - [x] 3.1 LabelGenerator 클래스 구현
    - `generate_labels`: Comparison Group별 VPS 순위 산출 → percent_rank × 100으로 0~100 연속 점수 변환
    - `validate_distribution`: 레이블 분포 균등성 검증, 특정 구간 80% 이상 집중 시 경고 출력
    - 대안 레이블 전략 (다중 지표 가중 순위) 지원
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 3.2 Property 4 테스트: 레이블 범위 및 순서 보존 (Label Range and Order Preservation)
    - **Property 4: 레이블 범위 및 순서 보존**
    - 생성된 레이블이 [0, 100] 범위이고, VPS 높은 영상의 레이블 ≥ VPS 낮은 영상의 레이블 검증
    - **Validates: Requirements 2.1, 2.3**

  - [ ]* 3.3 Label Generator 단위 테스트
    - 레이블 분포 80% 집중 시 경고 발생 검증
    - 빈 그룹 및 단일 영상 그룹 엣지 케이스 테스트
    - _Requirements: 2.2_

- [x] 4. Checkpoint - 피처 및 레이블 모듈 검증
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Model Trainer 구현
  - [x] 5.1 데이터 분할 및 필터링 구현
    - `split_data`: 채널 단위 Train(70%)/Val(15%)/Test(15%) 분할 (같은 채널 영상이 서로 다른 분할에 포함되지 않도록)
    - Comparison Group별 최소 20개 샘플 필터링
    - `TrainingConfig` 데이터 클래스 정의
    - _Requirements: 3.4, 3.5_

  - [x] 5.2 후보 모델 학습 구현
    - `train_all_candidates`: Ridge Regression, RandomForest, XGBoost, LightGBM, Stacking Ensemble 학습
    - MLP 옵션 활성화 시 추가 포함
    - `select_champion`: 검증 세트 Spearman 기준 최고 성능 모델 선정
    - `retrain_champion`: Champion 아키텍처로만 재학습
    - 모델 메타데이터(가중치, 하이퍼파라미터, 메트릭) JSON 저장
    - _Requirements: 3.1, 3.2, 3.3, 3.6_

  - [ ]* 5.3 Property 5 테스트: Champion 선정 최적성 (Champion Selection Optimality)
    - **Property 5: Champion 선정 최적성**
    - select_champion 반환 모델의 Spearman ≥ 모든 다른 후보의 Spearman 검증
    - **Validates: Requirements 3.3**

  - [ ]* 5.4 Property 6 테스트: 채널 단위 분할 불변량 (Channel-Level Split Invariant)
    - **Property 6: 채널 단위 분할 불변량**
    - split_data 후 어떤 채널도 두 개 이상의 분할에 동시 존재하지 않는지 검증
    - **Validates: Requirements 3.4**

  - [ ]* 5.5 Property 7 테스트: 최소 샘플 필터링 (Minimum Sample Filtering)
    - **Property 7: 최소 샘플 필터링**
    - 학습에 포함된 모든 그룹의 샘플 수 ≥ 20 검증
    - **Validates: Requirements 3.5**

  - [ ]* 5.6 Property 8 테스트: 모델 메타데이터 직렬화 Round-Trip
    - **Property 8: 모델 메타데이터 직렬화 Round-Trip**
    - JSON 직렬화 → 역직렬화 후 원본과 동일 데이터 복원 검증
    - **Validates: Requirements 3.6**

- [x] 6. Model Evaluator 구현
  - [x] 6.1 ModelEvaluator 클래스 구현
    - `evaluate`: MAE, RMSE, Spearman 순위 상관계수 산출
    - 점수 분포 히스토그램 생성 및 정규분포 근사 검증
    - 점수 구간별(0~20, 20~40, 40~60, 60~80, 80~100) 평균 VPS 단조 증가 검증
    - `compare_with_baseline`: Baseline(60/25/15) 대비 비교 리포트 생성
    - `check_deployment_gate`: Spearman이 Baseline보다 낮으면 배포 차단
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 6.2 Property 9 테스트: 단조 증가 검증 정확성 (Monotonicity Check Correctness)
    - **Property 9: 단조 증가 검증 정확성**
    - 점수 구간별 평균 VPS가 실제 단조 증가이면 True, 아니면 False 반환 검증
    - **Validates: Requirements 4.4**

  - [ ]* 6.3 Property 10 테스트: 배포 게이트 정확성 (Deployment Gate Correctness)
    - **Property 10: 배포 게이트 정확성**
    - new_spearman < baseline_spearman → False, ≥ → True 검증
    - **Validates: Requirements 4.5, 6.2**

  - [ ]* 6.4 Property 16 테스트: 교차 검증 안정성 검증 (Cross-Validation Stability Check)
    - **Property 16: 교차 검증 안정성 검증**
    - 5-fold MAE 편차가 평균의 20% 이내이면 True, 초과이면 False 검증
    - **Validates: Requirements 7.4**

- [x] 7. Checkpoint - 학습 및 평가 모듈 검증
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Model Server 구현
  - [x] 8.1 ModelServer 클래스 구현
    - `__init__`: S3에서 모델 아티팩트(champion_model.joblib, scaler_params.json, feature_config.json) 로드
    - `predict`: 영상 원시 데이터 입력 → Feature Engineer로 피처 변환 → 모델 추론 → 0~100 클리핑 → 점수 반환
    - `_baseline_fallback`: 모델 로드 실패 시 수동 가중치(60/25/15) 기반 점수 계산
    - 백분위 테이블(latest.json) 참조하여 실시간 백분위 피처 계산
    - 추론 응답 형식: video_id, score, model_version, comparison_group, percentiles, fallback_used
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 8.2 Property 11 테스트: 점수 출력 범위 불변량 (Score Output Range Invariant)
    - **Property 11: 점수 출력 범위 불변량**
    - 임의의 유효한 영상 입력에 대해 predict 출력이 항상 [0, 100] 범위 검증
    - **Validates: Requirements 5.2, 7.2**

  - [ ]* 8.3 Property 12 테스트: 백분위 계산 단조 증가 (Percentile Lookup Monotonicity)
    - **Property 12: 백분위 계산 단조 증가**
    - 정렬된 백분위 배열에서 a < b이면 percentile(a) ≤ percentile(b)이고 결과 ∈ [0, 1] 검증
    - **Validates: Requirements 5.3**

  - [ ]* 8.4 Model Server 단위 테스트
    - 모델 로드 실패 시 Baseline 폴백 동작 검증
    - 입력 데이터 형식 오류 시 에러 처리 검증
    - 추론 시간 200ms 이내 벤치마크
    - _Requirements: 5.4, 5.5_

- [x] 9. Training Pipeline 구현
  - [x] 9.1 TrainingPipeline 클래스 구현
    - `__init__`: PipelineConfig (S3 경로, Champion 정보, 성능 이력)
    - `run_retrain`: 새 데이터 병합 → Champion 아키텍처로만 재학습 → 성능 비교 → 조건부 배포
    - `check_degradation`: retrain_history.json에서 3회 연속 성능 하락 감지
    - `recommend_reselection`: 전체 모델 재선정 권고 알림 출력
    - 모델 버전 관리 (versions/ 디렉토리에 이력 저장, 롤백 지원)
    - 재학습 중 오류 발생 시 기존 모델 유지 및 오류 로그 기록
    - 소규모 그룹(< 20개) 폴백 로직: 상위 그룹(구독자 구간만 다른 그룹) 모델 사용
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.3_

  - [ ]* 9.2 Property 13 테스트: 연속 하락 감지 정확성 (Consecutive Degradation Detection)
    - **Property 13: 연속 하락 감지 정확성**
    - 마지막 3개 메트릭 연속 감소 → True, 아니면 False 검증
    - **Validates: Requirements 6.5**

  - [ ]* 9.3 Property 15 테스트: 소규모 그룹 폴백 (Small Group Fallback)
    - **Property 15: 소규모 그룹 폴백**
    - 그룹 샘플 수 < 20이면 상위 그룹 모델 사용 검증
    - **Validates: Requirements 7.3**

  - [ ]* 9.4 Property 17 테스트: 그룹 독립성 (Group Independence)
    - **Property 17: 그룹 독립성**
    - 새 그룹 데이터 추가 시 기존 그룹 영상 점수 불변 검증
    - **Validates: Requirements 7.5**

  - [ ]* 9.5 Training Pipeline 단위 테스트
    - 재학습 중 예외 발생 시 기존 모델 유지 검증
    - 버전 롤백 동작 검증
    - _Requirements: 6.3, 6.4_

- [x] 10. 통합 테스트 및 End-to-End 검증
  - [x] 10.1 통합 테스트 작성 (test_integration.py)
    - 소규모 데이터(100개 영상)로 전체 학습 파이프라인 end-to-end 실행 검증
    - moto로 S3 모킹 후 모델 저장/로드 round-trip 검증
    - 알려진 값에 대한 MAE/RMSE/Spearman 메트릭 계산 정확성 검증
    - 추론 성능 200ms 이내 벤치마크
    - 재학습 트리거 시 Champion 아키텍처만 학습되는지 검증
    - 이전 버전 복원(롤백) 가능 여부 검증
    - _Requirements: 3.1, 4.1, 4.2, 5.1, 5.4, 6.1, 6.3_

- [x] 11. Final Checkpoint - 전체 테스트 통과 확인
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- `*` 표시된 태스크는 선택적이며, 빠른 MVP를 위해 건너뛸 수 있습니다
- 각 태스크는 특정 요구사항을 참조하여 추적 가능합니다
- Checkpoint에서 점진적 검증을 수행합니다
- Property 테스트는 Hypothesis 라이브러리를 사용하며, 각 정확성 속성을 독립적으로 검증합니다
- 단위 테스트는 특정 예제 및 엣지 케이스를 검증합니다
- 통합 테스트는 moto를 사용하여 AWS 서비스를 모킹합니다
