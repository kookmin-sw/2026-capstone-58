"""
ML 점수 모델 학습 스크립트.

사용법:
    python train.py                    # data/ 디렉토리의 모든 CSV 사용
    python train.py data/cat_20_*.csv  # 특정 파일만 사용

흐름:
    1. CSV 데이터 로드
    2. 백분위 테이블 구축
    3. 피처 엔지니어링
    4. 레이블 생성
    5. 데이터 분할 (채널 단위)
    6. 후보 모델 학습 + Champion 선정
    7. 평가 리포트 출력
    8. 모델 아티팩트 저장 (models/)
"""

import argparse
import glob
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.feature_engineer import FeatureEngineer
from src.label_generator import LabelGenerator
from src.model_evaluator import ModelEvaluator, check_monotonic_increase
from src.model_trainer import ModelTrainer, TrainingConfig


# ── 설정 ──────────────────────────────────────────────────────────

DATA_DIR = Path("data")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


# ── 데이터 로드 ──────────────────────────────────────────────────

def load_csv_data(file_patterns: list[str] = None) -> pd.DataFrame:
    """CSV 파일들을 로드하여 하나의 DataFrame으로 합친다."""
    if file_patterns:
        files = []
        for pattern in file_patterns:
            files.extend(glob.glob(pattern))
    else:
        files = sorted(DATA_DIR.glob("*.csv"))

    if not files:
        print("❌ 데이터 파일을 찾을 수 없습니다.")
        print(f"   data/ 디렉토리에 CSV 파일이 있는지 확인하세요.")
        print(f"   수집: python collect_all.py")
        sys.exit(1)

    dfs = []
    for f in files:
        df = pd.read_csv(f)
        dfs.append(df)
        print(f"  ✓ {f} ({len(df):,}행)")

    combined = pd.concat(dfs, ignore_index=True)
    print(f"  → 총 {len(combined):,}개 영상 로드 완료")
    return combined


def df_to_video_dicts(df: pd.DataFrame) -> list[dict]:
    """DataFrame을 영상 딕셔너리 리스트로 변환."""
    videos = []

    # 채널별 평균 조회수 계산 (vs_channel_avg용)
    channel_avg = df.groupby("channel_id")["view_count"].mean().to_dict()

    for _, row in df.iterrows():
        # 구독자 구간 결정
        subs = int(row.get("subscriber_count", 1) or 1)
        tier = "S" if subs < 50000 else "M" if subs < 200000 else "L" if subs < 500000 else "XL"
        is_short = bool(row.get("is_short", False))
        is_short_int = 1 if is_short else 0
        cat_id = str(row.get("category_id", "1"))
        view_count = int(row.get("view_count", 0) or 0)
        ch_id = str(row.get("channel_id", ""))
        days = float(row.get("days_since_upload", 1) or 1)

        # vs_channel_avg: CSV에 있으면 사용, 없으면 계산
        if "vs_channel_avg" in row and pd.notna(row["vs_channel_avg"]):
            vs_channel_avg = float(row["vs_channel_avg"])
        else:
            avg = channel_avg.get(ch_id, view_count)
            vs_channel_avg = view_count / avg if avg > 0 else 1.0

        # daily_views: CSV에 있으면 사용, 없으면 계산
        if "daily_views" in row and pd.notna(row["daily_views"]):
            daily_views = float(row["daily_views"])
        else:
            daily_views = view_count / max(days, 1)

        video = {
            "video_id": str(row.get("video_id", "")),
            "channel_id": ch_id,
            "view_count": view_count,
            "like_count": int(row.get("like_count", 0) or 0),
            "comment_count": int(row.get("comment_count", 0) or 0),
            "subscriber_count": subs,
            "duration_sec": int(row.get("duration_sec", 0) or 0),
            "category_id": cat_id,
            "is_short": is_short,
            "published_at": str(row.get("published_at", "")) or None,
            "comparison_group": f"{tier}_{is_short_int}_{cat_id}",
            "vps": float(row.get("views_per_sub", 0) or 0),
            "vs_channel_avg": vs_channel_avg,
            "daily_views": daily_views,
        }
        videos.append(video)
    return videos


# ── 백분위 테이블 구축 ────────────────────────────────────────────

