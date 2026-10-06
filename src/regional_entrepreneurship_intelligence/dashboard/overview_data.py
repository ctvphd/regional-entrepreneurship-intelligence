"""Validated, A7.2-only inputs for the Executive Overview."""

from __future__ import annotations

import math

from .data_access import cached_dataset, cached_metadata
from .loader import DATA_DIR, load_dashboard_labels

REQUIRED_HOLDOUT_METRICS = ("AP", "prevalence", "ROC_AUC", "Brier", "top10_lift", "top20_lift", "top25_lift")
REQUIRED_COMPARISON_METRICS = ("AP", "ROC_AUC", "Brier")
TOP_N_OPTIONS = (10, 25, 50)
HOLDOUT_TABLE_LABEL = "Retrospective final temporal holdout predictions"


class OverviewDataError(ValueError):
    """Raised when finalized A7.2 inputs cannot support the Overview contract."""


def get_metric(summary, dataset_split: str, model: str, metric: str) -> float:
    rows = summary.loc[
        (summary["dataset_split"] == dataset_split)
        & (summary["model"] == model)
        & (summary["metric"] == metric),
        "value",
    ]
    if len(rows) != 1 or rows.isna().any() or not math.isfinite(float(rows.iloc[0])):
        raise OverviewDataError(
            f"dashboard_model_summary: expected one finite {dataset_split}/{model}/{metric} row"
        )
    return float(rows.iloc[0])


def validate_overview_data(data: dict) -> dict:
    metadata = data["metadata"]
    if metadata.get("primary_model") != "logistic":
        raise OverviewDataError("dashboard_metadata.json: primary_model must resolve to logistic")
    if metadata.get("sensitivity_model") != "hist_gradient_boosting":
        raise OverviewDataError("dashboard_metadata.json: sensitivity_model must resolve to HistGradientBoosting")

    summary = data["model_summary"]
    required = [("final_holdout", "logistic", metric) for metric in REQUIRED_HOLDOUT_METRICS]
    required += [("development_oof", "logistic", metric) for metric in REQUIRED_COMPARISON_METRICS]
    for split, model, metric in required:
        get_metric(summary, split, model, metric)

    holdout = data["predictions"].loc[data["predictions"]["development_or_holdout"] == "final_holdout"]
    if holdout.empty:
        raise OverviewDataError("dashboard_model_predictions.parquet: no final_holdout rows")
    if holdout["cbsa_code"].isna().any() or holdout["sector_code"].isna().any():
        raise OverviewDataError("dashboard_model_predictions.parquet: holdout identifiers contain nulls")
    if not (holdout["target_year"].astype(int) == holdout["predictor_year"].astype(int) + int(metadata["forecast_horizon_years"])).all():
        raise OverviewDataError("dashboard_model_predictions.parquet: predictor/target horizon is inconsistent")
    summary_n = summary.loc[
        (summary["dataset_split"] == "final_holdout")
        & (summary["model"] == "logistic")
        & (summary["metric"] == "AP"),
        "sample_n",
    ]
    if len(summary_n) != 1 or int(summary_n.iloc[0]) != len(holdout):
        raise OverviewDataError("dashboard_model_summary.parquet: holdout N does not reconcile to prediction rows")

    calibration = data["calibration"]
    if calibration.loc[
        (calibration["dataset_split"] == "final_holdout") & (calibration["model"] == "logistic")
    ].empty:
        raise OverviewDataError("dashboard_calibration.parquet: no final-holdout logistic bins")
    for dataset_name, key in (("model_by_year", "dataset_split"), ("model_by_msa_size", "dataset_split")):
        if data[dataset_name].loc[data[dataset_name][key] == "final_holdout"].empty:
            raise OverviewDataError(f"dashboard_{dataset_name}.parquet: no final_holdout rows")
    if data["coverage"].empty:
        raise OverviewDataError("dashboard_coverage.parquet: no coverage rows")
    if data["sources"].empty:
        raise OverviewDataError("dashboard_sources.parquet: no source rows")
    if not isinstance(data["labels"], dict) or "models" not in data["labels"] or "metrics" not in data["labels"]:
        raise OverviewDataError("dashboard_labels.json: required model/metric dictionaries are missing")
    return data


def load_overview_data(data_dir=DATA_DIR) -> dict:
    """Load and validate only the dashboard-ready Overview inputs."""
    try:
        data = {
            "metadata": cached_metadata(str(data_dir)),
            "labels": load_dashboard_labels(data_dir=data_dir),
            "model_summary": cached_dataset("model_summary", str(data_dir)),
            "predictions": cached_dataset("model_predictions", str(data_dir)),
            "calibration": cached_dataset("calibration", str(data_dir)),
            "model_by_year": cached_dataset("model_by_year", str(data_dir)),
            "model_by_msa_size": cached_dataset("model_by_msa_size", str(data_dir)),
            "coverage": cached_dataset("coverage", str(data_dir)),
            "sources": cached_dataset("sources", str(data_dir)),
        }
    except (OSError, ValueError, KeyError) as exc:
        if isinstance(exc, OverviewDataError):
            raise
        raise OverviewDataError(str(exc)) from exc
    return validate_overview_data(data)
