"""Synthetic reviewer execution path for Assignment 6 orchestration checks."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from regional_entrepreneurship_intelligence.database.connection import PROJECT_ROOT
from regional_entrepreneurship_intelligence.models.baseline import (
    MODEL_FEATURES,
    build_predictor_pairs,
    fit_logistic_baseline,
    predict_gap_probability,
)
from regional_entrepreneurship_intelligence.models.expected import (
    fit_expected_model,
    predict_expected,
)
from regional_entrepreneurship_intelligence.models.features import validate_feature_timing
from regional_entrepreneurship_intelligence.models.gap import (
    calculate_gap_thresholds,
    construct_gap_labels,
    construct_t_plus_3_pairs,
)
from regional_entrepreneurship_intelligence.models.temporal import (
    TemporalDesign,
    generate_sample_fold_spec,
)
from regional_entrepreneurship_intelligence.review.build_reviewer_fixture import (
    DEFAULT_DATABASE,
    REVIEW_DIR,
    build,
)


REVIEWER_WARNING = (
    "Synthetic reviewer fixture — execution-path validation only. "
    "Performance metrics are not interpretable."
)
REVIEWER_TEMPORAL_DESIGN = TemporalDesign(
    development_predictor_years=(2018, 2019),
    holdout_predictor_years=(2020,),
    horizon=3,
    label="synthetic_reviewer",
)
DEFAULT_OUTPUT_DIR = REVIEW_DIR / "assignment6"
REVIEWER_EXPECTED_FEATURES = (
    "startup_rate_lag1",
    "employment_growth",
    "sector_code",
    "year",
)
REVIEWER_EXPECTED_FORMULA = (
    "startup_rate ~ startup_rate_lag1 + employment_growth + C(sector_code) + year"
)


def _load_panel(database_path: Path) -> pd.DataFrame:
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA query_only = ON")
        return pd.read_sql_query(
            "SELECT * FROM v_analytics_msa_industry_year "
            "ORDER BY cbsa_code, sector_code, year",
            connection,
        )
    finally:
        connection.close()


def _gap_thresholds(summary: dict[str, float | int]) -> dict[str, float]:
    return {
        "p10": float(summary["residual_p10"]),
        "p20": float(summary["residual_p20"]),
        "p25": float(summary["residual_p25"]),
        "mean_minus_1sd": float(summary["residual_minus_1sd"]),
    }


def run_reviewer_assignment6(
    *,
    database_path: Path = DEFAULT_DATABASE,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    source_dir: Path | None = None,
    temporal_design: TemporalDesign = REVIEWER_TEMPORAL_DESIGN,
) -> dict[str, object]:
    """Build and run the small synthetic A6 path without production outputs."""
    database_path = Path(database_path)
    output_dir = Path(output_dir)
    resolved_database = database_path.resolve()
    resolved_output = output_dir.resolve()
    production_database_dir = (PROJECT_ROOT / "database").resolve()
    if resolved_database.is_relative_to(production_database_dir):
        raise ValueError("Reviewer mode cannot write inside the production database directory")
    if not resolved_output.is_relative_to(resolved_database.parent):
        raise ValueError("Reviewer outputs must remain under the reviewer database directory")
    fixture = build(database_path, source_dir) if source_dir is not None else build(database_path)
    panel = _load_panel(database_path)
    available_years = set(pd.to_numeric(panel.year, errors="raise").astype(int))
    temporal_design.validate(available_years)
    folds = generate_sample_fold_spec(temporal_design)

    predictive_features = MODEL_FEATURES["baseline_1_simple"]
    validate_feature_timing(list(predictive_features))
    validate_feature_timing(list(REVIEWER_EXPECTED_FEATURES))

    expected_training = panel[panel.year.le(max(temporal_design.holdout_predictor_years))].copy()
    expected_model = fit_expected_model(
        expected_training,
        name="synthetic_reviewer",
        training_year_end=max(temporal_design.holdout_predictor_years),
        features=REVIEWER_EXPECTED_FEATURES,
        formula=REVIEWER_EXPECTED_FORMULA,
    )
    target_years = {
        *temporal_design.development_target_years,
        *temporal_design.holdout_target_years,
    }
    target_residuals = predict_expected(expected_model, panel[panel.year.isin(target_years)])
    target_residuals = target_residuals.rename(
        columns={"year": "target_year", "residual": "alignment_residual"}
    )
    development_residuals = target_residuals[
        target_residuals.target_year.isin(temporal_design.development_target_years)
    ]
    threshold_summary = calculate_gap_thresholds(development_residuals.alignment_residual)
    all_predictor_years = (
        *temporal_design.development_predictor_years,
        *temporal_design.holdout_predictor_years,
    )
    pairs = construct_t_plus_3_pairs(
        panel[["cbsa_code", "sector_code", "year"]],
        predictor_start_year=min(all_predictor_years),
        predictor_end_year=max(all_predictor_years),
    )
    labeled = pairs.merge(
        target_residuals[["cbsa_code", "sector_code", "target_year", "alignment_residual"]],
        on=["cbsa_code", "sector_code", "target_year"],
        how="inner",
        validate="one_to_one",
    )
    labeled = construct_gap_labels(labeled, _gap_thresholds(threshold_summary))
    modeled = build_predictor_pairs(
        labeled,
        panel[panel.year.le(max(all_predictor_years))],
        max_predictor_year=max(all_predictor_years),
    )
    required = ["gap_p20", *predictive_features]
    modeled = modeled.dropna(subset=required).copy()
    development = modeled[
        modeled.predictor_year.isin(temporal_design.development_predictor_years)
    ].copy()
    holdout = modeled[
        modeled.predictor_year.isin(temporal_design.holdout_predictor_years)
    ].copy()
    if development.gap_p20.nunique() != 2:
        counts = development.gap_p20.value_counts().sort_index().to_dict()
        raise ValueError(
            "Synthetic reviewer development rows must exercise both target classes; "
            f"observed {counts}"
        )
    if development.empty or holdout.empty:
        raise ValueError("Synthetic reviewer design requires nonempty development and holdout rows")

    classifier = fit_logistic_baseline(development, model="baseline_1_simple")
    holdout["synthetic_gap_probability"] = predict_gap_probability(classifier, holdout)
    prediction_columns = [
        "cbsa_code",
        "sector_code",
        "predictor_year",
        "target_year",
        "gap_p20",
        "synthetic_gap_probability",
    ]
    predictions = holdout[prediction_columns].sort_values(
        ["cbsa_code", "sector_code", "predictor_year"]
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = output_dir / "reviewer_predictions.csv"
    design_path = output_dir / "temporal_design.json"
    summary_path = output_dir / "execution_summary.json"
    predictions.to_csv(predictions_path, index=False)
    design_payload = {
        "label": temporal_design.label,
        "development_predictor_years": list(temporal_design.development_predictor_years),
        "development_target_years": list(temporal_design.development_target_years),
        "holdout_predictor_years": list(temporal_design.holdout_predictor_years),
        "holdout_target_years": list(temporal_design.holdout_target_years),
        "horizon": temporal_design.horizon,
        "folds": [fold.__dict__ for fold in folds],
    }
    design_path.write_text(json.dumps(design_payload, indent=2) + "\n", encoding="utf-8")
    summary = {
        "warning": REVIEWER_WARNING,
        "source": "reviewer",
        "fixture_label": fixture["label"],
        "fixture_years": fixture["year_min_max"],
        "development_rows": int(len(development)),
        "holdout_rows": int(len(holdout)),
        "development_classes": sorted(int(value) for value in development.gap_p20.unique()),
        "feature_registry_validated": True,
        "exact_horizon_validated": bool(
            modeled.target_year.eq(modeled.predictor_year + temporal_design.horizon).all()
        ),
        "outputs": {
            "predictions": str(predictions_path),
            "temporal_design": str(design_path),
            "summary": str(summary_path),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
