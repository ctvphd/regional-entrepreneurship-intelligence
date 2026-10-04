"""Leakage-safe logistic baseline utilities for Assignment 6.4."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm

TARGET = "gap_p20"
CORE_NUMERIC = ("startup_rate", "startup_rate_lag1", "employment_growth")
REGIONAL_NUMERIC = (
    "acs_population_growth",
    "median_household_income",
    "educational_attainment_pct",
    "labor_force_participation_pct",
    "unemployment_rate",
)
MODEL_FEATURES = {
    "baseline_1_simple": CORE_NUMERIC + ("sector_code", "year"),
    "baseline_2_extended": CORE_NUMERIC + REGIONAL_NUMERIC + ("sector_code", "year"),
    "baseline_2_no_startup_lag1": ("startup_rate", "employment_growth") + REGIONAL_NUMERIC + ("sector_code", "year"),
    "baseline_2_no_employment_growth": ("startup_rate", "startup_rate_lag1") + REGIONAL_NUMERIC + ("sector_code", "year"),
    "baseline_1_no_sector": CORE_NUMERIC + ("year",),
    "baseline_1_no_time": CORE_NUMERIC + ("sector_code",),
}
EXTENDED_REQUIRED = MODEL_FEATURES["baseline_2_extended"]


@dataclass
class LogisticFit:
    model: str
    result: object
    columns: tuple[str, ...]
    numeric_means: dict[str, float]
    numeric_scales: dict[str, float]
    sector_levels: tuple[str, ...]
    numeric_features: tuple[str, ...]


def build_predictor_pairs(target_pairs: pd.DataFrame, predictor_panel: pd.DataFrame) -> pd.DataFrame:
    """Attach only the predictor-year panel row to each A6.3 labeled pair."""
    keys = ["cbsa_code", "sector_code", "predictor_year"]
    panel = predictor_panel.copy()
    panel["predictor_year"] = panel["year"]
    for key in ("cbsa_code", "sector_code"):
        panel[key] = panel[key].astype(str)
    if panel.duplicated(keys).any():
        raise ValueError("Predictor panel has duplicate MSA-sector-year keys")
    feature_columns = list(dict.fromkeys([*keys, "acs_population", *sum((list(v) for v in MODEL_FEATURES.values()), [])]))
    absent = sorted(set(feature_columns) - set(panel.columns))
    if absent:
        raise ValueError(f"Predictor panel is missing registered fields: {absent}")
    feature_panel = panel[feature_columns].copy()
    if not feature_panel.predictor_year.le(2017).all():
        raise ValueError("Holdout predictor years must not enter A6.4 development features")
    left = target_pairs.copy()
    left["predictor_year"] = pd.to_numeric(left.predictor_year, errors="raise").astype(int)
    for key in ("cbsa_code", "sector_code"):
        left[key] = left[key].astype(str)
    merged = left.merge(feature_panel, on=keys, how="left", validate="many_to_one", suffixes=("", "_feature"))
    if merged["year"].isna().any():
        raise ValueError("Some target pairs lack an exact predictor-year panel row")
    if not merged.year.eq(merged.predictor_year).all():
        raise ValueError("A predictor feature did not come from its declared predictor year")
    return merged


def complete_predictor_sample(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Use a common Baseline-2-complete sample for paired model comparison."""
    finite = frame.loc[:, list(EXTENDED_REQUIRED)].replace([np.inf, -np.inf], np.nan)
    included = finite.notna().all(axis=1)
    audit = frame.copy()
    audit["model_feature_complete"] = included
    audit["additional_feature_missing"] = ~included
    return frame.loc[included].copy(), audit


def fit_prevalence_baseline(training_labels: pd.Series) -> float:
    """Estimate the natural training-fold prevalence and nothing else."""
    values = pd.to_numeric(training_labels, errors="raise")
    if values.empty or not values.isin([0, 1]).all():
        raise ValueError("Training labels must be nonempty and binary")
    return float(values.mean())


def validate_oof_predictions(frame: pd.DataFrame) -> None:
    """Require one exact-horizon, development-only prediction per validation key."""
    keys = ["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"]
    missing = sorted(set(keys + ["actual_gap"]) - set(frame.columns))
    if missing:
        raise ValueError(f"OOF prediction fields are missing: {missing}")
    if frame.duplicated(keys).any():
        raise ValueError("Pooled OOF predictions contain duplicate fold/key rows")
    if not frame.target_year.eq(frame.predictor_year + 3).all() or int(frame.target_year.max()) > 2020:
        raise ValueError("OOF predictions must be exact t+3 development observations only")
    if not frame.actual_gap.isin([0, 1]).all():
        raise ValueError("OOF outcomes must retain the binary natural label")