def build_percentile_tables(videos: list[dict]) -> dict:
    """영상 데이터에서 Comparison Group별 백분위 테이블을 구축한다."""
    from collections import defaultdict

    groups = defaultdict(list)
    for v in videos:
        groups[v["comparison_group"]].append(v)

    tables = {}
    for group_key, group_videos in groups.items():
        vps_vals = sorted([v["vps"] for v in group_videos])
        eng_vals = sorted([
            (v["like_count"] + v["comment_count"]) / max(v["view_count"], 1)
            for v in group_videos
        ])
        like_vals = sorted([
            v["like_count"] / max(v["view_count"], 1)
            for v in group_videos
        ])
        vca_vals = sorted([v.get("vs_channel_avg", 1.0) for v in group_videos])
        dv_vals = sorted([v.get("daily_views", 0.0) for v in group_videos])

        def to_percentile_array(vals):
            if len(vals) < 2:
                return np.linspace(0, max(vals[0] if vals else 0.001, 0.001), 101).tolist()
            return np.percentile(vals, np.linspace(0, 100, 101)).tolist()

        tables[group_key] = {
            "vps": to_percentile_array(vps_vals),
            "engagement_rate": to_percentile_array(eng_vals),
            "like_rate": to_percentile_array(like_vals),
            "vs_channel_avg": to_percentile_array(vca_vals),
            "daily_views": to_percentile_array(dv_vals),
        }

    return tables


