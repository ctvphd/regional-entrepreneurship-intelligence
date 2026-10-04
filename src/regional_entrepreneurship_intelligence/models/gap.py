"""Reusable fold-local entrepreneurial-gap target construction helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.models.design import PREDICTION_HORIZON_YEARS
from regional_entrepreneurship_intelligence.models.temporal import build_temporal_pairs

THRESHOLD_COLUMNS = {
    "p10": "gap_p10",
    "p20": "gap_p20",
    "p25": "gap_p25",
    "mean_minus_1sd": "gap_minus_1sd",
}


def calculate_gap_thresholds(residuals: pd.Series) -> dict[str, float | int]:
    """Calculate the locked primary p20 and diagnostic cutoffs from training residuals."""
    values = pd.to_numeric(residuals, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if values.empty:
        raise ValueError("At least one finite training residual is required")
    mean = float(values.mean())
    sd = float(values.std(ddof=1)) if len(values) > 1 else 0.0
    p10, p20, p25 = values.quantile([0.10, 0.20, 0.25]).astype(float)
    return {
        "train_n": int(len(values)),
        "residual_mean": mean,
        "residual_sd": sd,
        "residual_p10": float(p10),
        "residual_p20": float(p20),
        "residual_p25": float(p25),
        "residual_minus_1sd": mean - sd,
        "primary_threshold": float(p20),
    }


def apply_gap_threshold(residuals: pd.Series, threshold: float) -> pd.Series:
    """Apply the inclusive, fold-frozen residual cutoff without re-estimation."""
    return residuals.le(float(threshold)).astype("int8")


def construct_gap_labels(
    frame: pd.DataFrame,
    thresholds: dict[str, float],
) -> pd.DataFrame:
    """Add primary/sensitivity labels and p20 margin on a copy of target rows."""
    if "alignment_residual" not in frame:
        raise ValueError("alignment_residual is required to construct gap labels")
    required = set(THRESHOLD_COLUMNS) - set(thresholds)
    if required:
        raise ValueError(f"Gap thresholds are missing: {sorted(required)}")
    result = frame.copy()
    for name, label in THRESHOLD_COLUMNS.items():
        result[label] = apply_gap_threshold(result.alignment_residual, thresholds[name])
    result["primary_threshold"] = float(thresholds["p20"])
    result["gap_margin"] = result.alignment_residual - result["primary_threshold"]
    return result


def construct_t_plus_3_pairs(
    panel_keys: pd.DataFrame,
    *,
    predictor_start_year: int,
    predictor_end_year: int,
) -> pd.DataFrame:
    """Return exact same-CBSA/same-sector t→t+3 keys in the requested predictor window."""
    pairs = build_temporal_pairs(panel_keys)
    return pairs[
        pairs.predictor_year.between(predictor_start_year, predictor_end_year)
    ].reset_index(drop=True)


def summarize_gap_prevalence(
    frame: pd.DataFrame,
    *,
    group_columns: tuple[str, ...] = (),
    label_column: str = "gap_p20",
) -> pd.DataFrame:
    """Summarize natural prevalence without balancing or dropping absent classes."""
    if label_column not in frame:
        raise ValueError(f"Gap label is absent: {label_column}")
    if not group_columns:
        groups = [((), frame)]
    else:
        grouped = frame.groupby(list(group_columns), dropna=False, observed=True, sort=True)
        groups = list(grouped)
    rows: list[dict[str, object]] = []
    for keys, sample in groups:
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_columns, keys))
        n = int(sample[label_column].notna().sum())
        gap_n = int(sample[label_column].sum())
        row.update({"eligible_n": n, "gap_n": gap_n, "non_gap_n": n - gap_n,
                    "gap_prevalence": gap_n / n if n else float("nan")})
        rows.append(row)
    return pd.DataFrame(rows)


def compare_gap_definitions(
    frame: pd.DataFrame,
    *,
    group_columns: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Return long-form prevalence summaries for p10, p20, p25, and mean-minus-SD."""
    outputs = []
    for definition, label in THRESHOLD_COLUMNS.items():
        summary = summarize_gap_prevalence(frame, group_columns=group_columns, label_column=label)
        summary.insert(0, "threshold_definition", definition)
        outputs.append(summary)
    return pd.concat(outputs, ignore_index=True)


def validate_gap_target(
    frame: pd.DataFrame,
    *,
    max_development_target_year: int = 2020,
    horizon: int = PREDICTION_HORIZON_YEARS,
) -> None:
    """Assert exact temporal alignment, binary natural labels, and no holdout rows."""
    required = {"cbsa_code", "sector_code", "predictor_year", "target_year", "gap_p20"}
    absent = sorted(required - set(frame.columns))
    if absent:
        raise ValueError(f"Target-pair fields are absent: {absent}")
    if not frame.target_year.eq(frame.predictor_year + horizon).all():
        raise ValueError(f"Target pairs must use exact calendar t+{horizon}")
    if int(frame.target_year.max()) > max_development_target_year:
        raise ValueError("Final-holdout outcomes are prohibited in development target outputs")
    if not frame.gap_p20.dropna().isin([0, 1]).all():
        raise ValueError("Primary gap target must be binary")
    pair_keys = ["fold", "split_role", "cbsa_code", "sector_code", "predictor_year", "target_year"]
    if set(pair_keys).issubset(frame.columns) and frame.duplicated(pair_keys).any():
        raise ValueError("Duplicate target pairs found within a fold and split role")
