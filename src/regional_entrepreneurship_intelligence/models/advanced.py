"""Conservative, fold-safe nonlinear classifiers for Assignment 6.5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import average_precision_score

from regional_entrepreneurship_intelligence.models.baseline import (
    CORE_NUMERIC,
    REGIONAL_NUMERIC,
    probability_metrics,
)
from regional_entrepreneurship_intelligence.models.features import validate_feature_timing

TARGET = "gap_p20"
TREE_FEATURES = CORE_NUMERIC + REGIONAL_NUMERIC + ("sector_code", "year")
NUMERIC_FEATURES = CORE_NUMERIC + REGIONAL_NUMERIC + ("year",)
MODEL_NAMES = ("random_forest", "hist_gradient_boosting")

TUNING_CANDIDATES: dict[str, tuple[dict[str, Any], ...]] = {
    "random_forest": (
        {"n_estimators": 250, "max_depth": None, "min_samples_leaf": 10, "max_features": "sqrt"},
        {"n_estimators": 250, "max_depth": 12, "min_samples_leaf": 10, "max_features": "sqrt"},
        {"n_estimators": 250, "max_depth": None, "min_samples_leaf": 30, "max_features": 0.7},
        {"n_estimators": 250, "max_depth": 12, "min_samples_leaf": 30, "max_features": 0.7},
    ),
    "hist_gradient_boosting": (
        {"max_iter": 120, "learning_rate": 0.05, "max_leaf_nodes": 15, "min_samples_leaf": 30, "l2_regularization": 1.0},
        {"max_iter": 120, "learning_rate": 0.08, "max_leaf_nodes": 31, "min_samples_leaf": 30, "l2_regularization": 1.0},
        {"max_iter": 200, "learning_rate": 0.05, "max_leaf_nodes": 31, "min_samples_leaf": 60, "l2_regularization": 1.0},
        {"max_iter": 200, "learning_rate": 0.08, "max_leaf_nodes": 15, "min_samples_leaf": 60, "l2_regularization": 1.0},
    ),
}

ABLATIONS: dict[str, tuple[str, ...]] = {
    "no_employment_growth": ("employment_growth",),
    "no_acs_controls": REGIONAL_NUMERIC,
    "no_sector": ("sector_code",),
    "no_startup_rate_lag1": ("startup_rate_lag1",),
}


@dataclass
class InnerSplit:
    fit: pd.DataFrame
    validation: pd.DataFrame
    predictor_cutoff: int
    training_outcome_cutoff: int


def validate_tree_features(feature_names: tuple[str, ...] | list[str]) -> None:
    """Validate all predictors against the frozen registry and timing boundary."""
    validate_feature_timing(tuple(feature_names))
    prohibited = {"startup_rate_t_plus_1", "startup_rate_t_plus_2", "startup_rate_t_plus_3",
                  "alignment_residual", "expected_target_startup_rate", "gap_margin", TARGET}
    if prohibited.intersection(feature_names):
        raise ValueError("Target-derived/future fields are prohibited in the tree feature matrix")
    if set(feature_names) != set(TREE_FEATURES):
        raise ValueError("Primary nonlinear models must use the locked A6.4 extended feature families")


def make_inner_temporal_split(training: pd.DataFrame) -> InnerSplit:
    """Reserve the latest predictor year of outer training for inner tuning only."""
    if training.empty or training.predictor_year.nunique() < 2:
        raise ValueError("Inner temporal tuning requires at least two training predictor years")
    cutoff = int(training.predictor_year.max())
    fit = training.loc[training.predictor_year.lt(cutoff)].copy()
    validation = training.loc[training.predictor_year.eq(cutoff)].copy()
    if fit.empty or validation.empty or int(fit.target_year.max()) >= int(validation.target_year.min()):
        raise ValueError("Inner split is not forward in target time")
    return InnerSplit(fit, validation, cutoff, int(fit.target_year.max()))


def _preprocessor(features: tuple[str, ...]) -> ColumnTransformer:
    numeric = [name for name in features if name != "sector_code"]
    transformers = [("numeric", StandardScaler(), numeric)]
    if "sector_code" in features:
        transformers.append(("sector", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["sector_code"]))
    return ColumnTransformer(transformers, remainder="drop", verbose_feature_names_out=False)


def build_advanced_pipeline(model_name: str, params: dict[str, Any], *, features: tuple[str, ...] = TREE_FEATURES) -> Pipeline:
    if model_name not in MODEL_NAMES:
        raise ValueError(f"Unsupported advanced model: {model_name}")
    if not set(features).issubset(TREE_FEATURES) or TARGET in features:
        raise ValueError("Feature ablation contains an unknown or target-derived field")
    seed = 20261004
    if model_name == "random_forest":
        classifier = RandomForestClassifier(
            **params, class_weight=None, bootstrap=True, random_state=seed, n_jobs=1
        )
    else:
        classifier = HistGradientBoostingClassifier(
            **params, early_stopping=False, random_state=seed
        )
    return Pipeline([("preprocess", _preprocessor(features)), ("classifier", classifier)])


def fit_advanced_model(
    training: pd.DataFrame, *, model_name: str, params: dict[str, Any], features: tuple[str, ...] = TREE_FEATURES
) -> Pipeline:
    """Fit preprocessing and classifier only on the supplied fold-training rows."""
    if model_name not in MODEL_NAMES:
        raise ValueError(f"Unsupported advanced model: {model_name}")
    if features == TREE_FEATURES:
        validate_tree_features(features)
    y = pd.to_numeric(training[TARGET], errors="raise").astype(int)
    if y.nunique() != 2:
        raise ValueError("Training fold must contain both natural classes")
    estimator = build_advanced_pipeline(model_name, params, features=features)
    estimator.fit(training.loc[:, list(features)], y)
    return estimator


def predict_gap_probability(estimator: Pipeline, frame: pd.DataFrame, *, features: tuple[str, ...] = TREE_FEATURES) -> np.ndarray:
    probabilities = estimator.predict_proba(frame.loc[:, list(features)])[:, 1]
    return np.clip(np.asarray(probabilities, dtype=float), 0.0, 1.0)


def tune_advanced_model(training: pd.DataFrame, *, model_name: str) -> tuple[dict[str, Any], pd.DataFrame]:
    """Choose a small grid winner using only the last-year inner temporal split."""
    inner = make_inner_temporal_split(training)
    rows = []
    for candidate_id, params in enumerate(TUNING_CANDIDATES[model_name], start=1):
        fitted = fit_advanced_model(inner.fit, model_name=model_name, params=params)
        probabilities = predict_gap_probability(fitted, inner.validation)
        ap = float(average_precision_score(inner.validation[TARGET].astype(int), probabilities))
        rows.append({
            "model": model_name, "candidate_id": candidate_id, "params": repr(params), "inner_ap": ap,
            "inner_fit_n": len(inner.fit), "inner_validation_n": len(inner.validation),
            "inner_predictor_cutoff": inner.predictor_cutoff,
            "inner_fit_target_max": inner.training_outcome_cutoff,
            "inner_validation_target_min": int(inner.validation.target_year.min()),
        })
    results = pd.DataFrame(rows).sort_values(["inner_ap", "candidate_id"], ascending=[False, True]).reset_index(drop=True)
    winner_id = int(results.iloc[0].candidate_id)
    return dict(TUNING_CANDIDATES[model_name][winner_id - 1]), results


def validation_permutation_importance(
    estimator: Pipeline, validation: pd.DataFrame, *, model_name: str, fold: str
) -> pd.DataFrame:
    """Outer-validation permutation importance is diagnostic only, never used for tuning."""
    result = permutation_importance(
        estimator, validation.loc[:, list(TREE_FEATURES)], validation[TARGET].astype(int),
        scoring="average_precision", n_repeats=3, random_state=20261004, n_jobs=1, max_samples=0.5,
    )
    frame = pd.DataFrame({
        "model": model_name, "fold": fold, "feature": TREE_FEATURES,
        "importance_type": "validation_permutation_ap_drop",
        "importance_value": result.importances_mean,
        "importance_sd": result.importances_std,
    })
    frame["rank"] = frame.importance_value.rank(method="min", ascending=False).astype(int)
    return frame.sort_values("rank")


def feature_ablation(model_name: str, features: tuple[str, ...], omitted: tuple[str, ...]) -> tuple[str, ...]:
    if model_name not in MODEL_NAMES or not set(omitted).issubset(features):
        raise ValueError("Invalid model feature ablation")
    remaining = tuple(name for name in features if name not in omitted)
    if not remaining:
        raise ValueError("An ablation cannot remove every predictor")
    return remaining


def validate_advanced_oof(frame: pd.DataFrame) -> None:
    required = {"fold", "cbsa_code", "sector_code", "predictor_year", "target_year", "actual_gap"}
    if not required.issubset(frame.columns):
        raise ValueError(f"OOF fields missing: {sorted(required - set(frame.columns))}")
    keys = ["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"]
    if frame.duplicated(keys).any():
        raise ValueError("Advanced OOF rows must be unique development validation keys")
    if not frame.target_year.eq(frame.predictor_year + 3).all() or int(frame.target_year.max()) > 2020:
        raise ValueError("Advanced OOF artifact crossed the exact-horizon or holdout boundary")
    if not frame.actual_gap.isin([0, 1]).all():
        raise ValueError("Advanced OOF target must retain the unchanged binary gap_p20 label")


def partial_dependence_grid(
    estimator: Pipeline, training: pd.DataFrame, *, model_name: str, features: tuple[str, ...] = TREE_FEATURES,
    variables: tuple[str, ...] = ("startup_rate", "startup_rate_lag1", "employment_growth", "unemployment_rate", "median_household_income", "acs_population_growth"),
    grid_size: int = 12,
) -> pd.DataFrame:
    """Calculate simple marginal probability curves over training support, fold by fold."""
    sample = training.loc[:, list(features)].copy()
    if len(sample) > 2500:
        sample = sample.sample(2500, random_state=20261004)
    rows = []
    for variable in variables:
        quantiles = np.linspace(0.05, 0.95, grid_size)
        grid = np.unique(sample[variable].quantile(quantiles).to_numpy(dtype=float))
        for value in grid:
            changed = sample.copy()
            changed[variable] = value
            rows.append({"model": model_name, "feature": variable, "feature_value": value,
                         "mean_predicted_probability": float(predict_gap_probability(estimator, changed, features=features).mean()),
                         "training_support_min": float(sample[variable].quantile(0.05)),
                         "training_support_max": float(sample[variable].quantile(0.95))})
    return pd.DataFrame(rows)


def evaluate_predictions(actual: pd.Series, probabilities: np.ndarray) -> dict[str, float]:
    return probability_metrics(actual, probabilities)
