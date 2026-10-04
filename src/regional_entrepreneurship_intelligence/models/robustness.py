"""Reusable safeguards and summaries for Assignment 6.6 sensitivities."""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from regional_entrepreneurship_intelligence.models.baseline import (
    lift_table,
    probability_metrics,
)


def deterministic_geography_split(codes: pd.Series, *, test_fraction: float = 0.20) -> pd.DataFrame:
    """Assign stable CBSA codes to train/test using a version-independent hash."""
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be strictly between zero and one")
    unique = sorted(pd.Series(codes).dropna().astype(str).unique())
    threshold = int(test_fraction * 10_000)
    rows = []
    for code in unique:
        bucket = int(hashlib.sha256(code.encode("utf-8")).hexdigest()[:8], 16) % 10_000
        rows.append({"cbsa_code": code, "geography_role": "test" if bucket < threshold else "train", "hash_bucket": bucket})
    return pd.DataFrame(rows)


def validate_geography_disjoint(split: pd.DataFrame) -> None:
    roles = split.groupby("cbsa_code").geography_role.nunique()
    if roles.gt(1).any() or split.cbsa_code.duplicated().any():
        raise ValueError("Each CBSA must have exactly one geographic role")


def label_agreement(primary: pd.Series, alternative: pd.Series) -> dict[str, float | int]:
    left = np.asarray(primary, dtype=int)
    right = np.asarray(alternative, dtype=int)
    if len(left) != len(right) or not len(left) or not np.isin(left, [0, 1]).all() or not np.isin(right, [0, 1]).all():
        raise ValueError("Label agreement requires aligned nonempty binary arrays")
    union = int(np.sum((left == 1) | (right == 1)))
    intersection = int(np.sum((left == 1) & (right == 1)))
    return {
        "n": len(left),
        "agreement": float(np.mean(left == right)),
        "positive_jaccard": intersection / union if union else 1.0,
        "cohen_kappa": float(cohen_kappa_score(left, right)),
        "primary_positive_n": int(left.sum()),
        "alternative_positive_n": int(right.sum()),
    }


def classification_summary(actual, probabilities: np.ndarray) -> dict[str, float | int]:
    metrics = probability_metrics(actual, probabilities)
    lift = lift_table(pd.Series(np.asarray(actual, dtype=int)), probabilities, cuts=(0.10, 0.20, 0.25))
    values = {f"top{int(row.risk_cut * 100)}_lift": float(row.lift_ratio) for row in lift.itertuples(index=False)}
    values["prevalence"] = float(np.mean(actual))
    return {**metrics, **values}


def standardized_mean_difference(included: pd.Series, excluded: pd.Series) -> float:
    a = pd.to_numeric(included, errors="coerce").dropna().to_numpy(dtype=float)
    b = pd.to_numeric(excluded, errors="coerce").dropna().to_numpy(dtype=float)
    if not len(a) or not len(b):
        return float("nan")
    pooled_sd = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2) if len(a) > 1 and len(b) > 1 else 0.0
    if pooled_sd == 0:
        return 0.0 if np.mean(a) == np.mean(b) else float("inf")
    return float((np.mean(a) - np.mean(b)) / pooled_sd)


def clip_from_training(training: pd.Series, validation: pd.Series, *, lower: float = .01, upper: float = .99):
    """Return copies clipped at quantiles estimated only from training values."""
    if not 0 <= lower < upper <= 1:
        raise ValueError("Invalid clipping quantiles")
    bounds = pd.to_numeric(training, errors="coerce").quantile([lower, upper])
    low, high = float(bounds.iloc[0]), float(bounds.iloc[1])
    return training.clip(low, high), validation.clip(low, high), low, high


def exclude_calendar_year_pairs(frame: pd.DataFrame, years: set[int]) -> pd.DataFrame:
    required = {"predictor_year", "target_year"}
    if not required.issubset(frame.columns):
        raise ValueError("Calendar sensitivity requires predictor_year and target_year")
    return frame.loc[~frame.predictor_year.isin(years) & ~frame.target_year.isin(years)].copy()


def assert_development_only(frame: pd.DataFrame, *, max_predictor_year: int = 2017, max_target_year: int = 2020) -> None:
    if frame.empty or int(frame.predictor_year.max()) > max_predictor_year or int(frame.target_year.max()) > max_target_year:
        raise ValueError("Robustness rows crossed the locked development temporal boundary")


def assign_population_terciles(training_population: pd.Series, validation_population: pd.Series) -> tuple[pd.Series, np.ndarray]:
    cutpoints = pd.to_numeric(training_population, errors="coerce").dropna().quantile([1 / 3, 2 / 3]).to_numpy()
    if len(cutpoints) != 2 or not np.isfinite(cutpoints).all() or cutpoints[0] >= cutpoints[1]:
        raise ValueError("Training populations do not support distinct tercile cutpoints")
    groups = pd.cut(pd.to_numeric(validation_population, errors="coerce"),
                    [-np.inf, cutpoints[0], cutpoints[1], np.inf],
                    labels=["lower_third", "middle_third", "upper_third"], include_lowest=True)
    return groups, cutpoints


def sector_sufficiency(event_count: int, *, minimum_events: int = 30) -> bool:
    if minimum_events < 1:
        raise ValueError("minimum_events must be positive")
    return int(event_count) >= minimum_events


def attach_predictor_year_fields(pairs: pd.DataFrame, panel: pd.DataFrame, fields: tuple[str, ...]) -> pd.DataFrame:
    """Attach sensitivity measures strictly by CBSA-sector-predictor-year key."""
    required_pairs = {"cbsa_code", "sector_code", "predictor_year", "target_year"}
    if not required_pairs.issubset(pairs.columns) or not {"cbsa_code", "sector_code", "year", *fields}.issubset(panel.columns):
        raise ValueError("Pair/panel fields are incomplete for predictor-year attachment")
    if not pairs.target_year.eq(pairs.predictor_year + 3).all():
        raise ValueError("Sensitivity pairs must preserve exact t+3")
    right = panel[["cbsa_code", "sector_code", "year", *fields]].copy().rename(columns={"year": "predictor_year"})
    for col in ("cbsa_code", "sector_code"):
        right[col] = right[col].astype(str)
    if right.duplicated(["cbsa_code", "sector_code", "predictor_year"]).any():
        raise ValueError("Predictor panel has duplicate sensitivity keys")
    left = pairs.copy()
    for col in ("cbsa_code", "sector_code"):
        left[col] = left[col].astype(str)
    merged = left.merge(right, on=["cbsa_code", "sector_code", "predictor_year"], how="left",
                        validate="many_to_one", suffixes=("", "_predictor"))
    if merged.loc[:, list(fields)].isna().all(axis=None):
        raise ValueError("No sensitivity measures matched predictor-year pairs")
    return merged