def _design(
    frame: pd.DataFrame, fit: LogisticFit | None = None, *, model_name: str | None = None
) -> tuple[pd.DataFrame, dict, dict, tuple[str, ...]]:
    model = fit.model if fit else model_name
    if model is None:
        raise ValueError("A logistic specification is required")
    model_features = MODEL_FEATURES[model]
    trained = fit is not None and fit.result is not None
    numeric = tuple(name for name in model_features if name not in {"sector_code", "year"})
    values = frame.copy()
    if not trained:
        means = {name: float(pd.to_numeric(values[name]).mean()) for name in numeric}
        scales = {name: float(pd.to_numeric(values[name]).std(ddof=0)) or 1.0 for name in numeric}
        sector_levels = tuple(sorted(values.sector_code.astype(str).unique())) if "sector_code" in model_features else ()
    else:
        means, scales, sector_levels = fit.numeric_means, fit.numeric_scales, fit.sector_levels
    result = pd.DataFrame(index=values.index)
    result["const"] = 1.0
    for name in numeric:
        result[name] = (pd.to_numeric(values[name]).astype(float) - means[name]) / scales[name]
    if "year" in model_features:
        year_values = pd.to_numeric(values.year).astype(float)
        mean = float(fit.numeric_means["__year__"]) if trained else float(year_values.mean())
        scale = float(fit.numeric_scales["__year__"]) if trained else (float(year_values.std(ddof=0)) or 1.0)
        result["year_trend"] = (year_values - mean) / scale
        if not trained:
            means["__year__"], scales["__year__"] = mean, scale
    if "sector_code" in model_features:
        sectors = pd.Categorical(values.sector_code.astype(str), categories=sector_levels)
        encoded = pd.get_dummies(sectors, prefix="sector", dtype=float)
        if sector_levels:
            encoded = encoded.drop(columns=f"sector_{sector_levels[0]}", errors="ignore")
        result = pd.concat([result, encoded.set_axis(values.index)], axis=1)
    return result.astype(float), means, scales, sector_levels


def fit_logistic_baseline(training: pd.DataFrame, *, model: str) -> LogisticFit:
    """Fit ridge-stabilized binomial logistic regression on training rows only."""
    if model not in MODEL_FEATURES:
        raise ValueError(f"Unknown logistic baseline: {model}")
    y = pd.to_numeric(training[TARGET], errors="raise").astype(int)
    if y.nunique() < 2:
        raise ValueError("Logistic training fold must contain both target classes")
    placeholder = LogisticFit(model, None, (), {}, {}, (), ())
    x, means, scales, sectors = _design(training, model_name=model)
    if not np.isfinite(x.to_numpy()).all():
        raise ValueError("Non-finite training design matrix")
    # A tiny L2 penalty stabilizes rare/separated sector cells without reweighting classes.
    result = sm.GLM(y, x, family=sm.families.Binomial()).fit_regularized(alpha=1e-5, L1_wt=0.0, maxiter=500)
    return LogisticFit(model, result, tuple(x.columns), means, scales, sectors,
                       tuple(name for name in MODEL_FEATURES[model] if name not in {"sector_code", "year"}))


def predict_gap_probability(model: LogisticFit, frame: pd.DataFrame) -> np.ndarray:
    """Score validation rows with training-fitted numeric transforms and categories."""
    x, _, _, _ = _design(frame, model)
    x = x.reindex(columns=model.columns, fill_value=0.0)
    probabilities = np.asarray(model.result.predict(x), dtype=float)
    return np.clip(probabilities, 0.0, 1.0)


