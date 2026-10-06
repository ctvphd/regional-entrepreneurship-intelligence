"""Pure filtering and display shaping for the A7.2 Explorer artifacts."""

from __future__ import annotations

import pandas as pd

PANEL_KEY = ["cbsa_code", "sector_code", "year"]
PREDICTION_KEY = ["cbsa_code", "sector_code", "predictor_year"]
PANEL_FIELDS = [
    "cbsa_code", "msa_name", "sector_code", "sector_name", "year", "startup_rate",
    "expected_startup_rate", "alignment_residual", "alignment_label",
    "observed_historical_gap_status", "gap_label_predictor_year", "employment_growth",
    "coverage_status", "msa_observation_count", "msa_sector_count", "msa_year_count",
    "has_suppression", "source_quality_notes",
]
class ExplorerDataError(ValueError):
    """Raised when dashboard-ready Explorer artifacts violate their contract."""


def validate_explorer_inputs(panel: pd.DataFrame, predictions: pd.DataFrame, horizon: int = 3) -> None:
    panel_required = set(PANEL_FIELDS)
    prediction_required = set(PREDICTION_KEY + ["target_year", "development_or_holdout", "actual_gap", "logistic_probability", "hgb_probability", "coverage_status"])
    missing_panel = sorted(panel_required - set(panel.columns))
    missing_predictions = sorted(prediction_required - set(predictions.columns))
    if missing_panel:
        raise ExplorerDataError(f"dashboard_msa_industry_year.parquet missing fields: {missing_panel}")
    if missing_predictions:
        raise ExplorerDataError(f"dashboard_model_predictions.parquet missing fields: {missing_predictions}")
    if panel[PANEL_KEY].isna().any().any() or panel.duplicated(PANEL_KEY).any():
        raise ExplorerDataError("dashboard_msa_industry_year.parquet keys must be non-null and unique")
    if predictions[PREDICTION_KEY].isna().any().any() or predictions.duplicated(PREDICTION_KEY).any():
        raise ExplorerDataError("dashboard_model_predictions.parquet prediction keys must be non-null and unique")
    if not (predictions["target_year"].astype(int) == predictions["predictor_year"].astype(int) + int(horizon)).all():
        raise ExplorerDataError("dashboard_model_predictions.parquet contains a non-exact forecast horizon")
    if not predictions["development_or_holdout"].isin(["development_oof", "final_holdout"]).all():
        raise ExplorerDataError("dashboard_model_predictions.parquet contains an unapproved evaluation split")
    if not predictions["coverage_status"].isin(["comparison_eligible", "thin"]).all():
        raise ExplorerDataError("dashboard_model_predictions.parquet contains an unapproved coverage status")
    if not predictions["actual_gap"].isin([0, 1]).all():
        raise ExplorerDataError("dashboard_model_predictions.parquet actual_gap must be binary")
    for field in ("logistic_probability", "hgb_probability"):
        values = pd.to_numeric(predictions[field], errors="coerce")
        if values.isna().any() or not values.between(0, 1).all():
            raise ExplorerDataError(f"dashboard_model_predictions.parquet {field} must be finite and in [0, 1]")
    if not panel["coverage_status"].isin(["comparison_eligible", "thin"]).all():
        raise ExplorerDataError("dashboard_msa_industry_year.parquet contains an unapproved coverage status")


