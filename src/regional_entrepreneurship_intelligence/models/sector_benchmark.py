"""Leakage-safe sector-prevalence benchmark helpers for frozen A6 labels."""

from __future__ import annotations

import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.models.baseline import (
    lift_table,
    probability_metrics,
)


def fit_sector_prevalence(
    development: pd.DataFrame,
    *,
    sector_column: str = "sector_code",
    label_column: str = "actual_gap",
) -> pd.DataFrame:
    """Calculate sector scores from development labels only."""
    missing = sorted({sector_column, label_column} - set(development.columns))
    if missing:
        raise ValueError(f"Sector benchmark fields are missing: {missing}")
    data = development[[sector_column, label_column]].copy()
    if data.isna().any().any():
        raise ValueError("Sector benchmark training fields cannot be missing")
    labels = pd.to_numeric(data[label_column], errors="raise")
    if not labels.isin([0, 1]).all():
        raise ValueError("Sector benchmark labels must be binary")
    data[label_column] = labels.astype("int8")
    result = data.groupby(sector_column, as_index=False, sort=True).agg(
        development_n=(label_column, "size"),
        development_gap_n=(label_column, "sum"),
        development_gap_prevalence=(label_column, "mean"),
    )
    if result.empty or result[sector_column].duplicated().any():
        raise ValueError("Sector benchmark requires unique nonempty sector rates")
    return result


def score_sector_prevalence(
    holdout: pd.DataFrame,
    sector_rates: pd.DataFrame,
    *,
    sector_column: str = "sector_code",
    score_column: str = "sector_only_probability",
    unseen_fallback: float | None = None,
) -> pd.DataFrame:
    """Assign frozen development sector rates without reading holdout labels."""
    required_rates = {sector_column, "development_gap_prevalence"}
    if missing := sorted(required_rates - set(sector_rates.columns)):
        raise ValueError(f"Sector-rate fields are missing: {missing}")
    if sector_column not in holdout:
        raise ValueError(f"Holdout sector field is missing: {sector_column}")
    if sector_rates[sector_column].duplicated().any():
        raise ValueError("Sector rates must contain one row per sector")
    result = holdout.copy()
    rate_map = sector_rates.set_index(sector_column).development_gap_prevalence
    result[score_column] = result[sector_column].map(rate_map)
    unseen = sorted(result.loc[result[score_column].isna(), sector_column].astype(str).unique())
    if unseen:
        if unseen_fallback is None:
            raise ValueError(f"Holdout contains unseen sectors: {unseen}")
        if not 0 <= float(unseen_fallback) <= 1:
            raise ValueError("Unseen-sector fallback must be a probability in [0, 1]")
        result[score_column] = result[score_column].fillna(float(unseen_fallback))
    return result


def benchmark_performance(
    labels: pd.Series,
    probabilities: pd.Series | np.ndarray,
) -> dict[str, float]:
    metrics = probability_metrics(labels, np.asarray(probabilities, dtype=float))
    lift = lift_table(labels, np.asarray(probabilities, dtype=float), cuts=(0.10,)).iloc[0]
    prevalence = float(pd.to_numeric(labels, errors="raise").mean())
    return {
        "n": int(len(labels)),
        "prevalence": prevalence,
        "AP": float(metrics["pr_auc"]),
        "AP_prevalence_ratio": float(metrics["pr_auc"] / prevalence),
        "ROC_AUC": float(metrics["roc_auc"]),
        "Brier": float(metrics["brier_score"]),
        "top10_lift": float(lift.lift_ratio),
    }


def within_sector_logistic_performance(
    holdout: pd.DataFrame,
    *,
    sector_column: str = "sector_code",
    label_column: str = "actual_gap",
    probability_column: str = "predicted_probability_logistic",
    minimum_positives: int = 30,
) -> pd.DataFrame:
    required = {sector_column, label_column, probability_column}
    if missing := sorted(required - set(holdout.columns)):
        raise ValueError(f"Within-sector fields are missing: {missing}")
    rows = []
    for sector, group in holdout.groupby(sector_column, sort=True):
        positive_n = int(group[label_column].sum())
        negative_n = int(len(group) - positive_n)
        eligible = positive_n >= minimum_positives and negative_n > 0
        row = {
            sector_column: sector,
            "n": int(len(group)),
            "positive_n": positive_n,
            "negative_n": negative_n,
            "prevalence": float(group[label_column].mean()),
            "eligible": eligible,
            "logistic_AP": np.nan,
            "logistic_ROC_AUC": np.nan,
            "AP_prevalence_ratio": np.nan,
        }
        if eligible:
            metrics = probability_metrics(group[label_column], group[probability_column].to_numpy())
            row.update(
                logistic_AP=float(metrics["pr_auc"]),
                logistic_ROC_AUC=float(metrics["roc_auc"]),
                AP_prevalence_ratio=float(metrics["pr_auc"] / row["prevalence"]),
            )
        rows.append(row)
    return pd.DataFrame(rows)