def probability_metrics(actual: pd.Series | np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    """Compute AP, rank ROC-AUC, and Brier score without optional ML dependencies."""
    y = np.asarray(actual, dtype=int)
    p = np.asarray(probabilities, dtype=float)
    if len(y) != len(p) or not len(y) or not np.isin(y, [0, 1]).all():
        raise ValueError("Metric inputs must be aligned, nonempty, and binary")
    positives = int(y.sum())
    grouped = pd.DataFrame({"actual": y, "probability": p}).groupby("probability", sort=False).agg(
        positives=("actual", "sum"), n=("actual", "size")
    ).sort_index(ascending=False)
    cumulative_tp = grouped.positives.cumsum().to_numpy()
    cumulative_n = grouped.n.cumsum().to_numpy()
    precision_at_threshold = cumulative_tp / cumulative_n
    recall_increments = grouped.positives.to_numpy() / positives if positives else np.zeros(len(grouped))
    average_precision = float(np.sum(precision_at_threshold * recall_increments)) if positives else float("nan")
    ranks = pd.Series(p).rank(method="average").to_numpy()
    negatives = len(y) - positives
    roc_auc = float((ranks[y == 1].sum() - positives * (positives + 1) / 2) / (positives * negatives)) if positives and negatives else float("nan")
    return {"pr_auc": average_precision, "roc_auc": roc_auc, "brier_score": float(np.mean((p - y) ** 2))}


def ranking_curve(actual: pd.Series | np.ndarray, probabilities: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return tie-aware PR and ROC threshold coordinates."""
    frame = pd.DataFrame({"actual": np.asarray(actual, dtype=int), "probability": probabilities})
    grouped = frame.groupby("probability", sort=False).agg(
        positives=("actual", "sum"), n=("actual", "size")
    ).sort_index(ascending=False)
    tp = np.r_[0, grouped.positives.cumsum().to_numpy()]
    fp = np.r_[0, (grouped.n - grouped.positives).cumsum().to_numpy()]
    positive_n = max(1, int(frame.actual.sum()))
    negative_n = max(1, len(frame) - int(frame.actual.sum()))
    recall = tp / positive_n
    precision = np.divide(tp, tp + fp, out=np.ones_like(tp, dtype=float), where=(tp + fp) > 0)
    return recall, precision, fp / negative_n, recall


def threshold_metrics(actual: pd.Series | np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, float | int]:
    y = np.asarray(actual, dtype=int)
    predicted = np.asarray(probabilities) >= float(threshold)
    tp = int(np.sum(predicted & (y == 1)))
    fp = int(np.sum(predicted & (y == 0)))
    tn = int(np.sum(~predicted & (y == 0)))
    fn = int(np.sum(~predicted & (y == 1)))
    recall = tp / (tp + fn) if tp + fn else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return {"true_positive": tp, "false_positive": fp, "true_negative": tn, "false_negative": fn,
            "recall": recall, "precision": precision, "f1": f1,
            "balanced_accuracy": (recall + specificity) / 2}


def calibration_table(actual: pd.Series, probabilities: np.ndarray, *, bins: int = 10) -> pd.DataFrame:
    frame = pd.DataFrame({"actual": np.asarray(actual, dtype=int), "probability": probabilities})
    if frame.probability.nunique() == 1:
        frame["risk_bin"] = 1
    else:
        frame["risk_bin"] = pd.qcut(frame.probability, q=min(bins, len(frame)), labels=False, duplicates="drop") + 1
    return frame.groupby("risk_bin", observed=True).agg(
        n=("actual", "size"), mean_predicted_probability=("probability", "mean"),
        observed_gap_prevalence=("actual", "mean"),
    ).reset_index()


def lift_table(actual: pd.Series, probabilities: np.ndarray, *, cuts=(0.10, 0.20, 0.25)) -> pd.DataFrame:
    frame = pd.DataFrame({"actual": np.asarray(actual, dtype=int), "probability": probabilities})
    frame = frame.sort_values("probability", ascending=False, kind="mergesort")
    overall = float(frame.actual.mean())
    rows = []
    for cut in cuts:
        selected_n = max(1, int(np.ceil(len(frame) * cut)))
        if frame.probability.nunique() == 1:
            prevalence = overall
        else:
            boundary = float(frame.iloc[selected_n - 1].probability)
            above = frame[frame.probability > boundary]
            tied = frame[frame.probability.eq(boundary)]
            tie_fraction = (selected_n - len(above)) / len(tied)
            prevalence = float((above.actual.sum() + tie_fraction * tied.actual.sum()) / selected_n)
        rows.append({"risk_cut": cut, "selected_n": selected_n, "observed_gap_prevalence": prevalence,
                     "overall_prevalence": overall, "lift_ratio": prevalence / overall if overall else np.nan})
    return pd.DataFrame(rows)
