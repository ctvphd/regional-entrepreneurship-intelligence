"""Frozen Assignment 6.1 modeling-design constants and validation only."""

from __future__ import annotations

PRIMARY_OUTCOME = "startup_rate"
PRIMARY_GROWTH = "employment_growth"
ALIGNMENT_FORMULA = "observed_startup_rate - expected_startup_rate"
PREDICTION_HORIZON_YEARS = 3
PRIMARY_GAP_QUANTILE = 0.20
GAP_THRESHOLD_SCOPE = "training_fold_only"
ROBUSTNESS_GAP_QUANTILES = (0.10, 0.25)
ROBUSTNESS_GAP_RULES = ("bottom_10", "bottom_25", "below_training_mean_minus_1sd")
GAP_THRESHOLD_OPERATOR = "less_than_or_equal"
EXPECTED_MODEL_SECTOR_EFFECTS = "mandatory"
EXPECTED_MODEL_YEAR_EFFECTS = "mandatory"
EXPECTED_MODEL_MSA_EFFECTS = "sensitivity_only"
PRIMARY_VALIDATION = "expanding_window_temporal"
PRIMARY_METRIC = "average_precision"


def validate_modeling_design() -> dict[str, object]:
    """Validate the frozen design constants without fitting or labeling data."""
    if PRIMARY_OUTCOME != "startup_rate" or PRIMARY_GROWTH != "employment_growth":
        raise ValueError("The A6.1 primary outcome or growth measure changed")
    if PREDICTION_HORIZON_YEARS != 3 or PRIMARY_GAP_QUANTILE != 0.20:
        raise ValueError("The A6.1 primary horizon or gap threshold changed")
    if GAP_THRESHOLD_SCOPE != "training_fold_only":
        raise ValueError("Gap threshold must be calculated from training residuals only")
    if EXPECTED_MODEL_SECTOR_EFFECTS != "mandatory" or EXPECTED_MODEL_YEAR_EFFECTS != "mandatory":
        raise ValueError("Sector and year effects are mandatory in the primary expected model")
    if EXPECTED_MODEL_MSA_EFFECTS != "sensitivity_only":
        raise ValueError("MSA fixed effects are sensitivity-only")
    return {
        "primary_outcome": PRIMARY_OUTCOME,
        "primary_growth": PRIMARY_GROWTH,
        "alignment_formula": ALIGNMENT_FORMULA,
        "horizon_years": PREDICTION_HORIZON_YEARS,
        "primary_gap_quantile": PRIMARY_GAP_QUANTILE,
        "gap_threshold_scope": GAP_THRESHOLD_SCOPE,
        "robustness_gap_quantiles": ROBUSTNESS_GAP_QUANTILES,
        "robustness_gap_rules": ROBUSTNESS_GAP_RULES,
        "gap_threshold_operator": GAP_THRESHOLD_OPERATOR,
        "validation": PRIMARY_VALIDATION,
        "primary_metric": PRIMARY_METRIC,
        "model_fitting_performed": False,
        "gap_labels_created": False,
    }
