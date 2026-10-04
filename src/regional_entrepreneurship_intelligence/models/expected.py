"""Fold-local expected-startup-rate models for Assignment 6.2."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

OUTCOME = "startup_rate"
BASE_FEATURES = (
    "startup_rate_lag1",
    "employment_growth",
    "acs_population_growth",
    "median_household_income",
    "educational_attainment_pct",
    "labor_force_participation_pct",
    "unemployment_rate",
    "sector_code",
    "year",
)
BASE_FORMULA = (
    "startup_rate ~ startup_rate_lag1 + employment_growth + acs_population_growth + "
    "median_household_income + educational_attainment_pct + "
    "labor_force_participation_pct + unemployment_rate + C(sector_code) + C(year)"
)
MODEL_FORMULAS = {
    "A": BASE_FORMULA,
    "B": BASE_FORMULA.replace(
        "+ C(sector_code) + C(year)",
        "+ C(sector_code) + employment_growth:C(sector_code) + C(year)",
    ),
    "C": BASE_FORMULA,
}
MODEL_FEATURES = {
    name: BASE_FEATURES for name in MODEL_FORMULAS
}


@dataclass
class ExpectedModel:
    name: str
    formula: str
    result: object
    training_frame: pd.DataFrame
    training_year_end: int
    estimator: str
    features: tuple[str, ...]


def complete_cases(frame: pd.DataFrame, features: tuple[str, ...]) -> pd.DataFrame:
    required = [OUTCOME, *features]
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"Expected-model fields are absent: {missing}")
    clean = frame.replace([np.inf, -np.inf], np.nan)
    return clean.dropna(subset=required).copy()


def fit_expected_model(
    frame: pd.DataFrame,
    *,
    name: str,
    training_year_end: int,
    features: tuple[str, ...] | None = None,
    formula: str | None = None,
    estimator: str = "ols",
) -> ExpectedModel:
    """Fit only complete observations through the declared temporal cutoff."""
    if name not in MODEL_FORMULAS and (features is None or formula is None):
        raise ValueError(f"Unknown model specification: {name}")
    used_features = features or MODEL_FEATURES[name]
    used_formula = formula or MODEL_FORMULAS[name]
    clean = complete_cases(frame, used_features)
    if clean.empty:
        raise ValueError(f"No complete training observations for {name}")
    if int(clean.year.max()) > training_year_end:
        raise ValueError(
            f"Training data end in {int(clean.year.max())}, after cutoff {training_year_end}"
        )
    if estimator == "ols":
        result = smf.ols(used_formula, data=clean).fit()
    elif estimator == "huber":
        result = smf.rlm(used_formula, data=clean, M=sm.robust.norms.HuberT()).fit()
    else:
        raise ValueError(f"Unsupported estimator: {estimator}")
    return ExpectedModel(name, used_formula, result, clean, training_year_end, estimator, used_features)


def predict_expected(model: ExpectedModel, frame: pd.DataFrame) -> pd.DataFrame:
    """Predict complete rows; unseen validation year effects persist at the last train year."""
    clean = complete_cases(frame, model.features)
    if "C(cbsa_code)" in model.formula and not clean.empty:
        trained_msas = set(model.training_frame.cbsa_code.astype(str))
        clean = clean[clean.cbsa_code.astype(str).isin(trained_msas)].copy()
    if clean.empty:
        clean["expected_startup_rate"] = pd.Series(dtype=float)
        return clean
    prediction_data = clean.copy()
    prediction_data["year"] = prediction_data.year.clip(upper=model.training_year_end)
    clean["expected_startup_rate"] = np.asarray(model.result.predict(prediction_data), dtype=float)
    clean["residual"] = clean[OUTCOME] - clean["expected_startup_rate"]
    return clean


def regression_metrics(
    observed: pd.Series,
    predicted: pd.Series,
    *,
    training_mean: float | None = None,
) -> dict[str, float | int]:
    residual = observed.to_numpy(dtype=float) - predicted.to_numpy(dtype=float)
    denominator_center = float(observed.mean()) if training_mean is None else training_mean
    denominator = float(np.square(observed.to_numpy(dtype=float) - denominator_center).sum())
    sse = float(np.square(residual).sum())
    return {
        "n": int(len(residual)),
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(np.square(residual)))),
        "r_squared": 1 - sse / denominator if denominator > 0 else float("nan"),
        "mean_residual": float(np.mean(residual)),
        "median_residual": float(np.median(residual)),
        "residual_sd": float(np.std(residual, ddof=1)) if len(residual) > 1 else float("nan"),
        "residual_p05": float(np.quantile(residual, 0.05)),
        "residual_p95": float(np.quantile(residual, 0.95)),
        "expected_below_zero_n": int((predicted < 0).sum()),
    }
