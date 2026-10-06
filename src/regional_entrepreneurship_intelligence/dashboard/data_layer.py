"""Build deterministic, read-only dashboard datasets from frozen A6 artifacts."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATABASE = ROOT / "database" / "assignment4_production.sqlite"
TABLE_DIR = ROOT / "reports" / "tables"
OUTPUT_DIR = ROOT / "data" / "dashboard"
QUALITY_DIR = TABLE_DIR

PANEL_COLUMNS = (
    "cbsa_code", "cbsa_name", "sector_code", "sector_title", "year",
    "startup_rate", "startup_rate_lag1", "employment_growth",
    "establishment_growth", "payroll_growth", "wage_growth",
    "acs_population", "acs_population_growth", "median_household_income",
    "educational_attainment_pct", "labor_force_participation_pct", "unemployment_rate",
    "bds_startup_available", "bds_has_suppression", "qcew_has_suppression",
    "qcew_is_complete_county_coverage", "acs_matched", "acs_has_suppression",
    "acs_has_missing_controls", "cbp_matched", "cbp_has_suppression",
    "cbp_is_complete_county_coverage", "has_suppression", "source_quality_notes",
)
KEYS = {
    "dashboard_msa_industry_year": ["cbsa_code", "sector_code", "year"],
    "dashboard_model_predictions": ["cbsa_code", "sector_code", "predictor_year", "target_year"],
    "dashboard_model_summary": ["dataset_split", "model", "metric"],
    "dashboard_calibration": ["dataset_split", "model", "risk_bin"],
    "dashboard_model_by_year": ["predictor_year", "target_year", "model"],
    "dashboard_model_by_sector": ["sector_code", "model"],
    "dashboard_model_by_msa_size": ["msa_size_group", "model"],
    "dashboard_coverage": ["cbsa_code"],
    "dashboard_sources": ["source_name", "dataset"],
}
MODEL_LABELS = {
    "prevalence_benchmark": "Prevalence benchmark",
    "logistic": "Logistic regression",
    "hist_gradient_boosting": "HistGradientBoosting (sensitivity)",
}
METRIC_LABELS = {
    "prevalence": "Observed gap prevalence",
    "AP": "Average Precision (PR-AUC)",
    "ROC_AUC": "ROC-AUC",
    "Brier": "Brier score",
    "recall": "Recall",
    "precision": "Precision",
    "f1": "F1 score",
    "balanced_accuracy": "Balanced accuracy",
    "top10_lift": "Top 10% lift",
    "top20_lift": "Top 20% lift",
    "top25_lift": "Top 25% lift",
}
METRIC_ORDER = {name: i for i, name in enumerate(METRIC_LABELS)}
SUMMARY_METRICS = tuple(METRIC_LABELS)
APPROVED_SECTORS = {
    "11", "21", "22", "23", "31-33", "42", "44-45", "48-49", "51", "52",
    "53", "54", "55", "56", "61", "62", "71", "72", "81",
}


def _read_csv(name: str, *, dtype: dict | None = None) -> pd.DataFrame:
    path = TABLE_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Required finalized A6 artifact is missing: {path}")
    return pd.read_csv(path, dtype=dtype)


def _normalize_codes(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "cbsa_code" in result:
        result["cbsa_code"] = result.cbsa_code.astype("string").str.zfill(5)
    if "sector_code" in result:
        result["sector_code"] = result.sector_code.astype("string")
    return result


def _read_panel(database_path: Path = DATABASE) -> pd.DataFrame:
    """Read selected descriptive fields through SQLite read-only/query-only mode."""
    uri = database_path.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        connection.execute("PRAGMA query_only = ON")
        columns = ", ".join(f'"{column}"' for column in PANEL_COLUMNS)
        frame = pd.read_sql_query(
            f"SELECT {columns} FROM v_analytics_msa_industry_year "
            "ORDER BY cbsa_code, sector_code, year",
            connection,
        )
    frame = _normalize_codes(frame)
    frame["year"] = pd.to_numeric(frame.year, errors="raise").astype("Int16")
    for column in PANEL_COLUMNS:
        if column in frame and column not in {
            "cbsa_code", "cbsa_name", "sector_code", "sector_title", "year", "source_quality_notes"
        }:
            if column.endswith(("matched", "suppression", "available", "coverage", "controls")) or column == "has_suppression":
                frame[column] = frame[column].astype("boolean")
            else:
                frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Float64")
    for column in ("cbsa_name", "sector_title", "source_quality_notes"):
        frame[column] = frame[column].astype("string")
    return frame


def _coverage_source(panel: pd.DataFrame) -> pd.DataFrame:
    a5 = _normalize_codes(_read_csv("a5_msa_coverage.csv", dtype={"cbsa_code": "string"}))
    a6 = _normalize_codes(_read_csv("a6_msa_coverage_audit.csv", dtype={"cbsa_code": "string"}))
    key = ["cbsa_code"]
    if a5.cbsa_code.duplicated().any() or a6.cbsa_code.duplicated().any():
        raise ValueError("Coverage source must contain exactly one row per CBSA")
    a5_fields = ["row_count", "sector_count", "year_count", "panel_count", "eligible_for_comparison"]
    comparison = a6.merge(a5[key + a5_fields], on=key, how="outer", suffixes=("_a6", "_a5"), indicator=True, validate="one_to_one")
    if not comparison._merge.eq("both").all():
        raise ValueError("A5/A6 coverage audit CBSA sets differ")
    for field in a5_fields:
        left, right = comparison[f"{field}_a6"], comparison[f"{field}_a5"]
        if not left.astype("string").fillna("<NA>").equals(right.astype("string").fillna("<NA>")):
            raise ValueError(f"A5/A6 coverage source mismatch in {field}")

    observed = panel.groupby("cbsa_code", observed=True).agg(
        first_year=("year", "min"), last_year=("year", "max"),
        panel_observation_count=("year", "size"), panel_sector_count=("sector_code", "nunique"),
        panel_year_count=("year", "nunique"),
    ).reset_index()
    coverage = a6.merge(observed, on="cbsa_code", how="outer", indicator=True, validate="one_to_one")
    if not coverage._merge.eq("both").all():
        raise ValueError("Coverage audit and analytical panel CBSA sets differ")
    for audit_col, panel_col in (("row_count", "panel_observation_count"),
                                 ("sector_count", "panel_sector_count"),
                                 ("year_count", "panel_year_count")):
        if not coverage[audit_col].eq(coverage[panel_col]).all():
            raise ValueError(f"Panel coverage counts disagree with A5/A6 field {audit_col}")

    expected_eligible = (
        coverage.row_count.ge(100) & coverage.sector_count.ge(5) & coverage.year_count.ge(10)
    )
    source_eligible = coverage.eligible_for_comparison.astype("boolean")
    if not np.array_equal(expected_eligible.to_numpy(dtype=bool), source_eligible.fillna(False).to_numpy(dtype=bool)):
        raise ValueError("A5 coverage flag no longer matches the documented 100/5/10 rule")
    coverage["coverage_status"] = np.where(expected_eligible, "comparison_eligible", "thin")
    coverage["comparison_eligible_flag"] = expected_eligible.astype("boolean")
    coverage["model_eligible_flag"] = coverage.modeling_eligible.astype("boolean")
    coverage["observation_count"] = coverage.row_count.astype("Int32")
    coverage["sector_count"] = coverage.sector_count.astype("Int16")
    coverage["year_count"] = coverage.year_count.astype("Int16")
    coverage["first_year"] = coverage.first_year.astype("Int16")
    coverage["last_year"] = coverage.last_year.astype("Int16")
    coverage["coverage_note"] = np.where(
        expected_eligible,
        "Passes A5 descriptive screen: at least 100 observations, 5 sectors, and 10 years; not a model-reliability guarantee.",
        "Below the A5 descriptive screen (100 observations, 5 sectors, and 10 years); interpret with limited coverage.",
    )
    coverage.loc[~coverage.model_eligible_flag.fillna(False), "coverage_note"] += " No A6 development OOF prediction is available for this MSA."
    return coverage.drop(columns=["_merge", "panel_observation_count", "panel_sector_count", "panel_year_count"])


def _attach_historical_gap(panel: pd.DataFrame) -> pd.DataFrame:
    gaps = _normalize_codes(_read_csv("a6_gap_target_pairs.csv", dtype={"cbsa_code": "string", "sector_code": "string"}))
    gaps = gaps.loc[gaps.split_role.eq("validation"), [
        "cbsa_code", "sector_code", "predictor_year", "target_year",
        "observed_target_startup_rate", "expected_target_startup_rate", "alignment_residual", "gap_p20",
    ]].copy()
    key = ["cbsa_code", "sector_code", "target_year"]
    if gaps.duplicated(key).any():
        raise ValueError("A6 validation target labels are not unique at CBSA-sector-target year")
    if gaps.target_year.gt(2020).any():
        raise ValueError("Development validation target artifact contains a post-2020 record")
    gaps["gap_p20"] = pd.to_numeric(gaps.gap_p20, errors="raise").astype("Int8")
    if not gaps.gap_p20.dropna().isin([0, 1]).all():
        raise ValueError("A6 historical gap labels must be binary 0/1")
    panel_targets = panel[["cbsa_code", "sector_code", "year", "startup_rate"]].rename(
        columns={"year": "target_year", "startup_rate": "panel_startup_rate"}
    )
    labeled = gaps.merge(
        panel_targets, on=key, how="left", validate="one_to_one", indicator=True,
    )
    if not labeled._merge.eq("both").all():
        raise ValueError("Some A6 validation target rows do not match the analytical panel")
    observed = pd.to_numeric(labeled.observed_target_startup_rate, errors="coerce")
    panel_observed = pd.to_numeric(labeled.panel_startup_rate, errors="coerce")
    if not np.allclose(observed, panel_observed, rtol=0, atol=1e-9, equal_nan=True):
        raise ValueError("A6 target startup rates disagree with the canonical analytical panel")
    labeled = labeled.rename(columns={
        "target_year": "year", "expected_target_startup_rate": "expected_startup_rate",
        "gap_p20": "observed_historical_gap_status",
    })
    labeled["year"] = labeled.year.astype("Int16")
    return labeled[[
        "cbsa_code", "sector_code", "year", "predictor_year", "expected_startup_rate",
        "alignment_residual", "observed_historical_gap_status",
    ]]


def build_msa_industry_year(panel: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    labels = _attach_historical_gap(panel)
    result = panel.merge(labels, on=["cbsa_code", "sector_code", "year"], how="left", validate="one_to_one")
    result = result.merge(
        coverage[["cbsa_code", "observation_count", "sector_count", "year_count", "coverage_status",
                  "comparison_eligible_flag", "model_eligible_flag"]],
        on="cbsa_code", how="left", validate="many_to_one",
    )
    result = result.rename(columns={
        "cbsa_name": "msa_name", "sector_title": "sector_name",
        "observation_count": "msa_observation_count", "sector_count": "msa_sector_count",
        "year_count": "msa_year_count",
    })
    result["alignment_label"] = pd.Series(pd.NA, index=result.index, dtype="string")
    valid = result.alignment_residual.notna()
    result.loc[valid & result.alignment_residual.ge(0), "alignment_label"] = "at_or_above_expected"
    result.loc[valid & result.alignment_residual.lt(0), "alignment_label"] = "below_expected"
    result["observed_historical_gap_status"] = result.observed_historical_gap_status.astype("Int8")
    result["predictor_year_for_gap_label"] = result.predictor_year.astype("Int16")
    result = result.drop(columns=["predictor_year"])
    result = result.rename(columns={"predictor_year_for_gap_label": "gap_label_predictor_year"})
    if result[["msa_name", "sector_name", "coverage_status"]].isna().any().any():
        raise ValueError("Dashboard longitudinal panel is missing geography/industry/coverage labels")
    return _stable_sort(result, ["cbsa_code", "sector_code", "year"])


def _stable_sort(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return frame.sort_values(columns, kind="mergesort", na_position="last").reset_index(drop=True)


def build_model_predictions(panel: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    key = ["cbsa_code", "sector_code", "predictor_year", "target_year"]
    dtype = {"cbsa_code": "string", "sector_code": "string"}
    dev_log = _normalize_codes(_read_csv("a6_baseline_oof_predictions.csv", dtype=dtype))
    dev_hgb = _normalize_codes(_read_csv("a6_advanced_oof_predictions.csv", dtype=dtype))
    if dev_log.duplicated(key).any() or dev_hgb.duplicated(key).any():
        raise ValueError("Development OOF prediction keys must be unique")
    dev = dev_log[key + ["fold", "actual_gap", "baseline_1_probability"]].merge(
        dev_hgb[key + ["actual_gap", "hist_gradient_boosting_probability"]],
        on=key, how="outer", suffixes=("_logistic", "_hgb"), validate="one_to_one", indicator=True,
    )
    if not dev._merge.eq("both").all() or not dev.actual_gap_logistic.eq(dev.actual_gap_hgb).all():
        raise ValueError("A6 development logistic/HGB OOF keys or outcomes do not align")
    dev = dev.rename(columns={
        "actual_gap_logistic": "actual_gap", "baseline_1_probability": "logistic_probability",
        "hist_gradient_boosting_probability": "hgb_probability",
    }).drop(columns=["actual_gap_hgb", "_merge"])
    dev["development_or_holdout"] = "development_oof"

    hold = _normalize_codes(_read_csv("a6_final_holdout_predictions.csv", dtype=dtype))
    hold = hold.rename(columns={
        "predicted_probability_logistic": "logistic_probability",
        "predicted_probability_hgb": "hgb_probability", "cbsa_name": "msa_name",
        "sector_title": "sector_name",
    })
    hold["development_or_holdout"] = "final_holdout"
    hold["fold"] = pd.Series(pd.NA, index=hold.index, dtype="string")
    hold = hold[key + ["fold", "actual_gap", "logistic_probability", "hgb_probability", "development_or_holdout", "msa_name", "sector_name"]]

    dev = dev.merge(
        panel[["cbsa_code", "sector_code", "year", "cbsa_name", "sector_title"]].drop_duplicates(),
        left_on=["cbsa_code", "sector_code", "predictor_year"],
        right_on=["cbsa_code", "sector_code", "year"], how="left", validate="many_to_one",
    ).rename(columns={"cbsa_name": "msa_name", "sector_title": "sector_name"}).drop(columns="year")
    dev["actual_gap"] = pd.to_numeric(dev.actual_gap, errors="raise").astype("Int8")
    hold["actual_gap"] = pd.to_numeric(hold.actual_gap, errors="raise").astype("Int8")
    predictions = pd.concat([dev, hold], ignore_index=True, sort=False)
    predictions = predictions.merge(
        coverage[["cbsa_code", "coverage_status"]], on="cbsa_code", how="left", validate="many_to_one",
    )
    predictions["primary_model_flag"] = True
    for col in ("predictor_year", "target_year"):
        predictions[col] = pd.to_numeric(predictions[col], errors="raise").astype("Int16")
    predictions["fold"] = predictions.fold.astype("string")
    predictions["actual_gap"] = predictions.actual_gap.astype("Int8")
    if predictions[["msa_name", "sector_name", "coverage_status"]].isna().any().any():
        raise ValueError("Prediction rows could not join names/coverage")
    return _stable_sort(predictions[[
        "cbsa_code", "msa_name", "sector_code", "sector_name", "predictor_year", "target_year",
        "actual_gap", "development_or_holdout", "fold", "logistic_probability", "hgb_probability",
        "primary_model_flag", "coverage_status",
    ]], key)


def build_model_summary() -> pd.DataFrame:
    source = _read_csv("a6_final_model_performance.csv")
    source["dataset"] = source.dataset.replace({"holdout": "final_holdout"})
    records = []
    for row in source.to_dict("records"):
        for metric in SUMMARY_METRICS:
            value = row.get(metric)
            records.append({
                "dataset_split": row["dataset"], "model": row["model"],
                "model_label": MODEL_LABELS.get(row["model"], row["model"]),
                "metric": metric, "value": value, "metric_label": METRIC_LABELS[metric],
                "interpretation_order": METRIC_ORDER[metric], "primary_metric_flag": metric == "AP",
                "primary_model_flag": row["model"] == "logistic", "sample_n": int(row["N"]),
                "prevalence": row["prevalence"],
            })
    result = pd.DataFrame(records)
    result["value"] = pd.to_numeric(result.value, errors="coerce").astype("Float64")
    result["sample_n"] = result.sample_n.astype("Int32")
    result["interpretation_order"] = result.interpretation_order.astype("Int8")
    return _stable_sort(result, ["dataset_split", "model", "interpretation_order"])


def build_calibration() -> pd.DataFrame:
    dev_base = _read_csv("a6_baseline_calibration.csv")
    dev_adv = _read_csv("a6_advanced_calibration.csv")
    hold = _read_csv("a6_final_holdout_calibration.csv")
    dev_base = dev_base.loc[dev_base.model.isin(["baseline_0_prevalence", "baseline_1_simple"])].copy()
    dev_adv = dev_adv.loc[dev_adv.model.eq("hist_gradient_boosting")].copy()
    dev = pd.concat([dev_base, dev_adv], ignore_index=True)
    dev["dataset_split"] = "development_oof"
    hold = hold.loc[hold.model.isin(["prevalence_benchmark", "logistic", "hist_gradient_boosting"])].copy()
    hold["dataset_split"] = "final_holdout"
    result = pd.concat([dev, hold], ignore_index=True)
    result["model"] = result.model.replace({
        "baseline_0_prevalence": "prevalence_benchmark", "baseline_1_simple": "logistic",
    })
    result["risk_bin"] = pd.to_numeric(result.risk_bin, errors="raise").astype("Int8")
    result["n"] = pd.to_numeric(result.n, errors="raise").astype("Int32")
    return _stable_sort(result[[
        "dataset_split", "model", "risk_bin", "n", "mean_predicted_probability", "observed_gap_prevalence",
    ]], ["dataset_split", "model", "risk_bin"])


def build_model_by_year(panel: pd.DataFrame) -> pd.DataFrame:
    result = _read_csv("a6_final_holdout_by_year.csv")
    result = result.rename(columns={"N": "sample_n"})
    result["dataset_split"] = "final_holdout"
    result["predictor_year"] = result.predictor_year.astype("Int16")
    result["target_year"] = result.target_year.astype("Int16")
    # The table is already at model x year grain; no sector key is needed.
    return _stable_sort(result, ["predictor_year", "target_year", "model"])


def build_model_by_sector(panel: pd.DataFrame) -> pd.DataFrame:
    result = _read_csv("a6_final_holdout_by_sector.csv", dtype={"sector": "string"})
    result = result.rename(columns={"sector": "sector_code", "N": "sample_n", "positive_N": "positive_n"})
    labels = panel[["sector_code", "sector_title"]].drop_duplicates()
    if labels.sector_code.duplicated().any():
        raise ValueError("Sector code maps to multiple labels in the analytical panel")
    result = result.merge(labels, on="sector_code", how="left", validate="many_to_one")
    result = result.rename(columns={"sector_title": "sector_name"})
    result["dataset_split"] = "final_holdout"
    result["sample_n"] = result.sample_n.astype("Int32")
    result["positive_n"] = result.positive_n.astype("Int32")
    result["sufficient_sample_flag"] = result.sufficient_sample_flag.astype("boolean")
    return _stable_sort(result, ["sector_code", "model"])


def build_model_by_msa_size() -> pd.DataFrame:
    result = _read_csv("a6_final_holdout_by_msa_size.csv")
    result = result.rename(columns={"MSA_count": "msa_count", "N": "sample_n"})
    result["dataset_split"] = "final_holdout"
    result["msa_count"] = result.msa_count.astype("Int16")
    result["sample_n"] = result.sample_n.astype("Int32")
    return _stable_sort(result, ["msa_size_group", "model"])


def build_sources(database_path: Path = DATABASE) -> pd.DataFrame:
    uri = database_path.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        connection.execute("PRAGMA query_only = ON")
        manifest = pd.read_sql_query(
            "SELECT source_name, source_agency AS agency, dataset_name AS dataset, "
            "MIN(source_year) AS min_year, MAX(source_year) AS max_year "
            "FROM metadata_source_manifest GROUP BY source_name, source_agency, dataset_name",
            connection,
        )
    keep = {
        "Census Business Dynamics Statistics (BDS)": "Business Dynamics Statistics: MSA by Sector",
        "BLS Quarterly Census of Employment and Wages (QCEW)": "Quarterly Census of Employment and Wages",
        "Census County Business Patterns (CBP)": "County Business Patterns",
        "American Community Survey (ACS)": "American Community Survey",
        "Census CBSA Delineation Files": "Core Based Statistical Areas reference",
        "North American Industry Classification System (NAICS)": "NAICS concordances and structure",
    }
    records = []
    for name, dataset in keep.items():
        rows = manifest.loc[manifest.source_name.eq(name)]
        if name.startswith("Census Business"):
            rows = rows.loc[rows.dataset.eq("Business Dynamics Statistics: MSA by Sector")]
        if rows.empty:
            raise ValueError(f"Required source manifest entry is missing: {name}")
        manifest_first, manifest_last = int(rows.min_year.min()), int(rows.max_year.max())
        if "BDS" in name or "QCEW" in name:
            role, geography, industry = "Entrepreneurship outcome / economic context", "MSA x industry", "2-digit sector; BDS native classification vintage retained in source metadata"
        elif "CBP" in name:
            role, geography, industry = "Business-structure context", "County aggregates mapped to CBSA", "Source NAICS vintage with audited analytical mapping"
        elif "ACS" in name:
            role, geography, industry = "Regional socioeconomic context", "MSA-year", "Not industry-specific"
        elif "CBSA" in name:
            role, geography, industry = "Geography reference", "CBSA/MSA", "Not applicable"
        else:
            role, geography, industry = "Industry reference/concordance", "National classification", "NAICS historical concordance to analytical reference"
        if any(token in name for token in ("BDS", "QCEW", "CBP", "ACS")):
            years_used = "2010-2023"
        elif "CBSA" in name:
            years_used = "2023"
        else:
            years_used = "2007-2022"
        records.append({
            "source_name": name, "agency": str(rows.agency.iloc[0]),
            "dataset": dataset, "role_in_project": role,
            "years_used": years_used, "geography": geography,
            "industry_level": industry,
            "notes": f"Canonical manifest records source vintage year(s) {manifest_first}-{manifest_last}; analytical use period and transformation/vintage caveats are documented in A4/A6 source documentation.",
            "source_category": "official_input_or_reference",
        })
    records.append({
        "source_name": "Assignment 6 finalized analytical outputs", "agency": "Project analysis",
        "dataset": "Locked A6 development OOF and final temporal holdout artifacts",
        "role_in_project": "Expected-rate, gap-label, prediction, and evaluation outputs",
        "years_used": "Development outcomes through 2020; holdout outcomes 2021-2023",
        "geography": "CBSA/MSA x sector", "industry_level": "2-digit NAICS sector",
        "notes": "Consumed without refitting; development OOF and retrospective final holdout remain explicitly separated.",
        "source_category": "finalized_research_output",
    })
    return _stable_sort(pd.DataFrame(records), ["source_category", "source_name", "dataset"])


def build_datasets(database_path: Path = DATABASE) -> dict[str, pd.DataFrame]:
    panel = _read_panel(database_path)
    coverage = _coverage_source(panel)
    datasets = {
        "dashboard_msa_industry_year": build_msa_industry_year(panel, coverage),
        "dashboard_model_predictions": build_model_predictions(panel, coverage),
        "dashboard_model_summary": build_model_summary(),
        "dashboard_calibration": build_calibration(),
        "dashboard_model_by_year": build_model_by_year(panel),
        "dashboard_model_by_sector": build_model_by_sector(panel),
        "dashboard_model_by_msa_size": build_model_by_msa_size(),
        "dashboard_coverage": coverage[[
            "cbsa_code", "cbsa_name", "observation_count", "sector_count", "year_count",
            "first_year", "last_year", "comparison_eligible_flag", "model_eligible_flag",
            "coverage_status", "coverage_note", "a6_oof_rows",
        ]].rename(columns={"cbsa_name": "msa_name", "a6_oof_rows": "a6_oof_row_count"}),
        "dashboard_sources": build_sources(database_path),
    }
    return _enforce_dtypes(datasets)


def _enforce_dtypes(datasets: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    strings = {
        "dashboard_msa_industry_year": ["cbsa_code", "msa_name", "sector_code", "sector_name", "source_quality_notes", "alignment_label", "coverage_status"],
        "dashboard_model_predictions": ["cbsa_code", "msa_name", "sector_code", "sector_name", "development_or_holdout", "fold", "coverage_status"],
        "dashboard_model_summary": ["dataset_split", "model", "model_label", "metric", "metric_label"],
        "dashboard_calibration": ["dataset_split", "model"],
        "dashboard_model_by_year": ["model", "dataset_split"],
        "dashboard_model_by_sector": ["sector_code", "sector_name", "model", "dataset_split"],
        "dashboard_model_by_msa_size": ["msa_size_group", "model", "dataset_split"],
        "dashboard_coverage": ["cbsa_code", "msa_name", "coverage_status", "coverage_note"],
        "dashboard_sources": ["source_name", "agency", "dataset", "role_in_project", "years_used", "geography", "industry_level", "notes", "source_category"],
    }
    for dataset, columns in strings.items():
        for column in columns:
            if column in datasets[dataset]:
                datasets[dataset][column] = datasets[dataset][column].astype("string")
    integer_columns = {
        "dashboard_msa_industry_year": {"year": "Int16", "gap_label_predictor_year": "Int16", "observed_historical_gap_status": "Int8", "msa_observation_count": "Int32", "msa_sector_count": "Int16", "msa_year_count": "Int16"},
        "dashboard_model_predictions": {"predictor_year": "Int16", "target_year": "Int16", "actual_gap": "Int8"},
        "dashboard_model_summary": {"sample_n": "Int32", "interpretation_order": "Int8"},
        "dashboard_calibration": {"risk_bin": "Int8", "n": "Int32"},
        "dashboard_model_by_year": {"predictor_year": "Int16", "target_year": "Int16", "sample_n": "Int32"},
        "dashboard_model_by_sector": {"sample_n": "Int32", "positive_n": "Int32"},
        "dashboard_model_by_msa_size": {"msa_count": "Int16", "sample_n": "Int32"},
        "dashboard_coverage": {"observation_count": "Int32", "sector_count": "Int16", "year_count": "Int16", "first_year": "Int16", "last_year": "Int16", "a6_oof_row_count": "Int32"},
    }
    for dataset, mapping in integer_columns.items():
        for column, dtype in mapping.items():
            datasets[dataset][column] = pd.to_numeric(datasets[dataset][column], errors="raise").astype(dtype)
    boolean_columns = {
        "dashboard_msa_industry_year": ["comparison_eligible_flag", "model_eligible_flag"],
        "dashboard_model_predictions": ["primary_model_flag"],
        "dashboard_model_summary": ["primary_metric_flag", "primary_model_flag"],
        "dashboard_model_by_sector": ["sufficient_sample_flag"],
        "dashboard_coverage": ["comparison_eligible_flag", "model_eligible_flag"],
    }
    for dataset, columns in boolean_columns.items():
        for column in columns:
            datasets[dataset][column] = datasets[dataset][column].astype("boolean")
    for dataset, frame in datasets.items():
        for column in frame.columns:
            if column in {"cbsa_code", "msa_name", "sector_code", "sector_name", "year", "fold", "model", "model_label", "metric", "metric_label", "dataset_split", "development_or_holdout", "coverage_status", "coverage_note", "source_name", "agency", "dataset", "role_in_project", "years_used", "geography", "industry_level", "notes", "source_category", "msa_size_group", "alignment_label", "source_quality_notes"}:
                continue
            if column.endswith("_flag") or column in {"bds_startup_available", "bds_has_suppression", "qcew_has_suppression", "qcew_is_complete_county_coverage", "acs_matched", "acs_has_suppression", "acs_has_missing_controls", "cbp_matched", "cbp_has_suppression", "cbp_is_complete_county_coverage", "has_suppression"}:
                continue
            if column not in integer_columns.get(dataset, {}):
                if pd.api.types.is_numeric_dtype(frame[column].dtype):
                    frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Float64")
    return datasets


def _model_and_category_options(predictions: pd.DataFrame, panel: pd.DataFrame) -> dict:
    msas = panel[["cbsa_code", "msa_name"]].drop_duplicates().sort_values("cbsa_code")
    sectors = panel[["sector_code", "sector_name"]].drop_duplicates().sort_values("sector_code")
    gap = _read_csv("a6_gap_target_pairs.csv")
    observed = sorted(int(x) for x in gap.loc[gap.split_role.eq("validation"), "gap_p20"].dropna().unique())
    return {
        "msa_options": [{"value": r.cbsa_code, "label": r.msa_name} for r in msas.itertuples(index=False)],
        "sector_options": [{"value": r.sector_code, "label": r.sector_name} for r in sectors.itertuples(index=False)],
        "year_options": sorted(int(y) for y in panel.year.dropna().unique()),
        "observed_historical_gap_status_options": observed,
        "prediction_availability_options": ["available", "unavailable"],
        "prediction_predictor_years": sorted(int(y) for y in predictions.predictor_year.unique()),
        "risk_category_options": [],
        "risk_category_note": "No category rule is frozen; use continuous probability and ranking only.",
    }


def _label_dictionary(datasets: dict[str, pd.DataFrame]) -> dict:
    panel = datasets["dashboard_msa_industry_year"]
    return {
        "models": MODEL_LABELS,
        "metrics": METRIC_LABELS,
        "sectors": dict(sorted(panel[["sector_code", "sector_name"]].drop_duplicates().set_index("sector_code").sector_name.items())),
        "msas": dict(sorted(panel[["cbsa_code", "msa_name"]].drop_duplicates().set_index("cbsa_code").msa_name.items())),
        "alignment": {"at_or_above_expected": "Observed at or above expected startup activity", "below_expected": "Observed below expected startup activity"},
        "gap_status": {"0": "No entrepreneurial gap under the A6 p20 definition", "1": "Entrepreneurial gap under the A6 p20 definition"},
        "terms": {
            "startup_rate": "Observed startup activity",
            "expected_startup_rate": "Expected startup activity",
            "alignment_residual": "Entrepreneurial alignment (observed minus expected)",
            "observed_historical_gap_status": "Observed historical entrepreneurial gap",
            "actual_gap": "Realized target-year gap (evaluation outcome)",
            "logistic_probability": "Predicted probability of a gap at t+3 (primary logistic)",
            "hgb_probability": "Predicted probability of a gap at t+3 (HGB sensitivity)",
        },
    }


def validate_dashboard_outputs(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    checks: list[dict] = []

    def add(name: str, dataset: str, passed: bool, observed, expected, notes: str = "") -> None:
        checks.append({"check_name": name, "dataset": dataset, "status": "pass" if passed else "fail",
                       "observed": str(observed), "expected": str(expected), "notes": notes})
        if not passed:
            raise ValueError(f"Dashboard quality check failed: {name}; observed={observed}; expected={expected}")

    for name, frame in datasets.items():
        keys = KEYS[name]
        duplicate_n = int(frame.duplicated(keys).sum())
        add("unique_primary_key", name, duplicate_n == 0, duplicate_n, 0, ", ".join(keys))
        required = keys
        null_keys = int(frame[required].isna().any(axis=1).sum())
        add("non_null_primary_key", name, null_keys == 0, null_keys, 0)
    preds = datasets["dashboard_model_predictions"]
    horizon_ok = preds.target_year.eq(preds.predictor_year + 3).all()
    add("exact_three_year_horizon", "dashboard_model_predictions", bool(horizon_ok),
        int((preds.target_year - preds.predictor_year).value_counts().to_dict().get(3, 0)), len(preds))
    predictor_before_target = preds.predictor_year.lt(preds.target_year).all()
    add("predictor_precedes_target", "dashboard_model_predictions", bool(predictor_before_target),
        bool(predictor_before_target), True)
    for column in ("logistic_probability", "hgb_probability"):
        valid = preds[column].between(0, 1).all() and preds[column].notna().all()
        add("probability_bounds_" + column, "dashboard_model_predictions", bool(valid),
            f"min={preds[column].min()}, max={preds[column].max()}", "[0, 1], non-null")
    labels_valid = preds.actual_gap.dropna().isin([0, 1]).all() and preds.actual_gap.notna().all()
    add("binary_gap_labels", "dashboard_model_predictions", bool(labels_valid),
        sorted(int(x) for x in preds.actual_gap.unique()), "0/1")
    split_valid = preds.development_or_holdout.isin(["development_oof", "final_holdout"]).all()
    add("split_labels", "dashboard_model_predictions", bool(split_valid),
        sorted(preds.development_or_holdout.unique()), "development_oof/final_holdout")
    model_valid = (preds.primary_model_flag.all() and
                   set(datasets["dashboard_model_summary"].model.unique()) == set(MODEL_LABELS))
    add("model_identity_and_primary_flag", "dashboard_model_predictions", bool(model_valid),
        "logistic primary; HGB sensitivity", "frozen A6 model identities")
    temporal_roles_valid = (
        preds.loc[preds.development_or_holdout.eq("development_oof"), "target_year"].le(2020).all()
        and preds.loc[preds.development_or_holdout.eq("final_holdout"), "target_year"].between(2021, 2023).all()
        and preds.loc[preds.development_or_holdout.eq("final_holdout"), "predictor_year"].between(2018, 2020).all()
    )
    add("development_holdout_year_boundaries", "dashboard_model_predictions", bool(temporal_roles_valid),
        "development targets <=2020; holdout predictor 2018-2020/target 2021-2023",
        "development targets <=2020; holdout predictor 2018-2020/target 2021-2023")
    panel = datasets["dashboard_msa_industry_year"]
    add("cbsa_string_type", "dashboard_msa_industry_year", str(panel.cbsa_code.dtype) == "string",
        str(panel.cbsa_code.dtype), "string")
    add("sector_string_type", "dashboard_msa_industry_year", str(panel.sector_code.dtype) == "string",
        str(panel.sector_code.dtype), "string")
    valid_sectors = panel.sector_code.dropna().isin(APPROVED_SECTORS).all()
    add("sector_codes_resolve_to_panel_reference", "dashboard_msa_industry_year", bool(valid_sectors),
        sorted(panel.sector_code.dropna().unique()), sorted(APPROVED_SECTORS))
    status_ok = datasets["dashboard_coverage"].coverage_status.isin(["comparison_eligible", "thin"]).all()
    add("coverage_categories", "dashboard_coverage", bool(status_ok),
        sorted(datasets["dashboard_coverage"].coverage_status.unique()), "comparison_eligible/thin")
    coverage = datasets["dashboard_coverage"]
    add("one_coverage_row_per_msa", "dashboard_coverage", not coverage.cbsa_code.duplicated().any(),
        int(coverage.cbsa_code.duplicated().sum()), 0)
    coverage_valid_counts = (
        coverage.observation_count.ge(0).all() & coverage.sector_count.ge(0).all()
        & coverage.year_count.ge(0).all() & coverage.first_year.le(coverage.last_year).all()
    )
    add("coverage_counts_and_year_range", "dashboard_coverage", bool(coverage_valid_counts),
        "nonnegative counts; first_year <= last_year", "nonnegative counts; first_year <= last_year")
    dev_panel_labels = panel.loc[panel.observed_historical_gap_status.notna()]
    historical_label_years_valid = dev_panel_labels.year.between(2017, 2020).all()
    add("historical_gap_label_year_scope", "dashboard_msa_industry_year", bool(historical_label_years_valid),
        sorted(int(x) for x in dev_panel_labels.year.unique()), "development OOF target years through 2020")
    panel_years_valid = panel.year.between(2010, 2023).all()
    add("descriptive_year_range", "dashboard_msa_industry_year", bool(panel_years_valid),
        f"{int(panel.year.min())}-{int(panel.year.max())}", "2010-2023")
    sector_perf = datasets["dashboard_model_by_sector"]
    sector_nulls_valid = (
        sector_perf.loc[sector_perf.sufficient_sample_flag, ["AP", "ROC_AUC"]].notna().all().all()
        and sector_perf.loc[~sector_perf.sufficient_sample_flag, ["AP", "ROC_AUC"]].isna().all().all()
    )
    add("sector_metric_suppression_matches_a6_flag", "dashboard_model_by_sector", bool(sector_nulls_valid),
        "A6 sufficiency flag agrees with AP/ROC-AUC null status", "metrics present iff source flag sufficient")
    summary_models = set(datasets["dashboard_model_summary"].model.unique())
    add("summary_model_names", "dashboard_model_summary", summary_models == set(MODEL_LABELS),
        sorted(summary_models), sorted(MODEL_LABELS))
    required_calibration = datasets["dashboard_calibration"]
    calibration_ok = required_calibration[["n", "mean_predicted_probability", "observed_gap_prevalence"]].notna().all().all()
    calibration_bounds = required_calibration[["mean_predicted_probability", "observed_gap_prevalence"]].apply(
        lambda col: col.between(0, 1).all()
    ).all()
    add("calibration_null_and_probability_policy", "dashboard_calibration", bool(calibration_ok and calibration_bounds),
        "required values populated and proportions in [0,1]", "same")
    add("no_risk_category_rule", "dashboard_model_predictions", "risk_category" not in preds.columns,
        "risk_category" in preds.columns, False, "A7.1 has no frozen non-holdout category rule")

    source_perf = _read_csv("a6_final_model_performance.csv")
    summary = datasets["dashboard_model_summary"]
    row = source_perf.loc[source_perf.dataset.eq("holdout") & source_perf.model.eq("logistic")].iloc[0]
    for metric, source_col in (("AP", "AP"), ("prevalence", "prevalence"), ("ROC_AUC", "ROC_AUC"),
                               ("Brier", "Brier"), ("top10_lift", "top10_lift")):
        got = summary.loc[(summary.dataset_split.eq("final_holdout")) & summary.model.eq("logistic") & summary.metric.eq(metric), "value"].iloc[0]
        want = float(row[source_col])
        passed = bool(np.isclose(float(got), want, rtol=0, atol=1e-14))
        add("metric_reconciliation_" + metric, "dashboard_model_summary", passed, got, want,
            "Source is reports/tables/a6_final_model_performance.csv")
    return pd.DataFrame(checks)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_dashboard_data(output_dir: Path = OUTPUT_DIR, database_path: Path = DATABASE) -> dict[str, object]:
    datasets = build_datasets(database_path)
    checks = validate_dashboard_outputs(datasets)
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory_rows = []
    row_counts = {}
    for name, frame in datasets.items():
        filename = name + ".parquet"
        path = output_dir / filename
        frame.to_parquet(path, index=False, engine="pyarrow", compression="zstd", version="2.6")
        row_counts[name] = int(len(frame))
        inventory_rows.append({
            "dataset": name, "path": f"data/dashboard/{filename}", "row_count": len(frame),
            "column_count": len(frame.columns), "primary_key": "+".join(KEYS[name]),
            "source": _dataset_source(name), "dashboard_pages": _dataset_pages(name),
            "contains_model_output": name in {"dashboard_model_predictions", "dashboard_model_summary", "dashboard_calibration", "dashboard_model_by_year", "dashboard_model_by_sector", "dashboard_model_by_msa_size"},
            "contains_holdout_outcome": name in {"dashboard_model_predictions", "dashboard_model_summary", "dashboard_calibration", "dashboard_model_by_year", "dashboard_model_by_sector", "dashboard_model_by_msa_size"},
            "file_size_bytes": path.stat().st_size,
        })
    filter_options = _model_and_category_options(
        datasets["dashboard_model_predictions"], datasets["dashboard_msa_industry_year"]
    )
    labels = _label_dictionary(datasets)
    _write_json(output_dir / "dashboard_filter_options.json", filter_options)
    _write_json(output_dir / "dashboard_labels.json", labels)
    full_hash = subprocess.run(["git", "rev-parse", "78f89c6"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    metadata = {
        "dashboard_data_version": "1.0.0", "schema_version": "1.0.0",
        "repository_name": "regional-entrepreneurship-intelligence", "assignment": "A7.2",
        "study_period": {"descriptive": [2010, 2023], "development_target_max": 2020, "holdout_target": [2021, 2023]},
        "unit_of_analysis": "CBSA x 2-digit NAICS sector x year",
        "primary_model": "logistic", "sensitivity_model": "hist_gradient_boosting",
        "target_definition": "A6 gap_p20: Model A startup-rate residual at exact t+3 target year relative to development-only p20 cutoff",
        "forecast_horizon_years": 3, "final_A6_commit": full_hash,
        "build_timestamp_utc": None,
        "dataset_row_counts": row_counts,
        "dataset_schemas": {name: [{"field": c, "dtype": str(dtype)} for c, dtype in frame.dtypes.items()] for name, frame in datasets.items()},
        "risk_categories": None,
        "risk_category_note": "No fixed presentation cutpoints are approved; probability/rank only.",
        "database_access": "SQLite read-only URI and PRAGMA query_only",
    }
    _write_json(output_dir / "dashboard_metadata.json", metadata)
    inventory = pd.DataFrame(inventory_rows)
    inventory.to_csv(QUALITY_DIR / "a7_dashboard_dataset_inventory.csv", index=False, lineterminator="\n")
    checks.to_csv(QUALITY_DIR / "a7_dashboard_quality_checks.csv", index=False, lineterminator="\n")
    lineage = build_lineage_audit(datasets)
    lineage.to_csv(QUALITY_DIR / "a7_dashboard_lineage_audit.csv", index=False, lineterminator="\n")
    dictionary_path = ROOT / "docs" / "ASSIGNMENT7_DATA_DICTIONARY.md"
    dictionary_path.write_text(build_data_dictionary_markdown(datasets, lineage), encoding="utf-8", newline="\n")
    report_path = ROOT / "reports" / "assignment7_dashboard_data_layer.md"
    report_path.write_text(build_data_layer_report(inventory, checks, metadata), encoding="utf-8", newline="\n")
    return {"datasets": datasets, "metadata": metadata, "inventory": inventory,
            "quality_checks": checks, "lineage": lineage, "report_path": report_path,
            "filter_options": filter_options,
            "labels": labels}


def _dataset_source(name: str) -> str:
    return {
        "dashboard_msa_industry_year": "A4 analytical panel + A6 validation gap target + A5/A6 coverage",
        "dashboard_model_predictions": "A6 baseline OOF + A6 advanced OOF + A6 final holdout predictions",
        "dashboard_model_summary": "A6 final model performance",
        "dashboard_calibration": "A6 baseline/advanced OOF calibration + A6 final holdout calibration",
        "dashboard_model_by_year": "A6 final holdout by year",
        "dashboard_model_by_sector": "A6 final holdout by sector + analytical sector labels",
        "dashboard_model_by_msa_size": "A6 final holdout by MSA size",
        "dashboard_coverage": "A5 coverage + A6 coverage audit + A4 analytical panel year range",
        "dashboard_sources": "A4 metadata source manifest + A6 finalized artifacts",
    }[name]


def _dataset_pages(name: str) -> str:
    if name in {"dashboard_msa_industry_year", "dashboard_model_predictions", "dashboard_coverage"}:
        return "Executive Overview; Regional & Industry Explorer; Data Quality & Limitations"
    if name == "dashboard_sources":
        return "About / Methods / Sources"
    if name in {"dashboard_model_summary", "dashboard_calibration", "dashboard_model_by_year", "dashboard_model_by_sector", "dashboard_model_by_msa_size"}:
        return "Executive Overview; Model Performance"
    return ""


def build_data_dictionary_markdown(
    datasets: dict[str, pd.DataFrame], lineage: pd.DataFrame
) -> str:
    definitions = {
        "cbsa_code": ("Core-Based Statistical Area code; normalized to five-character string.", "identifier"),
        "msa_name": ("CBSA/MSA display name from the analytical geography reference.", "text"),
        "sector_code": ("Analytical 2-digit NAICS sector code; compound sectors retain hyphens.", "category"),
        "sector_name": ("Analytical sector title from the A4 industry reference.", "text"),
        "year": ("Descriptive calendar year for the observed MSA-sector panel row.", "year"),
        "predictor_year": ("Calendar year t at which prediction inputs are observed.", "year"),
        "target_year": ("Calendar year t+3 of the prediction outcome.", "year"),
        "gap_label_predictor_year": ("OOF predictor year associated with the historical gap label stored at the target-year panel row.", "year"),
        "startup_rate": ("Observed firm startup rate as defined by the source analytical panel; source value is unchanged.", "source-defined rate"),
        "startup_rate_lag1": ("One-calendar-year lagged BDS startup rate; null where source predecessor is unavailable.", "source-defined rate"),
        "employment_growth": ("Annual QCEW employment growth measure from the analytical panel.", "fraction/rate as stored"),
        "establishment_growth": ("Annual QCEW establishment growth measure from the analytical panel.", "fraction/rate as stored"),
        "payroll_growth": ("Annual QCEW payroll growth measure from the analytical panel.", "fraction/rate as stored"),
        "wage_growth": ("Annual QCEW wage growth measure from the analytical panel.", "fraction/rate as stored"),
        "acs_population": ("ACS population estimate joined at MSA-year level.", "persons"),
        "acs_population_growth": ("Annual change in ACS population from the analytical panel.", "fraction/rate as stored"),
        "median_household_income": ("ACS median household income estimate.", "nominal dollars as stored"),
        "educational_attainment_pct": ("ACS educational attainment measure in the analytical panel.", "percent as stored"),
        "labor_force_participation_pct": ("ACS labor-force participation measure in the analytical panel.", "percent as stored"),
        "unemployment_rate": ("ACS unemployment measure in the analytical panel.", "percent/rate as stored"),
        "expected_startup_rate": ("A6 fold-validation Model A expected startup rate for the panel target year.", "source-defined rate"),
        "alignment_residual": ("A6 fold-validation observed target startup rate minus expected target startup rate.", "startup-rate points"),
        "alignment_label": ("Presentation label: residual >= 0 is at/above expected; residual < 0 is below expected.", "category"),
        "observed_historical_gap_status": ("A6 fold-validation gap_p20 label for the descriptive row's target year; 1=gap, 0=no gap.", "binary 0/1"),
        "actual_gap": ("Realized binary A6 outcome for the prediction pair's target year; retrospective target, 1=gap.", "binary 0/1"),
        "logistic_probability": ("Frozen A6 primary logistic predicted probability for the t+3 gap.", "probability 0-1"),
        "hgb_probability": ("Frozen A6 HistGradientBoosting sensitivity predicted probability for the t+3 gap.", "probability 0-1"),
        "development_or_holdout": ("A6 sample role; development OOF or final temporal holdout.", "category"),
        "fold": ("A6 development validation fold; not applicable to final holdout refit.", "category"),
        "primary_model_flag": ("True marks logistic as the A6 primary/reference model; HGB remains sensitivity.", "boolean"),
        "dataset_split": ("A6 evaluation split: development_oof or final_holdout.", "category"),
        "model": ("A6 model key: prevalence benchmark, logistic, or HistGradientBoosting.", "category"),
        "model_label": ("Human-readable label for the unchanged A6 model key.", "text"),
        "metric": ("A6 metric key in long-format performance output.", "category"),
        "value": ("Finalized A6 metric value copied without recomputation.", "metric-specific; proportions unless noted"),
        "metric_label": ("Human-readable label for metric key.", "text"),
        "interpretation_order": ("Stable display order for A6 metric families.", "integer order"),
        "primary_metric_flag": ("True for Average Precision, the prespecified primary metric.", "boolean"),
        "sample_n": ("Number of eligible MSA-sector prediction pairs represented by the metric row.", "observations"),
        "prevalence": ("Observed positive-gap share in the named sample.", "proportion 0-1"),
        "risk_bin": ("Ascending A6 score-ranked calibration bin identifier.", "ordinal bin"),
        "n": ("Number of observations in the calibration bin.", "observations"),
        "mean_predicted_probability": ("Mean model probability in the calibration bin.", "probability 0-1"),
        "observed_gap_prevalence": ("Observed positive-gap share in the calibration bin.", "proportion 0-1"),
        "comparison_eligible_flag": ("A5 descriptive coverage screen: >=100 rows, >=5 sectors, >=10 years.", "boolean"),
        "model_eligible_flag": ("A6 flag that at least one development OOF prediction exists for the MSA.", "boolean"),
        "observation_count": ("A5 observed MSA-industry-year panel row count.", "rows"),
        "msa_observation_count": ("A5 observed MSA-industry-year panel row count joined to each panel row.", "rows"),
        "sector_count": ("Distinct sectors represented in MSA coverage audit.", "sectors"),
        "msa_sector_count": ("Distinct sectors represented in MSA coverage audit, joined to panel row.", "sectors"),
        "year_count": ("Distinct years represented in MSA coverage audit.", "years"),
        "msa_year_count": ("Distinct years represented in MSA coverage audit, joined to panel row.", "years"),
        "first_year": ("Minimum observed analytical panel year for the MSA.", "year"),
        "last_year": ("Maximum observed analytical panel year for the MSA.", "year"),
        "coverage_status": ("A5 descriptive status: comparison_eligible or thin; not model reliability.", "category"),
        "coverage_note": ("Plain-language A5 screen definition and optional no-development-OOF note.", "text"),
        "a6_oof_row_count": ("Count of A6 development OOF prediction rows for the MSA.", "observations"),
        "msa_count": ("Number of MSAs represented in the MSA-size group.", "MSAs"),
        "msa_size_group": ("Training-cutpoint-defined small, middle, or large holdout MSA-size group.", "category"),
        "positive_n": ("Positive gap-event count for sector performance cell.", "events"),
        "sufficient_sample_flag": ("A6 event-count rule indicates sector score is reportable.", "boolean"),
        "source_name": ("Named source or finalized research-output family.", "text"),
        "agency": ("Source agency from acquisition manifest, or project analysis for A6 outputs.", "text"),
        "dataset": ("Named upstream source dataset or finalized A6 output group.", "text"),
        "role_in_project": ("Descriptive, predictor/context, target, or evaluation use.", "text"),
        "years_used": ("Analytical years represented or relevant reference vintage.", "year range"),
        "geography": ("Geographic grain of the source.", "text"),
        "industry_level": ("Industry granularity/vintage role, or not applicable.", "text"),
        "notes": ("Source-vintage and transformation caveat.", "text"),
        "source_category": ("Official input/reference or finalized research output.", "category"),
        "bds_startup_available": ("Canonical panel flag for available startup-rate source value.", "boolean"),
        "bds_has_suppression": ("Canonical panel BDS suppression indicator.", "boolean"),
        "qcew_has_suppression": ("Canonical panel QCEW suppression indicator.", "boolean"),
        "qcew_is_complete_county_coverage": ("QCEW CBSA aggregation completeness indicator.", "boolean"),
        "acs_matched": ("ACS MSA-year match indicator.", "boolean"),
        "acs_has_suppression": ("ACS suppression indicator.", "boolean"),
        "acs_has_missing_controls": ("ACS required-control missingness indicator.", "boolean"),
        "cbp_matched": ("CBP business-structure match indicator.", "boolean"),
        "cbp_has_suppression": ("CBP suppression indicator.", "boolean"),
        "cbp_is_complete_county_coverage": ("CBP CBSA aggregation completeness indicator.", "boolean"),
        "has_suppression": ("Combined source suppression flag from analytical panel.", "boolean"),
        "source_quality_notes": ("Source-quality note carried through from the analytical panel.", "text"),
        "top10_lift": ("Observed gap prevalence in highest-scored 10% divided by overall prevalence.", "ratio"),
        "top20_lift": ("Observed gap prevalence in highest-scored 20% divided by overall prevalence.", "ratio"),
        "top25_lift": ("Observed gap prevalence in highest-scored 25% divided by overall prevalence.", "ratio"),
        "AP": ("Average Precision for the named sample and model.", "unitless score"),
        "ROC_AUC": ("Area under the receiver operating characteristic curve.", "unitless score"),
        "Brier": ("Mean squared probability error.", "unitless score"),
        "recall": ("True-positive rate at the frozen A6 diagnostic threshold.", "proportion 0-1"),
        "precision": ("Positive predictive value at the frozen A6 diagnostic threshold.", "proportion 0-1"),
        "f1": ("Harmonic mean of precision and recall at the frozen A6 diagnostic threshold.", "proportion 0-1"),
        "balanced_accuracy": ("Mean of class-specific recall at the frozen A6 diagnostic threshold.", "proportion 0-1"),
    }
    lineage_by_key = lineage.set_index(["dashboard_dataset", "dashboard_field"])
    lines = [
        "# Assignment 7 Dashboard Data Dictionary", "",
        "Field-level dictionary generated from the validated A7.2 schemas and lineage audit. Source measures retain their upstream units; no scientific value is rescaled except probabilities/rates as noted.",
        "", "## Dataset Schemas", "",
    ]
    for dataset, frame in datasets.items():
        lines += [f"### `{dataset}`", "", f"Primary key: `{'+'.join(KEYS[dataset])}`.", "",
                  "| Field | Type | Definition | Unit | Null policy | Upstream artifact.field | Dashboard use |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        for field, dtype in frame.dtypes.items():
            definition, unit = definitions.get(field, (f"Source-derived `{field}` value; see lineage for exact upstream field and transformation.", "as defined by source"))
            if dataset == "dashboard_model_by_sector" and field in {"AP", "ROC_AUC"}:
                null = "Allowed where A6 suppresses cells below its event/no-negative-class rule."
            elif dataset == "dashboard_model_predictions" and field == "fold":
                null = "Null for final holdout; populated for development OOF."
            elif dataset == "dashboard_msa_industry_year" and field in {"expected_startup_rate", "alignment_residual", "alignment_label", "observed_historical_gap_status", "gap_label_predictor_year"}:
                null = "Expected outside A6 fold-validation target rows; no extrapolation."
            elif dataset == "dashboard_msa_industry_year" and field not in {"cbsa_code", "msa_name", "sector_code", "sector_name", "year", "coverage_status", "msa_observation_count", "msa_sector_count", "msa_year_count", "comparison_eligible_flag", "model_eligible_flag"}:
                null = "Allowed for source missingness/suppression/unavailable predecessor; never filled with zero."
            else:
                null = "Not expected in current artifact; keys and required fields fail validation if null."
            src = lineage_by_key.loc[(dataset, field)]
            source = f"{src.upstream_artifact}.{src.upstream_field}"
            use = _dataset_pages(dataset)
            safe = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{safe(field)}` | `{safe(dtype)}` | {safe(definition)} | {safe(unit)} | {safe(null)} | `{safe(source)}` | {safe(use)} |")
        lines.append("")
    lines += ["## Interpretation Notes", "",
              "`actual_gap` is a realized target outcome and is retrospective; `observed_historical_gap_status` exists only for development fold-validation target years in the longitudinal panel. `logistic_probability` and `hgb_probability` are score probabilities for the explicit `predictor_year` to `target_year` pair. There is no risk category field because no presentation cutoff was frozen. See `ASSIGNMENT7_NULL_POLICY.md` and `ASSIGNMENT7_COVERAGE_POLICY.md` for governing rules.", ""]
    return "\n".join(lines)


def build_lineage_audit(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    direct = {
        "dashboard_msa_industry_year": {
            "cbsa_code": ("v_analytics_msa_industry_year.cbsa_code", "Direct; cast to five-character string"),
            "msa_name": ("v_analytics_msa_industry_year.cbsa_name", "Direct rename"),
            "sector_code": ("v_analytics_msa_industry_year.sector_code", "Direct; cast to string"),
            "sector_name": ("v_analytics_msa_industry_year.sector_title", "Direct rename"),
            "year": ("v_analytics_msa_industry_year.year", "Direct; nullable integer"),
            "startup_rate": ("v_analytics_msa_industry_year.startup_rate", "Direct; no imputation"),
            "startup_rate_lag1": ("v_analytics_msa_industry_year.startup_rate_lag1", "Direct; no imputation"),
            "employment_growth": ("v_analytics_msa_industry_year.employment_growth", "Direct; no imputation"),
            "establishment_growth": ("v_analytics_msa_industry_year.establishment_growth", "Direct; no imputation"),
            "payroll_growth": ("v_analytics_msa_industry_year.payroll_growth", "Direct; no imputation"),
            "wage_growth": ("v_analytics_msa_industry_year.wage_growth", "Direct; no imputation"),
            "acs_population": ("v_analytics_msa_industry_year.acs_population", "Direct; no imputation"),
            "acs_population_growth": ("v_analytics_msa_industry_year.acs_population_growth", "Direct; no imputation"),
            "median_household_income": ("v_analytics_msa_industry_year.median_household_income", "Direct; no imputation"),
            "educational_attainment_pct": ("v_analytics_msa_industry_year.educational_attainment_pct", "Direct; no imputation"),
            "labor_force_participation_pct": ("v_analytics_msa_industry_year.labor_force_participation_pct", "Direct; no imputation"),
            "unemployment_rate": ("v_analytics_msa_industry_year.unemployment_rate", "Direct; no imputation"),
            "bds_startup_available": ("v_analytics_msa_industry_year.bds_startup_available", "Direct boolean quality flag"),
            "bds_has_suppression": ("v_analytics_msa_industry_year.bds_has_suppression", "Direct boolean quality flag"),
            "qcew_has_suppression": ("v_analytics_msa_industry_year.qcew_has_suppression", "Direct boolean quality flag"),
            "qcew_is_complete_county_coverage": ("v_analytics_msa_industry_year.qcew_is_complete_county_coverage", "Direct boolean quality flag"),
            "acs_matched": ("v_analytics_msa_industry_year.acs_matched", "Direct boolean quality flag"),
            "acs_has_suppression": ("v_analytics_msa_industry_year.acs_has_suppression", "Direct boolean quality flag"),
            "acs_has_missing_controls": ("v_analytics_msa_industry_year.acs_has_missing_controls", "Direct boolean quality flag"),
            "cbp_matched": ("v_analytics_msa_industry_year.cbp_matched", "Direct boolean quality flag"),
            "cbp_has_suppression": ("v_analytics_msa_industry_year.cbp_has_suppression", "Direct boolean quality flag"),
            "cbp_is_complete_county_coverage": ("v_analytics_msa_industry_year.cbp_is_complete_county_coverage", "Direct boolean quality flag"),
            "has_suppression": ("v_analytics_msa_industry_year.has_suppression", "Direct boolean quality flag"),
            "source_quality_notes": ("v_analytics_msa_industry_year.source_quality_notes", "Direct text note"),
            "expected_startup_rate": ("a6_gap_target_pairs.expected_target_startup_rate", "Fold-validation rows only; join by CBSA/sector/target-year"),
            "alignment_residual": ("a6_gap_target_pairs.alignment_residual", "A6 fold-validation residual; no recomputation"),
            "observed_historical_gap_status": ("a6_gap_target_pairs.gap_p20", "A6 fold-validation label; target year is descriptive row year"),
            "gap_label_predictor_year": ("a6_gap_target_pairs.predictor_year", "Retained to expose the forecast origin for the historical OOF label"),
            "alignment_label": ("a6_gap_target_pairs.alignment_residual", "Presentation label by residual sign: >=0 at/above; <0 below expected"),
            "msa_observation_count": ("a5_msa_coverage.row_count", "Join coverage summary by CBSA"),
            "msa_sector_count": ("a5_msa_coverage.sector_count", "Join coverage summary by CBSA"),
            "msa_year_count": ("a5_msa_coverage.year_count", "Join coverage summary by CBSA"),
            "coverage_status": ("a5_msa_coverage.eligible_for_comparison", "Apply documented A5 100/5/10 rule"),
            "comparison_eligible_flag": ("a5_msa_coverage.eligible_for_comparison", "Direct A5 flag, validated against threshold rule"),
            "model_eligible_flag": ("a6_msa_coverage_audit.modeling_eligible", "A6 flag: at least one development OOF row"),
        },
        "dashboard_model_predictions": {
            "logistic_probability": ("a6_baseline_oof_predictions.baseline_1_probability; a6_final_holdout_predictions.predicted_probability_logistic", "Direct frozen A6 scores"),
            "hgb_probability": ("a6_advanced_oof_predictions.hist_gradient_boosting_probability; a6_final_holdout_predictions.predicted_probability_hgb", "Direct frozen A6 scores"),
        },
    }
    source_fields = {
        "dashboard_msa_industry_year": {
            "msa_name": "cbsa_name", "sector_name": "sector_title",
            "expected_startup_rate": "expected_target_startup_rate",
            "observed_historical_gap_status": "gap_p20", "gap_label_predictor_year": "predictor_year",
            "alignment_label": "alignment_residual", "msa_observation_count": "row_count",
            "msa_sector_count": "sector_count", "msa_year_count": "year_count",
            "coverage_status": "eligible_for_comparison",
            "model_eligible_flag": "modeling_eligible",
        },
        "dashboard_model_predictions": {
            "cbsa_code": "cbsa_code (normalized from numeric/string source without changing identifier)",
            "msa_name": "cbsa_name", "sector_name": "sector_title",
            "predictor_year": "predictor_year", "target_year": "target_year",
            "actual_gap": "actual_gap", "development_or_holdout": "artifact split",
            "fold": "fold (development only)", "logistic_probability": "baseline_1_probability / predicted_probability_logistic",
            "hgb_probability": "hist_gradient_boosting_probability / predicted_probability_hgb",
            "primary_model_flag": "A6 final model lock", "coverage_status": "coverage_status",
        },
        "dashboard_model_summary": {
            "dataset_split": "dataset", "model": "model", "model_label": "A7 label dictionary",
            "metric": "source metric column", "value": "source metric value",
            "metric_label": "A7 label dictionary", "interpretation_order": "A7 metric ordering",
            "primary_metric_flag": "A7 metric policy", "primary_model_flag": "A6 final model lock",
            "sample_n": "N", "prevalence": "prevalence",
        },
        "dashboard_calibration": {
            "dataset_split": "artifact role", "model": "model (normalized name)",
            "risk_bin": "risk_bin", "n": "n", "mean_predicted_probability": "mean_predicted_probability",
            "observed_gap_prevalence": "observed_gap_prevalence",
        },
        "dashboard_model_by_year": {
            "sample_n": "N", "dataset_split": "A6 artifact role",
        },
        "dashboard_model_by_sector": {
            "sector_code": "sector", "sample_n": "N", "positive_n": "positive_N",
            "sector_name": "sector_title (analytical reference)", "dataset_split": "A6 artifact role",
        },
        "dashboard_model_by_msa_size": {
            "msa_count": "MSA_count", "sample_n": "N", "dataset_split": "A6 artifact role",
        },
        "dashboard_coverage": {
            "msa_name": "cbsa_name", "observation_count": "row_count", "sector_count": "sector_count",
            "year_count": "year_count", "first_year": "analytical panel year minimum",
            "last_year": "analytical panel year maximum",
            "comparison_eligible_flag": "eligible_for_comparison", "model_eligible_flag": "modeling_eligible",
            "coverage_status": "eligible_for_comparison plus fixed A5 rule",
            "coverage_note": "coverage_status and A5 rule explanation", "a6_oof_row_count": "a6_oof_rows",
        },
        "dashboard_sources": {
            "source_name": "metadata_source_manifest.source_name", "agency": "metadata_source_manifest.source_agency",
            "dataset": "metadata_source_manifest.dataset_name", "years_used": "source_year plus verified analytical period",
            "role_in_project": "A7 source-role mapping", "geography": "A7 lineage mapping",
            "industry_level": "A7 lineage mapping", "notes": "manifest vintage and A4/A6 notes",
            "source_category": "A7 source category",
        },
    }
    rows = []
    for dataset, frame in datasets.items():
        for field in frame.columns:
            source = direct.get(dataset, {}).get(field)
            if dataset == "dashboard_model_predictions":
                source = {
                    "cbsa_code": ("A6 predictions / analytical panel", "String normalization; no code reassignment"),
                    "msa_name": ("A6 holdout predictions / analytical panel", "Direct heldout label or predictor-year join"),
                    "sector_code": ("A6 prediction artifacts", "Direct; string-preserved"),
                    "sector_name": ("A6 holdout predictions / analytical panel", "Direct heldout label or predictor-year join"),
                    "predictor_year": ("A6 prediction artifacts.predictor_year", "Direct typed integer"),
                    "target_year": ("A6 prediction artifacts.target_year", "Direct; separately retained; t+3 validated"),
                    "actual_gap": ("A6 prediction artifacts.actual_gap", "Direct binary outcome; retrospective target"),
                    "development_or_holdout": ("A6 baseline/advanced OOF or final holdout artifact", "Source split assigned explicitly"),
                    "fold": ("A6 baseline/advanced OOF.fold", "Direct for development OOF; null for final holdout"),
                    "primary_model_flag": ("A6 final model lock", "True denotes logistic primary reference; HGB remains sensitivity"),
                    "coverage_status": ("A5/A6 coverage by CBSA", "Validated many-to-one join"),
                }.get(field, source)
            elif dataset == "dashboard_model_summary":
                source = ("a6_final_model_performance.csv", "Long-format reshape of finalized metric columns; values unchanged")
            elif dataset == "dashboard_calibration":
                source = ("A6 baseline/advanced calibration and a6_final_holdout_calibration.csv", "Direct bin summaries with explicit split label and normalized model name")
            elif dataset == "dashboard_model_by_year":
                source = ("a6_final_holdout_by_year.csv", "Direct finalized holdout subgroup metric; field rename only")
            elif dataset == "dashboard_model_by_sector":
                source = ("a6_final_holdout_by_sector.csv + analytical panel sector reference", "Direct metric/flag with validated sector-name join")
            elif dataset == "dashboard_model_by_msa_size":
                source = ("a6_final_holdout_by_msa_size.csv", "Direct finalized subgroup metric; field rename only")
            elif dataset == "dashboard_coverage":
                source = ("a5_msa_coverage.csv + a6_msa_coverage_audit.csv + analytical panel", "A5/A6 fields cross-checked; year endpoints from panel; status uses exact A5 thresholds")
            elif dataset == "dashboard_sources":
                source = ("metadata_source_manifest + A6 frozen artifacts", "Curated used-source rows; source years and agency from manifest")
            if source is None:
                source = ("A6/canonical source as documented in data dictionary", "Deterministic label/order/typed reshape; see data dictionary")
            upstream, transformation = source
            rows.append({
                "dashboard_dataset": dataset, "dashboard_field": field,
                "upstream_artifact": upstream,
                "upstream_field": source_fields.get(dataset, {}).get(field, field),
                "transformation": transformation, "verified": True,
                "notes": "See docs/ASSIGNMENT7_DATA_DICTIONARY.md for type, units, null handling, and display use.",
            })
    return pd.DataFrame(rows)


def build_data_layer_report(inventory: pd.DataFrame, checks: pd.DataFrame, metadata: dict) -> str:
    lines = [
        "# Assignment 7.2 Dashboard Data Layer",
        "",
        "## Executive Summary",
        "",
        "A7.2 produces a typed, local Parquet layer from the read-only A4 analytical view and finalized A5/A6 artifacts. No model was fit, no target/threshold was changed, and holdout outcomes remain retrospective.",
        "",
        "## Purpose",
        "",
        "Provide deterministic datasets and pure-Python loaders for the future Streamlit app without repeatedly scanning the full analytical database. No UI, Plotly chart, map, or deployment code is included.",
        "",
        "## Source Inventory and Lineage",
        "",
        "The read-only `v_analytics_msa_industry_year` supplies descriptive values and quality flags. A6 fold-validation rows supply historical expected rates/residuals/p20 labels only through 2020. Separate A6 baseline/advanced OOF and final holdout artifacts supply frozen scores. A5/A6 audits supply coverage. Full field-level lineage is in `reports/tables/a7_dashboard_lineage_audit.csv` and `docs/ASSIGNMENT7_SOURCE_LINEAGE.md`.",
        "",
        "## Dashboard Dataset Inventory",
        "",
        "| Dataset | Rows | Columns | Primary key | Size (bytes) | Pages | Model output | Holdout outcome |",
        "| --- | ---: | ---: | --- | ---: | --- | --- | --- |",
    ]
    for row in inventory.itertuples(index=False):
        lines.append(f"| `{row.dataset}` | {row.row_count} | {row.column_count} | `{row.primary_key}` | {row.file_size_bytes} | {row.dashboard_pages} | {row.contains_model_output} | {row.contains_holdout_outcome} |")
    lines += [
        "",
        "## Historical vs Predictive Semantics",
        "",
        "`dashboard_msa_industry_year.year` is a descriptive year. Its expected rate, alignment, and observed historical gap are populated only on A6 fold-validation target-year rows. `dashboard_model_predictions` is a separate pair-grain table with predictor year t and target year t+3; `actual_gap` is the later realized outcome. Development OOF and final holdout are explicit and never merged into a generic current score feed.",
        "",
        "## Coverage Policy",
        "",
        "A5 status uses its exact screen: >=100 rows, >=5 sectors, >=10 years. It maps to `comparison_eligible` or `thin`, is not a model reliability rating, and is validated against A5/A6 and analytical panel counts. A6 `model_eligible_flag` independently indicates any development OOF record.",
        "",
        "## Null Policy",
        "",
        "Source missingness/suppression and expected lack of historical A6 labels are preserved as Parquet nulls; no zero fill or UI imputation occurs. Holdout `fold` is null by design. Sector AP/ROC-AUC nulls retain A6 suppression below its event/no-negative-class rule. See `docs/ASSIGNMENT7_NULL_POLICY.md` and the generated field-level `docs/ASSIGNMENT7_DATA_DICTIONARY.md`.",
        "",
        "## Model Result Preservation",
        "",
        "Logistic is primary; HGB is sensitivity. Predictions, labels, cutoffs, and metrics are copied/reshaped from frozen A6 artifacts. The model summary reconciles from `a6_final_model_performance.csv`. No risk category is included because no non-holdout rule was frozen.",
        "",
        "## Quality Checks",
        "",
        f"{len(checks)} automated quality checks passed. Detailed names/results are in `reports/tables/a7_dashboard_quality_checks.csv`; the field-level audit is in `reports/tables/a7_dashboard_lineage_audit.csv`.",
        "",
        "## Filter Readiness",
        "",
        "`dashboard_filter_options.json` supplies CBSA/name, sector/name, descriptive years, observed historical binary gap values, and prediction availability/year options. It deliberately supplies no risk-category options. Model-performance metrics do not consume Explorer filters.",
        "",
        "## Reproducibility and Database Integrity",
        "",
        "Build with `uv run --offline python -m regional_entrepreneurship_intelligence.dashboard.run_data_layer`. Parquet uses PyArrow/Zstandard and stable table sorting; JSON is key-sorted, and metadata omits a volatile timestamp. All canonical database connections are read-only and query-only. Repeat-build output hashes are verified as a separate final QA step.",
        "",
        "## Readiness for A7.3",
        "",
        "The loader provides uncached pure-Python read functions and the contract preserves the A7.1 page/filter/model rules. A7.3 may build the Streamlit shell only after reviewing these schemas and the null/time-role rules. This report does not begin A7.3.",
        "",
    ]
    return "\n".join(lines)


def output_hashes(output_dir: Path = OUTPUT_DIR) -> dict[str, str]:
    paths = sorted(p for p in output_dir.iterdir() if p.is_file())
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