# ── 메인 학습 흐름 ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ML 점수 모델 학습")
    parser.add_argument("files", nargs="*", help="학습에 사용할 CSV 파일 패턴 (미지정 시 data/*.csv)")
    parser.add_argument("--cleanup", action="store_true",
                        help="학습 완료 후 data/ 디렉토리의 CSV 파일 삭제 (YouTube ToS 준수)")
    args = parser.parse_args()

    print("=" * 60)
    print("ML 점수 모델 학습")
    print("=" * 60)

    # 1. 데이터 로드
    print("\n[1/7] 데이터 로드")
    file_patterns = args.files if args.files else None
    df = load_csv_data(file_patterns)

    # 기본 필터링: view_count > 0, subscriber_count > 0
    df = df[(df["view_count"] > 0) & (df["subscriber_count"] > 0)]
    print(f"  → 필터링 후: {len(df):,}개 영상")

    # 2. 영상 딕셔너리 변환
    print("\n[2/7] 데이터 변환")
    videos = df_to_video_dicts(df)
    print(f"  → {len(videos):,}개 영상 딕셔너리 생성")

    # 3. 백분위 테이블 구축
    print("\n[3/7] 백분위 테이블 구축")
    percentile_tables = build_percentile_tables(videos)
    print(f"  → {len(percentile_tables)}개 Comparison Group")

    # 4. 피처 엔지니어링
    print("\n[4/7] 피처 엔지니어링")
    fe = FeatureEngineer(percentile_tables=percentile_tables)
    X = fe.transform_batch(videos).values
    print(f"  → 피처 매트릭스: {X.shape}")

    # 스케일러 fit
    scaler_params = fe.fit_scalers(videos)
    fe_scaled = FeatureEngineer(percentile_tables=percentile_tables, scaler_params=scaler_params)
    X_scaled = fe_scaled.transform_batch(videos).values
    print(f"  → 스케일링 적용 완료")

    # 5. 레이블 생성
    print("\n[5/7] 레이블 생성")
    lg = LabelGenerator()
    labels = lg.generate_labels(
        videos,
        strategy="multi_metric",
        weights={"vps": 0.40, "vs_channel_avg": 0.40, "daily_views": 0.20},
    )
    dist_check = lg.validate_distribution(labels)
    print(f"  → 레이블 범위: [{labels.min():.1f}, {labels.max():.1f}]")
    print(f"  → 분포 균등성: {'✓' if dist_check['is_uniform'] else '⚠ ' + dist_check['concentration_warning']}")

    # 6. 데이터 분할 + 모델 학습
    print("\n[6/7] 모델 학습")
    channel_ids = np.array([v["channel_id"] for v in videos])

    trainer = ModelTrainer(TrainingConfig(random_state=42))

    # 채널 단위 분할
    X_train, X_val, X_test, y_train, y_val, y_test = trainer.split_data(
        X_scaled, labels, channel_ids
    )
    print(f"  → Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")

    # 그룹 필터링 (최소 20개)
    group_keys = np.array([v["comparison_group"] for v in videos])

    # 후보 모델 학습
    print(f"  → 후보 모델 학습 중... (Ridge, RF, XGBoost, LightGBM, Stacking)")
    start_time = time.time()
    models = trainer.train_all_candidates(X_train, y_train, X_val, y_val)
    elapsed = time.time() - start_time
    print(f"  → {len(models)}개 모델 학습 완료 ({elapsed:.1f}초)")

    # Champion 선정
    champion_name = trainer.select_champion(models, X_val, y_val)
    print(f"  → 🏆 Champion: {champion_name}")

    # 7. 평가
    print("\n[7/7] 모델 평가")
    evaluator = ModelEvaluator()

    # Val 세트 성능 (Champion 선정 기준)
    from scipy.stats import spearmanr as _spearmanr
    print(f"\n  [검증 세트 — Champion 선정 기준]")
    print(f"  {'모델':<20s} {'Spearman(Val)':>12s}")
    print(f"  {'-'*34}")

    val_metrics = {}
    for name, model in models.items():
        val_pred = model.predict(X_val)
        val_corr, _ = _spearmanr(val_pred, y_val)
        val_metrics[name] = val_corr
        marker = " ← Champion" if name == champion_name else ""
        print(f"  {name:<20s} {val_corr:>12.4f}{marker}")

    # Test 세트 성능 (최종 성능 리포트)
    print(f"\n  [테스트 세트 — 최종 성능 리포트]")
    print(f"  {'모델':<20s} {'MAE':>8s} {'RMSE':>8s} {'Spearman':>10s}")
    print(f"  {'-'*48}")

    all_metrics = {}
    for name, model in models.items():
        metrics = evaluator.evaluate(model, X_test, y_test)
        all_metrics[name] = metrics
        marker = " ← Champion" if name == champion_name else ""
        print(f"  {name:<20s} {metrics['mae']:>8.2f} {metrics['rmse']:>8.2f} {metrics['spearman']:>10.4f}{marker}")

    # Baseline 비교
    baseline_metrics = {"mae": 999, "rmse": 999, "spearman": 0.0}
    # Baseline: 새 공식 VPS×40 + vs_channel_avg×40 + daily_views×20

    # 백분위 조회 헬퍼
    def _lookup_pct(value, sorted_values):
        arr = np.array(sorted_values)
        idx = np.searchsorted(arr, value, side="right")
        return min(idx, 100) / 100.0

    # Baseline 점수 계산 (40/40/20 공식)
    baseline_preds = []
    for v in videos:
        group_key = v["comparison_group"]
        group_table = percentile_tables.get(group_key)
        if group_table is not None:
            vps_pct = _lookup_pct(v["vps"], group_table["vps"])
            vca_pct = _lookup_pct(v["vs_channel_avg"], group_table.get("vs_channel_avg", [0, 1]))
            dv_pct = _lookup_pct(v["daily_views"], group_table.get("daily_views", [0, 1]))
        else:
            vps_pct = 0.5
            vca_pct = 0.5
            dv_pct = 0.5
        score = vps_pct * 40.0 + vca_pct * 40.0 + dv_pct * 20.0
        baseline_preds.append(score)
    baseline_preds = np.array(baseline_preds)

    # 테스트 세트에 해당하는 baseline 예측 추출
    test_indices = []
    unique_channels = np.unique(channel_ids)
    rng = np.random.RandomState(42)
    rng.shuffle(unique_channels)
    n_train_ch = int(np.round(len(unique_channels) * 0.70))
    n_val_ch = int(np.round(len(unique_channels) * 0.15))
    test_channels = set(unique_channels[n_train_ch + n_val_ch:])
    test_mask = np.array([ch in test_channels for ch in channel_ids])
    baseline_test_preds = baseline_preds[test_mask]

    from scipy.stats import spearmanr
    baseline_mae = float(np.mean(np.abs(baseline_test_preds - y_test)))
    baseline_rmse = float(np.sqrt(np.mean((baseline_test_preds - y_test) ** 2)))
    baseline_spearman, _ = spearmanr(baseline_test_preds, y_test)
    baseline_metrics = {"mae": baseline_mae, "rmse": baseline_rmse, "spearman": float(baseline_spearman)}

    print(f"\n  {'Baseline(40/40/20)':<20s} {baseline_mae:>8.2f} {baseline_rmse:>8.2f} {baseline_spearman:>10.4f}")

    champion_metrics = all_metrics[champion_name]
    comparison = evaluator.compare_with_baseline(champion_metrics, baseline_metrics)
    print(f"\n  Champion vs Baseline:")
    print(f"    MAE:      {comparison['comparison_report']['mae_diff']:+.2f}")
    print(f"    RMSE:     {comparison['comparison_report']['rmse_diff']:+.2f}")
    print(f"    Spearman: {comparison['comparison_report']['spearman_diff']:+.4f}")
    print(f"    개선 여부: {'✓ 개선됨' if comparison['improved'] else '✗ 개선 안됨'}")

    # VPS 단조 증가 검증
    vps_values = np.array([v["vps"] for v in videos])[test_mask]
    champion_preds = models[champion_name].predict(X_test)
    monotonic = check_monotonic_increase(champion_preds, vps_values)
    print(f"    단조 증가: {'✓' if monotonic else '✗'}")

    # 8. 모델 저장
    print("\n" + "=" * 60)
    print("모델 저장")
    print("=" * 60)

    today = datetime.now().strftime("%Y%m%d")

    # Champion 모델 저장
    model_path = MODELS_DIR / "champion_model.joblib"
    joblib.dump(models[champion_name], model_path)
    print(f"  ✓ 모델: {model_path}")

    # 스케일러 파라미터 저장
    scaler_path = MODELS_DIR / "scaler_params.json"
    with open(scaler_path, "w", encoding="utf-8") as f:
        json.dump(scaler_params, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 스케일러: {scaler_path}")

    # 메타데이터 저장
    metadata = trainer.save_metadata(models, champion_name, champion_metrics)
    metadata["baseline_metrics"] = baseline_metrics
    metadata["training_data"] = {
        "total_videos": len(videos),
        "total_channels": len(np.unique(channel_ids)),
        "groups": len(percentile_tables),
    }
    metadata["all_candidates"] = {
        name: {"mae": m["mae"], "rmse": m["rmse"], "spearman": m["spearman"]}
        for name, m in all_metrics.items()
    }

    meta_path = MODELS_DIR / "champion_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 메타데이터: {meta_path}")

    # 백분위 테이블 저장 (추론 시 필요)
    tables_path = MODELS_DIR / "percentile_tables.json"
    with open(tables_path, "w", encoding="utf-8") as f:
        json.dump(percentile_tables, f)
    print(f"  ✓ 백분위 테이블: {tables_path}")

    # 선정 리포트 저장
    selection_report = {
        "selected_at": datetime.now(timezone.utc).isoformat(),
        "candidates": {
            name: {"mae": m["mae"], "rmse": m["rmse"], "spearman": m["spearman"]}
            for name, m in all_metrics.items()
        },
        "champion": champion_name,
        "selection_criteria": "spearman",
        "baseline_metrics": baseline_metrics,
    }
    report_path = MODELS_DIR / "selection_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(selection_report, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 선정 리포트: {report_path}")

    # 버전 이력
    version_path = MODELS_DIR / f"versions/v1_{today}.joblib"
    os.makedirs(MODELS_DIR / "versions", exist_ok=True)
    joblib.dump(models[champion_name], version_path)
    print(f"  ✓ 버전 이력: {version_path}")

    print(f"\n{'='*60}")
    print(f"✅ 학습 완료!")
    print(f"   Champion: {champion_name} (Spearman: {champion_metrics['spearman']:.4f})")
    print(f"   Baseline 대비: Spearman {comparison['comparison_report']['spearman_diff']:+.4f}")
    print(f"{'='*60}")

    # 데이터 정리 (YouTube ToS 준수)
    if args.cleanup:
        print(f"\n[정리] --cleanup 플래그 감지. data/ CSV 파일 삭제 중...")
        csv_files = list(DATA_DIR.glob("*.csv"))
        for f in csv_files:
            f.unlink()
            print(f"  ✓ 삭제: {f}")
        print(f"  → {len(csv_files)}개 파일 삭제 완료 (YouTube ToS 준수)")
    else:
        print(f"\n💡 참고: YouTube ToS에 따라 원본 데이터는 30일 내 삭제해야 합니다.")
        print(f"   삭제하려면: python train.py --cleanup")


if __name__ == "__main__":
    main()