def filter_explorer_data(
    panel: pd.DataFrame,
    *,
    msa: str | None = None,
    sectors: list[str] | tuple[str, ...] | None = None,
    year: int | None = None,
    gap_status: int | None = None,
    has_prediction: bool = False,
    predictions: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Filter descriptive panel rows without changing values or imputing nulls."""
    result = panel
    if msa is not None:
        result = result.loc[result["cbsa_code"].astype(str) == str(msa)]
    if sectors:
        result = result.loc[result["sector_code"].astype(str).isin({str(value) for value in sectors})]
    if year is not None:
        if int(year) not in set(panel["year"].astype(int).unique()):
            raise ValueError(f"Descriptive year {year} is not available in dashboard_msa_industry_year")
        result = result.loc[result["year"].astype(int) == int(year)]
    if gap_status is not None:
        result = result.loc[result["observed_historical_gap_status"] == int(gap_status)]
    if has_prediction:
        if predictions is None:
            raise ValueError("predictions are required when has_prediction is enabled")
        keys = predictions.loc[:, PREDICTION_KEY].rename(columns={"predictor_year": "year"})
        result = result.merge(keys.drop_duplicates(), on=PANEL_KEY, how="inner", validate="one_to_one")
    return result.copy()


def attach_prediction_records(panel: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    """Attach each row's explicitly keyed t-to-t+3 evaluation score, if available."""
    fields = PREDICTION_KEY + ["development_or_holdout", "target_year", "actual_gap", "logistic_probability", "hgb_probability"]
    right = predictions[fields].copy()
    right["prediction_predictor_year"] = right["predictor_year"]
    right = right.rename(columns={"predictor_year": "year"})
    return panel.merge(right, on=PANEL_KEY, how="left", validate="one_to_one")


def filter_predictions(
    predictions: pd.DataFrame,
    *,
    split: str,
    predictor_year: int | None,
    msa: str | None = None,
    sectors: list[str] | tuple[str, ...] | None = None,
) -> pd.DataFrame:
    if split not in {"development_oof", "final_holdout"}:
        raise ValueError("split must be development_oof or final_holdout")
    result = predictions.loc[predictions["development_or_holdout"] == split]
    if predictor_year is not None:
        available = set(result["predictor_year"].astype(int).unique())
        if int(predictor_year) not in available:
            raise ValueError(f"Predictor year {predictor_year} is unavailable for {split}")
        result = result.loc[result["predictor_year"].astype(int) == int(predictor_year)]
    if msa is not None:
        result = result.loc[result["cbsa_code"].astype(str) == str(msa)]
    if sectors:
        result = result.loc[result["sector_code"].astype(str).isin({str(value) for value in sectors})]
    return result.copy()


def build_top_risk_ranking(
    predictions: pd.DataFrame,
    *,
    split: str,
    predictor_year: int | None,
    top_n: int,
    msa: str | None = None,
    sectors: list[str] | tuple[str, ...] | None = None,
    labels: dict | None = None,
) -> pd.DataFrame:
    if top_n not in (10, 25, 50):
        raise ValueError("top_n must be 10, 25, or 50")
    rows = filter_predictions(
        predictions, split=split, predictor_year=predictor_year, msa=msa, sectors=sectors
    )
    rows = rows.sort_values(
        ["logistic_probability", "cbsa_code", "sector_code", "predictor_year"],
        ascending=[False, True, True, True], kind="mergesort",
    ).head(top_n)
    gap_labels = (labels or {}).get("gap_status", {})
    actual = rows["actual_gap"].astype(int).astype(str).map(gap_labels)
    actual = actual.map({
        gap_labels.get("1"): "Gap observed",
        gap_labels.get("0"): "No gap observed",
    }).fillna("Unavailable")
    return pd.DataFrame({
        "Rank": range(1, len(rows) + 1),
        "MSA": rows["msa_name"].astype(str).to_numpy(),
        "Industry sector": rows["sector_name"].astype(str).to_numpy(),
        "Predictor year (t)": rows["predictor_year"].astype(int).to_numpy(),
        "Target year (t+3)": rows["target_year"].astype(int).to_numpy(),
        "Predicted gap probability (logistic)": rows["logistic_probability"].astype(float).to_numpy(),
        "Actual target gap (retrospective)": actual.to_numpy(),
        "Coverage status": rows["coverage_status"].astype(str).to_numpy(),
    })


def alignment_interpretation(residual, gap_status) -> str:
    if pd.isna(residual):
        return "Alignment is unavailable for this row; no expectation is extrapolated."
    if not pd.isna(gap_status) and int(gap_status) == 1:
        return "Observed startup activity fell materially below the modeled expectation under the development-defined A6 gap rule."
    if float(residual) < 0:
        if not pd.isna(gap_status):
            return "Observed startup activity was below expectation, but this row was not below the A6 gap threshold."
        return "Observed startup activity was below expectation; the A6 gap label is unavailable for this row."
    if not pd.isna(gap_status):
        return "Observed startup activity was at or above expectation; no A6 gap was observed."
    return "Observed startup activity was at or above expectation; the A6 gap label is unavailable for this row."


def selection_summary(rows: pd.DataFrame, *, msa: str | None, sectors: list[str], year: int) -> str:
    n_rows = len(rows)
    if msa is None:
        place = "all available MSAs"
    else:
        place = str(rows["msa_name"].iloc[0]) if n_rows else "selected MSA"
    n_sectors = rows["sector_code"].nunique()
    if sectors and len(sectors) == 1:
        industry = str(rows["sector_name"].iloc[0]) if n_rows else "selected sector"
        scope = industry
    elif sectors:
        scope = f"{n_sectors} selected sectors"
    else:
        scope = f"{n_sectors} available sectors"
    return f"Showing {n_rows:,} MSA-sector rows for {scope} in {place}, {year}."


def filtered_csv_frame(rows: pd.DataFrame, *, dashboard_version: str, primary_model: str) -> pd.DataFrame:
    columns = [
        "cbsa_code", "msa_name", "sector_code", "sector_name", "year", "startup_rate",
        "expected_startup_rate", "alignment_residual", "alignment_label",
        "observed_historical_gap_status", "gap_label_predictor_year", "development_or_holdout",
        "prediction_predictor_year", "target_year", "logistic_probability", "hgb_probability",
        "actual_gap", "coverage_status", "has_suppression", "source_quality_notes",
    ]
    export = rows.loc[:, [field for field in columns if field in rows.columns]].copy()
    export.insert(0, "dashboard_data_version", dashboard_version)
    export.insert(1, "primary_model", primary_model)
    return export.rename(columns={
        "year": "descriptive_year",
        "development_or_holdout": "prediction_evaluation_split",
        "target_year": "prediction_target_year",
        "logistic_probability": "predicted_gap_probability_logistic",
        "hgb_probability": "predicted_gap_probability_hgb_sensitivity",
        "actual_gap": "actual_target_gap_retrospective",
    })
