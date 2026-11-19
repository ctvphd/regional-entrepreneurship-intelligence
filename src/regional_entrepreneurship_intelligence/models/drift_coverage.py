"""Holdout drift and complete-case coverage diagnostic helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def standardized_prevalence(
    reference: pd.DataFrame,
    comparison: pd.DataFrame,
    *,
    strata: tuple[str, ...],
    label_column: str = "actual_gap",
) -> dict[str, float | int]:
    """Apply reference composition weights to comparison stratum rates."""
    required = {*strata, label_column}
    for name, frame in (("reference", reference), ("comparison", comparison)):
        if missing := sorted(required - set(frame.columns)):
            raise ValueError(f"{name} standardization fields are missing: {missing}")
        labels = pd.to_numeric(frame[label_column], errors="raise")
        if frame.empty or not labels.isin([0, 1]).all():
            raise ValueError(f"{name} labels must be nonempty and binary")
    reference_weights = (
        reference.groupby(list(strata), observed=True, dropna=False).size() / len(reference)
    ).rename("reference_weight")
    comparison_rates = comparison.groupby(
        list(strata), observed=True, dropna=False
    )[label_column].mean().rename("comparison_rate")
    joined = reference_weights.to_frame().join(comparison_rates, how="left")
    if joined.comparison_rate.isna().any():
        raise ValueError("Comparison data lack one or more reference strata")
    return {
        "standardized_prevalence": float(
            (joined.reference_weight * joined.comparison_rate).sum()
        ),
        "reference_weight_covered": float(joined.reference_weight.sum()),
        "strata_n": int(len(joined)),
    }


def classify_eligibility(
    candidates: pd.DataFrame,
    *,
    target_required: tuple[str, ...],
    predictor_required: tuple[str, ...],
) -> pd.DataFrame:
    """Classify frozen eligibility from existing fields without imputing values."""
    required = {*target_required, *predictor_required}
    if missing := sorted(required - set(candidates.columns)):
        raise ValueError(f"Eligibility fields are missing: {missing}")
    result = candidates.copy()
    finite = result.replace([np.inf, -np.inf], np.nan)
    result["target_label_eligible"] = finite[list(target_required)].notna().all(axis=1)
    result["predictor_complete"] = finite[list(predictor_required)].notna().all(axis=1)
    result["eligible"] = result.target_label_eligible & result.predictor_complete
    return result


def exclusion_reason_table(
    candidates: pd.DataFrame,
    *,
    target_required: tuple[str, ...],
    predictor_required: tuple[str, ...],
) -> pd.DataFrame:
    """Report overlapping broad and field-level reasons among excluded rows."""
    classified = classify_eligibility(
        candidates,
        target_required=target_required,
        predictor_required=predictor_required,
    )
    excluded = classified[~classified.eligible]
    rows = []

    def add(scope: str, reason: str, mask: pd.Series) -> None:
        count = int(mask.sum())
        rows.append(
            {
                "scope": scope,
                "reason": reason,
                "excluded_n": count,
                "pct_all_candidates": count / len(classified),
                "pct_excluded": count / len(excluded) if len(excluded) else np.nan,
                "overlap_allowed": True,
            }
        )

    add(
        "broad",
        "target benchmark inputs incomplete",
        ~classified.target_label_eligible,
    )
    add(
        "broad",
        "predictor complete-case inputs incomplete",
        ~classified.predictor_complete,
    )
    add(
        "broad",
        "both target and predictor inputs incomplete",
        ~classified.target_label_eligible & ~classified.predictor_complete,
    )
    for column in target_required:
        add("target_field", f"missing {column}", excluded[column].isna())
    for column in predictor_required:
        add("predictor_field", f"missing {column}", excluded[column].isna())
    return pd.DataFrame(rows)


def standardized_mean_difference(
    included: pd.Series,
    excluded: pd.Series,
) -> float:
    """Calculate a pooled-SD standardized mean difference on available values."""
    left = pd.to_numeric(included, errors="coerce").dropna().astype(float)
    right = pd.to_numeric(excluded, errors="coerce").dropna().astype(float)
    if len(left) < 2 or len(right) < 2:
        return float("nan")
    pooled = np.sqrt((left.var(ddof=1) + right.var(ddof=1)) / 2)
    return float((left.mean() - right.mean()) / pooled) if pooled else float("nan")
