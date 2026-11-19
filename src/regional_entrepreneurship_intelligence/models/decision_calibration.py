"""Decision-rule evaluation for frozen Assignment 6 holdout scores."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


DEFAULT_KEYS = ("cbsa_code", "sector_code", "predictor_year", "target_year")


def rank_top_fraction(
    frame: pd.DataFrame,
    fraction: float,
    *,
    probability_column: str = "predicted_probability_logistic",
    key_columns: tuple[str, ...] = DEFAULT_KEYS,
) -> pd.DataFrame:
    """Select an exact ceiling-sized workload with deterministic tie handling."""
    if not 0 < fraction <= 1:
        raise ValueError("Selection fraction must be in (0, 1]")
    required = {probability_column, *key_columns}
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"Top-fraction fields are missing: {missing}")
    if frame.duplicated(list(key_columns)).any():
        raise ValueError("Decision rows must have unique evaluation keys")
    probabilities = pd.to_numeric(frame[probability_column], errors="raise")
    if probabilities.isna().any() or not np.isfinite(probabilities).all() or not probabilities.between(0, 1).all():
        raise ValueError("Decision probabilities must be finite and in [0, 1]")

    ranked = frame.copy()
    ranked[probability_column] = probabilities.astype(float)
    ranked = ranked.sort_values(
        [probability_column, *key_columns],
        ascending=[False, *([True] * len(key_columns))],
        kind="mergesort",
    ).reset_index(drop=True)
    selected_n = int(math.ceil(len(ranked) * fraction))
    ranked["selection_rank"] = np.arange(1, len(ranked) + 1)
    ranked["selected"] = ranked.selection_rank.le(selected_n)
    return ranked


def evaluate_selection(
    frame: pd.DataFrame,
    selected: pd.Series | np.ndarray,
    *,
    rule: str,
    label_column: str = "actual_gap",
) -> dict[str, float | int | str]:
    """Summarize workload, yield, coverage, and false-positive burden."""
    if label_column not in frame:
        raise ValueError(f"Decision label field is missing: {label_column}")
    labels = pd.to_numeric(frame[label_column], errors="raise")
    selected_values = np.asarray(selected)
    if len(labels) != len(selected_values) or selected_values.dtype != bool:
        raise ValueError("Selection mask must be aligned and boolean")
    if not labels.isin([0, 1]).all() or labels.nunique() != 2:
        raise ValueError("Decision labels must be binary and contain both classes")
    flagged = int(selected_values.sum())
    if flagged < 1:
        raise ValueError("Decision rule must flag at least one row")
    y = labels.to_numpy(dtype=int)
    true_positive = int(y[selected_values].sum())
    false_positive = flagged - true_positive
    false_negative = int(y[~selected_values].sum())
    precision = true_positive / flagged
    recall = true_positive / int(y.sum())
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    prevalence = float(labels.mean())
    return {
        "rule": rule,
        "flagged_n": flagged,
        "true_positive_n": true_positive,
        "false_positive_n": false_positive,
        "false_negative_n": false_negative,
        "precision": precision,
        "recall": recall,
        "captured_gap_pct": recall,
        "f1": f1,
        "lift": precision / prevalence,
        "false_positive_share": false_positive / flagged,
        "false_positives_per_true_positive": false_positive / true_positive,
    }


def evaluate_top_fraction(
    frame: pd.DataFrame,
    fraction: float,
    *,
    probability_column: str = "predicted_probability_logistic",
    label_column: str = "actual_gap",
) -> tuple[pd.DataFrame, dict[str, float | int | str]]:
    ranked = rank_top_fraction(frame, fraction, probability_column=probability_column)
    metrics = evaluate_selection(
        ranked,
        ranked.selected,
        rule=f"top_{fraction:.0%}",
        label_column=label_column,
    )
    metrics["selection_fraction"] = fraction
    metrics["probability_cutoff"] = float(
        ranked.loc[ranked.selected, probability_column].min()
    )
    return ranked, metrics


def evaluate_threshold(
    frame: pd.DataFrame,
    threshold: float,
    *,
    probability_column: str = "predicted_probability_logistic",
    label_column: str = "actual_gap",
) -> dict[str, float | int | str]:
    if probability_column not in frame:
        raise ValueError(f"Decision probability field is missing: {probability_column}")
    if not 0 <= float(threshold) <= 1:
        raise ValueError("Decision threshold must be in [0, 1]")
    probabilities = pd.to_numeric(frame[probability_column], errors="raise")
    if probabilities.isna().any() or not np.isfinite(probabilities).all() or not probabilities.between(0, 1).all():
        raise ValueError("Decision probabilities must be finite and in [0, 1]")
    metrics = evaluate_selection(
        frame,
        probabilities.ge(float(threshold)).to_numpy(dtype=bool),
        rule="development_prevalence_threshold",
        label_column=label_column,
    )
    metrics["selection_fraction"] = metrics["flagged_n"] / len(frame)
    metrics["probability_cutoff"] = float(threshold)
    return metrics
