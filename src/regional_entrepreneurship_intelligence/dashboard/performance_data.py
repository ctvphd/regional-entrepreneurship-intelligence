"""Validated A7.2-only inputs and deterministic diagnostics for A7.6."""

from __future__ import annotations

import math

import pandas as pd

from .data_access import cached_dataset, cached_labels, cached_metadata
from .loader import DATA_DIR
from .overview_data import get_metric

HOLDOUT_METRICS = (
    "AP", "prevalence", "ROC_AUC", "Brier", "recall", "precision", "f1", "top10_lift",
)
DEVELOPMENT_METRICS = ("AP", "ROC_AUC", "Brier", "top10_lift")
EXPECTED_HOLDOUT_PAIRS = ((2018, 2021), (2019, 2022), (2020, 2023))
MSA_SIZE_ORDER = ("small", "middle", "large")
DISPLAY_MODELS = {
    "prevalence_benchmark": "Prevalence benchmark",
    "logistic": "Logistic regression (primary)",
    "hist_gradient_boosting": "HistGradientBoosting (sensitivity)",
    "random_forest": "Random Forest (comparison only)",
}


class PerformanceDataError(ValueError):
    """Raised when finalized A7.2 performance artifacts violate the page contract."""


def metric_value(summary: pd.DataFrame, split: str, model: str, metric: str) -> float:
    try:
        return get_metric(summary, split, model, metric)
    except (ValueError, KeyError) as exc:
        raise PerformanceDataError(str(exc)) from exc


def validate_performance_data(data: dict) -> dict:
    metadata = data["metadata"]
    if metadata.get("primary_model") != "logistic":
        raise PerformanceDataError("dashboard_metadata.json: primary_model must resolve to logistic")
    if metadata.get("sensitivity_model") != "hist_gradient_boosting":
        raise PerformanceDataError("dashboard_metadata.json: sensitivity_model must resolve to HistGradientBoosting")
    if int(metadata.get("forecast_horizon_years", 0)) != 3:
        raise PerformanceDataError("dashboard_metadata.json: forecast_horizon_years must be 3")

    summary = data["model_summary"]
    required_summary = {"dataset_split", "model", "metric", "value", "sample_n", "prevalence"}
    if not required_summary.issubset(summary.columns):
        raise PerformanceDataError("dashboard_model_summary.parquet: required metric/sample fields are missing")
    for metric in HOLDOUT_METRICS:
        metric_value(summary, "final_holdout", "logistic", metric)
    for metric in DEVELOPMENT_METRICS:
        metric_value(summary, "development_oof", "logistic", metric)
    for split in ("development_oof", "final_holdout"):
        for model in ("prevalence_benchmark", "logistic", "hist_gradient_boosting"):
            for metric in ("AP", "ROC_AUC", "Brier"):
                metric_value(summary, split, model, metric)
        core_rows = summary.loc[
            (summary.dataset_split == split)
            & summary.model.isin(("prevalence_benchmark", "logistic", "hist_gradient_boosting"))
            & (summary.metric == "AP")
        ]
        if core_rows.sample_n.nunique() != 1 or core_rows.prevalence.nunique() != 1 or len(core_rows) != 3:
            raise PerformanceDataError(f"dashboard_model_summary.parquet: comparison model populations differ in {split}")
    models = set(summary["model"].astype(str))
    if "random_forest" in models:
        for metric in ("AP", "ROC_AUC", "Brier"):
            metric_value(summary, "development_oof", "random_forest", metric)

    predictions = data["predictions"]
    required_prediction_fields = {
        "cbsa_code", "sector_code", "predictor_year", "target_year", "actual_gap",
        "development_or_holdout", "logistic_probability", "hgb_probability",
    }
    missing = sorted(required_prediction_fields - set(predictions.columns))
    if missing:
        raise PerformanceDataError("dashboard_model_predictions.parquet: missing " + ", ".join(missing))
    key = ["cbsa_code", "sector_code", "predictor_year", "target_year"]
    if predictions[key].isna().any().any() or predictions.duplicated(key).any():
        raise PerformanceDataError("dashboard_model_predictions.parquet: null or duplicate prediction key")
    if not (predictions["target_year"].astype(int) == predictions["predictor_year"].astype(int) + 3).all():
        raise PerformanceDataError("dashboard_model_predictions.parquet: prediction years are not exact t+3 pairs")
    if not set(predictions["development_or_holdout"].astype(str)).issubset({"development_oof", "final_holdout"}):
        raise PerformanceDataError("dashboard_model_predictions.parquet: unapproved evaluation split")
    if not predictions["actual_gap"].isin([0, 1]).all():
        raise PerformanceDataError("dashboard_model_predictions.parquet: actual_gap must be binary")
    for field in ("logistic_probability", "hgb_probability"):
        values = predictions[field].astype(float)
        if not values.map(math.isfinite).all() or not values.between(0, 1).all():
            raise PerformanceDataError(f"dashboard_model_predictions.parquet: invalid {field}")
    for split in ("development_oof", "final_holdout"):
        rows = predictions.loc[predictions["development_or_holdout"] == split]
        if rows.empty or rows["actual_gap"].nunique() != 2:
            raise PerformanceDataError(f"dashboard_model_predictions.parquet: {split} lacks both outcome classes")
        expected_n = summary.loc[
            (summary["dataset_split"] == split)
            & (summary["model"] == "logistic")
            & (summary["metric"] == "AP"), "sample_n",
        ]
        if len(expected_n) != 1 or int(expected_n.iloc[0]) != len(rows):
            raise PerformanceDataError(f"dashboard_model_summary.parquet: {split} N does not match prediction rows")

    calibration = data["calibration"]
    required_calibration = {
        "dataset_split", "model", "risk_bin", "n", "mean_predicted_probability", "observed_gap_prevalence",
    }
    if not required_calibration.issubset(calibration.columns):
        raise PerformanceDataError("dashboard_calibration.parquet: required calibration columns are missing")
    for split in ("development_oof", "final_holdout"):
        for model in ("logistic", "hist_gradient_boosting"):
            bins = calibration.loc[(calibration.dataset_split == split) & (calibration.model == model)]
            if bins.empty or bins["n"].isna().any() or (bins["n"] <= 0).any():
                raise PerformanceDataError(f"dashboard_calibration.parquet: missing/invalid {split}/{model} bins")
            for field in ("mean_predicted_probability", "observed_gap_prevalence"):
                values = bins[field].astype(float)
                if not values.map(math.isfinite).all() or not values.between(0, 1).all():
                    raise PerformanceDataError(f"dashboard_calibration.parquet: invalid {field}")

    by_year = data["model_by_year"]
    if "dataset_split" not in by_year or "predictor_year" not in by_year or "target_year" not in by_year:
        raise PerformanceDataError("dashboard_model_by_year.parquet: required year/split columns missing")
    years = by_year.loc[(by_year.dataset_split == "final_holdout") & (by_year.model == "logistic")]
    observed_pairs = tuple(zip(years.predictor_year.astype(int), years.target_year.astype(int)))
    if observed_pairs != EXPECTED_HOLDOUT_PAIRS:
        raise PerformanceDataError("dashboard_model_by_year.parquet: finalized holdout year sequence is incomplete or unordered")
    for metric in ("AP", "ROC_AUC", "Brier"):
        if metric not in years or years[metric].isna().any():
            raise PerformanceDataError(f"dashboard_model_by_year.parquet: missing finalized logistic {metric}")
    hgb_years = by_year.loc[(by_year.dataset_split == "final_holdout") & (by_year.model == "hist_gradient_boosting")]
    hgb_pairs = tuple(zip(hgb_years.predictor_year.astype(int), hgb_years.target_year.astype(int)))
    if hgb_pairs != EXPECTED_HOLDOUT_PAIRS or any(hgb_years[field].isna().any() for field in ("AP", "ROC_AUC", "Brier")):
        raise PerformanceDataError("dashboard_model_by_year.parquet: finalized HGB year rows are incomplete")

    by_size = data["model_by_msa_size"]
    if "dataset_split" not in by_size:
        raise PerformanceDataError("dashboard_model_by_msa_size.parquet: dataset_split is missing")
    size_rows = by_size.loc[(by_size.dataset_split == "final_holdout") & (by_size.model == "logistic")]
    if set(size_rows.msa_size_group.astype(str)) != set(MSA_SIZE_ORDER) or len(size_rows) != len(MSA_SIZE_ORDER):
        raise PerformanceDataError("dashboard_model_by_msa_size.parquet: expected small, middle, large holdout rows")
    for metric in ("AP", "ROC_AUC", "top10_lift"):
        if metric not in size_rows or size_rows[metric].isna().any():
            raise PerformanceDataError(f"dashboard_model_by_msa_size.parquet: missing {metric}")
    hgb_size_rows = by_size.loc[(by_size.dataset_split == "final_holdout") & (by_size.model == "hist_gradient_boosting")]
    if len(hgb_size_rows) != len(MSA_SIZE_ORDER) or set(hgb_size_rows.msa_size_group.astype(str)) != set(MSA_SIZE_ORDER) or any(
        hgb_size_rows[field].isna().any() for field in ("AP", "ROC_AUC", "top10_lift")
    ):
        raise PerformanceDataError("dashboard_model_by_msa_size.parquet: finalized HGB size rows are incomplete")

    by_sector = data["model_by_sector"]
    required_sector = {"sector_code", "sector_name", "sample_n", "positive_n", "prevalence", "AP", "ROC_AUC", "sufficient_sample_flag", "model", "dataset_split"}
    if not required_sector.issubset(by_sector.columns):
        raise PerformanceDataError("dashboard_model_by_sector.parquet: sufficient_sample_flag or required fields missing")
    sector_rows = by_sector.loc[(by_sector.dataset_split == "final_holdout") & (by_sector.model == "logistic")]
    if sector_rows.empty or sector_rows["sufficient_sample_flag"].isna().any():
        raise PerformanceDataError("dashboard_model_by_sector.parquet: logistic sector sufficiency flags are missing")
    sufficient = sector_rows.loc[sector_rows.sufficient_sample_flag.astype(bool)]
    insufficient = sector_rows.loc[~sector_rows.sufficient_sample_flag.astype(bool)]
    if sufficient[["AP", "ROC_AUC"]].isna().any().any() or insufficient[["AP", "ROC_AUC"]].notna().any().any():
        raise PerformanceDataError("dashboard_model_by_sector.parquet: metrics do not follow the source sufficiency flags")

    labels = data["labels"]
    if not isinstance(labels, dict) or not {"models", "metrics"}.issubset(labels):
        raise PerformanceDataError("dashboard_labels.json: model/metric dictionaries are missing")
    if not {"logistic", "hist_gradient_boosting", "prevalence_benchmark"}.issubset(labels["models"]):
        raise PerformanceDataError("dashboard_labels.json: required comparison model labels are missing")
    return data


def load_performance_data(data_dir=DATA_DIR) -> dict:
    """Load only dashboard-ready artifacts required by the fixed performance page."""
    try:
        data = {
            "metadata": cached_metadata(str(data_dir)),
            "labels": cached_labels(str(data_dir)),
            "model_summary": cached_dataset("model_summary", str(data_dir)),
            "calibration": cached_dataset("calibration", str(data_dir)),
            "model_by_year": cached_dataset("model_by_year", str(data_dir)),
            "model_by_sector": cached_dataset("model_by_sector", str(data_dir)),
            "model_by_msa_size": cached_dataset("model_by_msa_size", str(data_dir)),
            "predictions": cached_dataset("model_predictions", str(data_dir)),
        }
    except (OSError, ValueError, KeyError) as exc:
        if isinstance(exc, PerformanceDataError):
            raise
        raise PerformanceDataError(str(exc)) from exc
    return validate_performance_data(data)


def build_risk_concentration_table(summary: pd.DataFrame) -> pd.DataFrame:
    """Present frozen lift/prevalence and protocol-defined selected counts."""
    prevalence = metric_value(summary, "final_holdout", "logistic", "prevalence")
    sample_n = int(summary.loc[
        (summary.dataset_split == "final_holdout") & (summary.model == "logistic") & (summary.metric == "AP"),
        "sample_n",
    ].iloc[0])
    rows = []
    for model in ("logistic", "hist_gradient_boosting", "prevalence_benchmark"):
        for fraction, metric in ((0.10, "top10_lift"), (0.20, "top20_lift"), (0.25, "top25_lift")):
            lift = metric_value(summary, "final_holdout", model, metric)
            rows.append({
                "Model": DISPLAY_MODELS[model],
                "Top-risk fraction": fraction,
                "Selected N (ceiling rule)": math.ceil(sample_n * fraction),
                "Observed gap prevalence (lift x overall)": lift * prevalence,
                "Overall prevalence": prevalence,
                "Lift": lift,
            })
    return pd.DataFrame(rows)


def build_sector_performance_table(by_sector: pd.DataFrame) -> pd.DataFrame:
    """Expose source sector metrics and keep suppressed scores explicitly blank."""
    rows = by_sector.loc[(by_sector.dataset_split == "final_holdout") & (by_sector.model == "logistic")].copy()
    rows = rows.sort_values(
        ["sufficient_sample_flag", "AP", "sector_name"],
        ascending=[False, False, True],
        na_position="last",
    )
    return pd.DataFrame({
        "Sector": rows.sector_name.astype(str),
        "N": rows.sample_n.astype(int),
        "Positive N": rows.positive_n.astype(int),
        "Prevalence": rows.prevalence.astype(float),
        "AP": rows.AP,
        "ROC-AUC": rows.ROC_AUC,
        "Sufficient sample": rows.sufficient_sample_flag.astype(bool),
    }).reset_index(drop=True)
