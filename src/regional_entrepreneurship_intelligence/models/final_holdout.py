"""Locked Assignment 6.7 fit-and-evaluate workflow."""

from __future__ import annotations

import hashlib
import argparse
import re
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path
from urllib.parse import quote

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

from regional_entrepreneurship_intelligence.analysis.eda import DEFAULT_EDA_DATABASE
from regional_entrepreneurship_intelligence.models.advanced import (
    TREE_FEATURES,
    fit_advanced_model,
    predict_gap_probability,
)
from regional_entrepreneurship_intelligence.models.baseline import (
    EXTENDED_REQUIRED,
    MODEL_FEATURES,
    fit_logistic_baseline,
    lift_table,
    predict_gap_probability as predict_logistic_probability,
    probability_metrics,
    ranking_curve,
    threshold_metrics,
)
from regional_entrepreneurship_intelligence.models.expected import fit_expected_model, predict_expected

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "docs" / "ASSIGNMENT6_FINAL_MODEL_LOCK.md"
TABLE_DIR = ROOT / "reports" / "tables"
FIGURE_DIR = ROOT / "reports" / "figures"
REPORT_PATH = ROOT / "reports" / "assignment6_final_analytics_engine.md"
EXPECTED_FEATURES = (
    "startup_rate_lag1", "employment_growth", "acs_population_growth",
    "median_household_income", "educational_attainment_pct",
    "labor_force_participation_pct", "unemployment_rate", "sector_code", "year",
)
EXPECTED_FORMULA = (
    "startup_rate ~ startup_rate_lag1 + employment_growth + acs_population_growth + "
    "median_household_income + educational_attainment_pct + "
    "labor_force_participation_pct + unemployment_rate + C(sector_code) + C(year)"
)
HGB_PARAMS = {
    "max_iter": 120,
    "learning_rate": 0.05,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 30,
    "l2_regularization": 1.0,
}
HOLDOUT_PREDICTOR_YEARS = (2018, 2019, 2020)
HOLDOUT_TARGET_YEARS = (2021, 2022, 2023)
DEVELOPMENT_PREDICTOR_YEARS = tuple(range(2010, 2018))
DEVELOPMENT_TARGET_MAX = 2020
MIN_SECTOR_EVENTS = 30
MODEL_NAME = "baseline_1_simple"


def validate_locked_design(*, require_threshold: bool = False) -> None:
    """Fail closed if the implementation drifts from the committed model lock."""
    if not LOCK_PATH.is_file():
        raise FileNotFoundError(f"Committed model lock is missing: {LOCK_PATH}")
    lock_commit = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", str(LOCK_PATH.relative_to(ROOT))],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    if not lock_commit or subprocess.run(["git", "merge-base", "--is-ancestor", lock_commit, "HEAD"],
                                         cwd=ROOT, check=False).returncode != 0:
        raise AssertionError("Final model lock must be committed before any holdout query")
    if subprocess.run(["git", "status", "--porcelain", "--", str(LOCK_PATH.relative_to(ROOT))],
                      cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip():
        raise AssertionError("Final model lock has uncommitted edits")
    if MODEL_FEATURES[MODEL_NAME] != ("startup_rate", "startup_rate_lag1", "employment_growth", "sector_code", "year"):
        raise AssertionError("Simple logistic feature family differs from the final model lock")
    if tuple(TREE_FEATURES) != (
        "startup_rate", "startup_rate_lag1", "employment_growth", "acs_population_growth",
        "median_household_income", "educational_attainment_pct", "labor_force_participation_pct",
        "unemployment_rate", "sector_code", "year",
    ):
        raise AssertionError("HGB feature family differs from frozen A6.5")
    if HOLDOUT_PREDICTOR_YEARS != (2018, 2019, 2020) or HOLDOUT_TARGET_YEARS != (2021, 2022, 2023):
        raise AssertionError("Holdout calendar boundary changed")
    if require_threshold:
        threshold_path = TABLE_DIR / "a6_final_target_threshold.csv"
        if not threshold_path.is_file():
            raise FileNotFoundError("Development-only threshold must be frozen before holdout access")
        if subprocess.run(["git", "status", "--porcelain", "--", str(threshold_path.relative_to(ROOT))],
                          cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip():
            raise AssertionError("Development-only threshold artifact must be committed before holdout access")
        cutoff_match = re.search(r"Frozen numerical development p20 cutoff: `([-+0-9.eE]+)`", LOCK_PATH.read_text(encoding="utf-8"))
        if cutoff_match is None:
            raise AssertionError("Final model lock must contain the numeric development p20 cutoff")
        frozen = pd.read_csv(threshold_path).iloc[0]
        if not np.isclose(float(cutoff_match.group(1)), float(frozen.p20_residual_cutoff), rtol=0, atol=1e-12):
            raise AssertionError("Committed model lock and threshold artifact disagree")


def read_panel_readonly(database_path: Path, *, year_max: int | None = None,
                        years: tuple[int, ...] | None = None) -> pd.DataFrame:
    """Read the analytical view through a read-only SQLite connection."""
    uri = f"file:{quote(database_path.resolve().as_posix(), safe='/:')}?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        connection.execute("PRAGMA query_only = ON")
        if year_max is not None:
            panel = pd.read_sql_query("SELECT * FROM v_analytics_msa_industry_year WHERE year <= ?",
                                      connection, params=(year_max,))
        elif years is not None:
            placeholders = ",".join("?" for _ in years)
            panel = pd.read_sql_query(f"SELECT * FROM v_analytics_msa_industry_year WHERE year IN ({placeholders})",
                                      connection, params=years)
        else:
            panel = pd.read_sql_query("SELECT * FROM v_analytics_msa_industry_year", connection)
    for col in ("cbsa_code", "sector_code"):
        panel[col] = panel[col].astype(str)
    panel["year"] = pd.to_numeric(panel.year, errors="raise").astype(int)
    if panel.duplicated(["cbsa_code", "sector_code", "year"]).any():
        raise ValueError("Analytical panel must be unique by CBSA-sector-year")
    return panel.sort_values(["year", "cbsa_code", "sector_code"], kind="mergesort").reset_index(drop=True)


def exact_pairs(panel: pd.DataFrame, predictor_years: tuple[int, ...]) -> pd.DataFrame:
    """Pair present rows exactly three calendar years apart, never by row order."""
    if "year" not in panel or not {"cbsa_code", "sector_code"}.issubset(panel.columns):
        raise ValueError("Panel does not contain exact-pair keys")
    pred = panel.loc[panel.year.isin(predictor_years), ["cbsa_code", "sector_code", "year"]].rename(
        columns={"year": "predictor_year"})
    target = panel.loc[panel.year.isin([year + 3 for year in predictor_years]),
                       ["cbsa_code", "sector_code", "year"]].rename(columns={"year": "target_year"})
    target["predictor_year"] = target.target_year - 3
    pairs = pred.merge(target, on=["cbsa_code", "sector_code", "predictor_year"],
                       how="inner", validate="one_to_one")
    if not pairs.target_year.eq(pairs.predictor_year + 3).all():
        raise AssertionError("Pair builder violated exact t+3")
    return pairs[["cbsa_code", "sector_code", "predictor_year", "target_year"]].sort_values(
        ["predictor_year", "cbsa_code", "sector_code"], kind="mergesort").reset_index(drop=True)


def development_threshold(expected_model) -> tuple[pd.DataFrame, float]:
    """Get the final p20 cutoff exclusively from fitted development residuals."""
    if expected_model.training_year_end != DEVELOPMENT_TARGET_MAX:
        raise ValueError("Expected model must use the locked 2020 development cutoff")
    training_residuals = predict_expected(expected_model, expected_model.training_frame)
    if training_residuals.empty or int(training_residuals.year.max()) > DEVELOPMENT_TARGET_MAX:
        raise ValueError("Threshold residuals crossed the development boundary")
    cutoff = float(training_residuals.residual.quantile(0.20, interpolation="linear"))
    return training_residuals, cutoff


def freeze_development_threshold(database_path: Path = DEFAULT_EDA_DATABASE) -> dict:
    """Compute and persist the final target cutoff using a development-only query."""
    validate_locked_design()
    development = read_panel_readonly(Path(database_path), year_max=DEVELOPMENT_TARGET_MAX)
    if development.year.max() > DEVELOPMENT_TARGET_MAX:
        raise AssertionError("Threshold panel query exceeded the development boundary")
    expected_model = fit_expected_model(development, name="A", training_year_end=DEVELOPMENT_TARGET_MAX)
    residuals, cutoff = development_threshold(expected_model)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([{"expected_model": "Model A OLS", "training_year_max": DEVELOPMENT_TARGET_MAX,
                           "residual_N": len(residuals), "p20_residual_cutoff": cutoff,
                           "cutoff_rule": "development in-sample residual 20th percentile; linear interpolation",
                           "model_lock_sha256": hashlib.sha256(LOCK_PATH.read_bytes()).hexdigest(),
                           "lock_commit": subprocess.run(
                               ["git", "log", "-1", "--format=%H", "--", str(LOCK_PATH.relative_to(ROOT))],
                               cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()}])
    frame.to_csv(TABLE_DIR / "a6_final_target_threshold.csv", index=False)
    return frame.iloc[0].to_dict()


def attach_final_labels(pairs: pd.DataFrame, scored_targets: pd.DataFrame, cutoff: float) -> pd.DataFrame:
    """Attach expected-model residual labels to exact keys, preserving unavailable outcomes."""
    targets = scored_targets[["cbsa_code", "sector_code", "year", "startup_rate",
                              "expected_startup_rate", "residual"]].rename(
        columns={"year": "target_year", "startup_rate": "target_startup_rate",
                 "expected_startup_rate": "target_expected_startup_rate",
                 "residual": "target_alignment_residual"})
    targets["cbsa_code"] = targets.cbsa_code.astype(str)
    targets["sector_code"] = targets.sector_code.astype(str)
    result = pairs.merge(targets, on=["cbsa_code", "sector_code", "target_year"], how="left",
                         validate="one_to_one")
    result["gap_p20"] = result.target_alignment_residual.le(cutoff).where(
        result.target_alignment_residual.notna()).astype("Int64")
    return result


def attach_predictors(pairs: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    """Join predictor-year fields and name metadata without exposing target covariates."""
    fields = list(dict.fromkeys([*(name for name in EXTENDED_REQUIRED if name not in {"sector_code", "year"}),
                                 "acs_population", "cbsa_name", "sector_title"]))
    predictor = panel.loc[:, ["cbsa_code", "sector_code", "year", *fields]].copy()
    predictor["predictor_year"] = predictor.year.astype(int)
    if predictor.duplicated(["cbsa_code", "sector_code", "predictor_year"]).any():
        raise ValueError("Predictor panel contains duplicate keys")
    out = pairs.merge(predictor, on=["cbsa_code", "sector_code", "predictor_year"],
                      how="left", validate="many_to_one")
    if not out.year.astype(int).eq(out.predictor_year.astype(int)).all():
        raise ValueError("Feature rows did not come from predictor year t")
    return out


def eligibility_audit(candidates: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int | float]]:
    """Summarize exact candidates, label eligibility, complete-case eligibility, and exclusions."""
    candidates = candidates.copy()
    candidates["model_complete"] = candidates[list(EXTENDED_REQUIRED)].replace([np.inf, -np.inf], np.nan).notna().all(axis=1)
    candidates["eligible"] = candidates.gap_p20.notna() & candidates.model_complete
    valid = candidates[candidates.eligible].copy()
    total = len(candidates)
    summary = {
        "candidate_pairs": total,
        "target_label_eligible_pairs": int(candidates.gap_p20.notna().sum()),
        "complete_case_eligible_pairs": len(valid),
        "excluded_pairs": total - len(valid),
        "exclusion_share": (total - len(valid)) / total if total else float("nan"),
        "msa_n": int(valid.cbsa_code.nunique()),
        "sector_n": int(valid.sector_code.nunique()),
        "prevalence": float(valid.gap_p20.astype(int).mean()) if len(valid) else float("nan"),
    }
    return valid, summary


def _threshold_summary(y: np.ndarray, p: np.ndarray, thresholds: np.ndarray) -> dict[str, float | int]:
    if len(y) != len(p) or len(y) != len(thresholds):
        raise ValueError("Threshold evaluation arrays must align")
    pred = p >= thresholds
    tp = int(np.sum(pred & (y == 1)))
    fp = int(np.sum(pred & (y == 0)))
    tn = int(np.sum(~pred & (y == 0)))
    fn = int(np.sum(~pred & (y == 1)))
    recall = tp / (tp + fn) if tp + fn else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return {"true_positive": tp, "false_positive": fp, "true_negative": tn, "false_negative": fn,
            "recall": recall, "precision": precision, "f1": f1,
            "balanced_accuracy": (recall + specificity) / 2}


def performance_row(y, p, *, model: str, dataset: str, thresholds) -> dict:
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    threshold_array = np.broadcast_to(np.asarray(thresholds, dtype=float), p.shape)
    metrics = probability_metrics(y, p)
    lift = lift_table(pd.Series(y), p, cuts=(.10, .20, .25)).set_index("risk_cut")
    classified = _threshold_summary(y, p, threshold_array)
    return {
        "dataset": dataset, "model": model, "N": len(y), "prevalence": float(y.mean()),
        "AP": metrics["pr_auc"], "ROC_AUC": metrics["roc_auc"], "Brier": metrics["brier_score"],
        **classified,
        "classification_threshold": float(threshold_array[0]) if np.all(threshold_array == threshold_array[0]) else np.nan,
        "top10_lift": float(lift.loc[.10, "lift_ratio"]),
        "top20_lift": float(lift.loc[.20, "lift_ratio"]),
        "top25_lift": float(lift.loc[.25, "lift_ratio"]),
    }


def score_bins(actual, probabilities, *, model: str, bins: int = 10) -> pd.DataFrame:
    """Create stable equal-count score deciles; labels are used only for observed rates."""
    frame = pd.DataFrame({"actual": np.asarray(actual, dtype=int),
                          "probability": np.asarray(probabilities, dtype=float)})
    frame["order"] = np.arange(len(frame))
    frame = frame.sort_values(["probability", "order"], kind="mergesort").reset_index(drop=True)
    frame["risk_bin"] = np.minimum(np.arange(len(frame)) * bins // max(len(frame), 1) + 1, bins)
    return frame.groupby("risk_bin", as_index=False).agg(
        N=("actual", "size"), mean_predicted_probability=("probability", "mean"),
        observed_gap_prevalence=("actual", "mean")).assign(model=model)


def evaluate_final(database_path: Path = DEFAULT_EDA_DATABASE) -> dict:
    """Train the locked models on development only and evaluate their holdout scores."""
    validate_locked_design(require_threshold=True)
    panel = read_panel_readonly(Path(database_path), year_max=DEVELOPMENT_TARGET_MAX)
    if set((*DEVELOPMENT_PREDICTOR_YEARS, *HOLDOUT_PREDICTOR_YEARS)) - set(panel.year):
        raise ValueError("Development-only panel lacks required predictor years")

    # All variables used to fit Model A and set the threshold are bounded at 2020.
    expected_development = panel.copy()
    expected_model = fit_expected_model(expected_development, name="A", training_year_end=DEVELOPMENT_TARGET_MAX)
    training_scored, cutoff = development_threshold(expected_model)
    frozen_threshold = pd.read_csv(TABLE_DIR / "a6_final_target_threshold.csv").iloc[0]
    if frozen_threshold.final_model_lock_sha256 != hashlib.sha256(LOCK_PATH.read_bytes()).hexdigest():
        raise AssertionError("Model lock checksum differs from the committed threshold record")
    frozen_cutoff = float(frozen_threshold.p20_residual_cutoff)
    if not np.isclose(cutoff, frozen_cutoff, rtol=0, atol=1e-12):
        raise AssertionError("Recomputed development cutoff differs from committed frozen threshold")

    # Build unique development labels from final development residuals and exact calendar pairs.
    dev_pairs = exact_pairs(panel, DEVELOPMENT_PREDICTOR_YEARS)
    dev_pairs = dev_pairs[dev_pairs.target_year.le(DEVELOPMENT_TARGET_MAX)].copy()
    dev_labels = attach_final_labels(dev_pairs, training_scored, cutoff)
    dev_labels = dev_labels[dev_labels.target_year.le(DEVELOPMENT_TARGET_MAX)].copy()
    predictor_panel = panel[panel.year.isin(DEVELOPMENT_PREDICTOR_YEARS)].copy()
    dev = attach_predictors(dev_labels, predictor_panel)
    dev_eligible, dev_audit = eligibility_audit(dev)
    if dev_eligible.empty or dev_eligible.gap_p20.nunique() != 2:
        raise ValueError("Development classifier sample must contain both target classes")
    dev_eligible["gap_p20"] = dev_eligible.gap_p20.astype(int)
    dev_eligible = dev_eligible.sort_values(["predictor_year", "cbsa_code", "sector_code"], kind="mergesort").reset_index(drop=True)
    if dev_eligible.predictor_year.max() > 2017 or dev_eligible.target_year.max() > 2020:
        raise AssertionError("Development classifier sample crossed its locked cutoff")

    logistic = fit_logistic_baseline(dev_eligible, model=MODEL_NAME)
    hgb = fit_advanced_model(dev_eligible, model_name="hist_gradient_boosting", params=HGB_PARAMS)
    train_prevalence = float(dev_eligible.gap_p20.mean())

    # No holdout target-year row is queried until both fitted pipelines are frozen in memory.
    hold_target_panel = read_panel_readonly(Path(database_path), years=HOLDOUT_TARGET_YEARS)
    if set(hold_target_panel.year) != set(HOLDOUT_TARGET_YEARS):
        raise ValueError("Panel lacks one or more reserved target years")
    hold_target_scored = predict_expected(expected_model, hold_target_panel)
    hold_predictors = panel[panel.year.isin(HOLDOUT_PREDICTOR_YEARS)].copy()
    hold_pair_panel = pd.concat([hold_predictors, hold_target_panel], ignore_index=True, sort=False)
    hold_pairs = exact_pairs(hold_pair_panel, HOLDOUT_PREDICTOR_YEARS)
    hold_labels = attach_final_labels(hold_pairs, hold_target_scored, frozen_cutoff)
    hold = attach_predictors(hold_labels, hold_predictors)
    hold_eligible, hold_audit = eligibility_audit(hold)
    if hold_eligible.empty or hold_eligible.gap_p20.nunique() != 2:
        raise ValueError("Holdout complete-case sample must contain both target classes")
    hold_eligible["gap_p20"] = hold_eligible.gap_p20.astype(int)
    hold_eligible = hold_eligible.sort_values(["predictor_year", "cbsa_code", "sector_code"], kind="mergesort").reset_index(drop=True)
    if set(hold_eligible.predictor_year.unique()) != set(HOLDOUT_PREDICTOR_YEARS):
        raise ValueError("Holdout lacks one or more locked predictor years")
    if not hold_eligible.target_year.eq(hold_eligible.predictor_year + 3).all():
        raise AssertionError("Holdout rows are not exact t+3 pairs")
    hold_audit.update({
        "predictor_year_min": int(hold_eligible.predictor_year.min()),
        "predictor_year_max": int(hold_eligible.predictor_year.max()),
        "target_year_min": int(hold_eligible.target_year.min()),
        "target_year_max": int(hold_eligible.target_year.max()),
    })

    p_logit = predict_logistic_probability(logistic, hold_eligible)
    p_hgb = predict_gap_probability(hgb, hold_eligible)
    hold_eligible = hold_eligible.copy()
    hold_eligible["predicted_probability_logistic"] = p_logit
    hold_eligible["predicted_probability_hgb"] = p_hgb
    validate_prediction_rows(hold_eligible, len(hold_eligible))

    baseline_oof = pd.read_csv(TABLE_DIR / "a6_baseline_oof_predictions.csv",
                               dtype={"cbsa_code": str, "sector_code": str, "fold": str})
    advanced_oof = pd.read_csv(TABLE_DIR / "a6_advanced_oof_predictions.csv",
                                dtype={"cbsa_code": str, "sector_code": str, "fold": str})
    oof = baseline_oof.merge(advanced_oof[["fold", "cbsa_code", "sector_code", "predictor_year", "target_year",
                                           "actual_gap", "hist_gradient_boosting_probability"]],
                              on=["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"],
                              how="inner", suffixes=("", "_advanced"), validate="one_to_one")
    if not oof.actual_gap.eq(oof.actual_gap_advanced).all():
        raise ValueError("Locked logistic and HGB development OOF labels differ")
    thresholds = pd.read_csv(TABLE_DIR / "a6_baseline_model_performance.csv")
    thresholds = thresholds[(thresholds.split_role.eq("validation")) &
                            (thresholds.threshold_policy.eq("train_prevalence")) &
                            (thresholds.model.eq(MODEL_NAME))].set_index("fold").train_prevalence
    dev_thresholds = oof.fold.map(thresholds).to_numpy(dtype=float)
    baseline_thresholds = oof.fold.map(
        pd.read_csv(TABLE_DIR / "a6_baseline_model_performance.csv").query(
            "split_role == 'validation' and threshold_policy == 'train_prevalence' and model == 'baseline_0_prevalence'"
        ).set_index("fold").train_prevalence).to_numpy(dtype=float)
    performance = [
        performance_row(oof.actual_gap, oof.baseline_0_probability, model="prevalence_benchmark",
                        dataset="development_oof", thresholds=baseline_thresholds),
        performance_row(oof.actual_gap, oof.baseline_1_probability, model="logistic",
                        dataset="development_oof", thresholds=dev_thresholds),
        performance_row(oof.actual_gap, oof.hist_gradient_boosting_probability, model="hist_gradient_boosting",
                        dataset="development_oof", thresholds=dev_thresholds),
        performance_row(hold_eligible.gap_p20, np.repeat(train_prevalence, len(hold_eligible)),
                        model="prevalence_benchmark", dataset="holdout", thresholds=train_prevalence),
        performance_row(hold_eligible.gap_p20, p_logit, model="logistic", dataset="holdout", thresholds=train_prevalence),
        performance_row(hold_eligible.gap_p20, p_hgb, model="hist_gradient_boosting", dataset="holdout", thresholds=train_prevalence),
    ]
    performance = pd.DataFrame(performance)
    threshold_diagnostics = pd.DataFrame([
        {"model": model_name, "threshold_policy": "fixed_0.50_diagnostic", "classification_threshold": .5,
         **threshold_metrics(hold_eligible.gap_p20, probabilities, .5)}
        for model_name, probabilities in [("logistic", p_logit), ("hist_gradient_boosting", p_hgb)]
    ])

    prediction_cols = ["cbsa_code", "cbsa_name", "sector_code", "predictor_year", "target_year", "gap_p20",
                       "predicted_probability_logistic", "predicted_probability_hgb"]
    predictions = hold_eligible[prediction_cols].rename(columns={"gap_p20": "actual_gap"}).copy()
    predictions["sector_title"] = hold_eligible.sector_title.to_numpy()
    predictions = predictions.sort_values(["predictor_year", "cbsa_code", "sector_code"]).reset_index(drop=True)

    calibration = pd.concat([
        score_bins(hold_eligible.gap_p20, np.repeat(train_prevalence, len(hold_eligible)), model="prevalence_benchmark"),
        score_bins(hold_eligible.gap_p20, p_logit, model="logistic"),
        score_bins(hold_eligible.gap_p20, p_hgb, model="hist_gradient_boosting"),
    ], ignore_index=True).rename(columns={"N": "n"})

    by_year_rows = []
    for (predictor_year, target_year), group in hold_eligible.groupby(["predictor_year", "target_year"], sort=True):
        for model_name, col in [("logistic", "predicted_probability_logistic"),
                                ("hist_gradient_boosting", "predicted_probability_hgb")]:
            by_year_rows.append({"predictor_year": predictor_year, "target_year": target_year, "model": model_name,
                                 "N": len(group), "prevalence": group.gap_p20.mean(),
                                 **probability_metrics(group.gap_p20, group[col].to_numpy())})
    by_year = pd.DataFrame(by_year_rows).rename(columns={"pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"})

    sector_rows = []
    for sector, group in hold_eligible.groupby("sector_code", sort=True):
        positives = int(group.gap_p20.sum())
        sufficient = positives >= MIN_SECTOR_EVENTS and positives < len(group)
        for model_name, col in [("logistic", "predicted_probability_logistic"),
                                ("hist_gradient_boosting", "predicted_probability_hgb")]:
            metric = probability_metrics(group.gap_p20, group[col].to_numpy()) if sufficient else {
                "pr_auc": np.nan, "roc_auc": np.nan}
            sector_rows.append({"sector": sector, "N": len(group), "positive_N": positives,
                                "prevalence": group.gap_p20.mean(), "model": model_name,
                                "AP": metric["pr_auc"], "ROC_AUC": metric["roc_auc"],
                                "sufficient_sample_flag": sufficient})
    by_sector = pd.DataFrame(sector_rows)

    # A6.6 rule: training-MSA median predictor-year population, with cutpoints estimated in development.
    msa_population = dev_eligible.groupby("cbsa_code").acs_population.median().dropna()
    size_cutpoints = msa_population.quantile([1 / 3, 2 / 3]).to_numpy()
    if len(size_cutpoints) != 2 or not np.isfinite(size_cutpoints).all() or size_cutpoints[0] >= size_cutpoints[1]:
        raise ValueError("Development population distribution cannot define distinct size terciles")
    hold_eligible["msa_size_group"] = pd.cut(
        hold_eligible.acs_population, [-np.inf, *size_cutpoints, np.inf],
        labels=["small", "middle", "large"], include_lowest=True)
    size_rows = []
    for group_name, group in hold_eligible.groupby("msa_size_group", observed=True, sort=False):
        for model_name, col in [("logistic", "predicted_probability_logistic"),
                                ("hist_gradient_boosting", "predicted_probability_hgb")]:
            size_rows.append({"msa_size_group": str(group_name), "MSA_count": group.cbsa_code.nunique(),
                              "N": len(group), "prevalence": group.gap_p20.mean(), "model": model_name,
                              **probability_metrics(group.gap_p20, group[col].to_numpy()),
                              "top10_lift": float(lift_table(group.gap_p20, group[col].to_numpy(), cuts=(.10,)).iloc[0].lift_ratio)})
    by_size = pd.DataFrame(size_rows).rename(columns={"pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"})

    _write_outputs(performance, threshold_diagnostics, predictions, calibration, by_year, by_sector, by_size,
                   hold_eligible, dev_eligible, dev_audit, hold_audit, cutoff, training_scored,
                   train_prevalence, p_logit, p_hgb, oof, logistic, size_cutpoints)
    return {"performance": performance, "predictions": predictions, "calibration": calibration,
            "by_year": by_year, "by_sector": by_sector, "by_size": by_size,
            "cutoff": cutoff, "train_prevalence": train_prevalence,
            "development_audit": dev_audit, "holdout_audit": hold_audit}


def validate_prediction_rows(predictions: pd.DataFrame, eligible_n: int) -> None:
    required = {"cbsa_code", "sector_code", "predictor_year", "target_year",
                "predicted_probability_logistic", "predicted_probability_hgb"}
    if not required.issubset(predictions.columns) or len(predictions) != eligible_n:
        raise ValueError("Every eligible holdout row must receive one score from each locked model")
    if predictions.duplicated(["cbsa_code", "sector_code", "predictor_year", "target_year"]).any():
        raise ValueError("Duplicate holdout prediction keys")
    if not predictions.target_year.eq(predictions.predictor_year + 3).all():
        raise ValueError("Holdout predictions must preserve exact t+3 keys")
    for col in ("predicted_probability_logistic", "predicted_probability_hgb"):
        if predictions[col].isna().any() or not predictions[col].between(0, 1).all():
            raise ValueError(f"Invalid probability values in {col}")


def _write_outputs(performance, threshold_diagnostics, predictions, calibration, by_year, by_sector, by_size,
                   hold, dev, dev_audit, hold_audit, cutoff, training_residuals,
                   train_prevalence, p_logit, p_hgb, oof, logistic, size_cutpoints):
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    performance.to_csv(TABLE_DIR / "a6_final_model_performance.csv", index=False)
    threshold_diagnostics.to_csv(TABLE_DIR / "a6_final_threshold_diagnostics.csv", index=False)
    predictions.to_csv(TABLE_DIR / "a6_final_holdout_predictions.csv", index=False)
    calibration.to_csv(TABLE_DIR / "a6_final_holdout_calibration.csv", index=False)
    by_year.to_csv(TABLE_DIR / "a6_final_holdout_by_year.csv", index=False)
    by_sector.to_csv(TABLE_DIR / "a6_final_holdout_by_sector.csv", index=False)
    by_size.to_csv(TABLE_DIR / "a6_final_holdout_by_msa_size.csv", index=False)
    pd.DataFrame([{"sample": "development", **dev_audit,
                   "predictor_year_min": int(dev.predictor_year.min()), "predictor_year_max": int(dev.predictor_year.max()),
                   "target_year_min": int(dev.target_year.min()), "target_year_max": int(dev.target_year.max())},
                  {"sample": "holdout", **hold_audit,
                   "predictor_year_min": int(hold.predictor_year.min()), "predictor_year_max": int(hold.predictor_year.max()),
                   "target_year_min": int(hold.target_year.min()), "target_year_max": int(hold.target_year.max())}]
                 ).to_csv(TABLE_DIR / "a6_final_sample_audit.csv", index=False)
    pd.DataFrame([{"msa_population_lower_tercile_cutpoint": size_cutpoints[0],
                   "msa_population_upper_tercile_cutpoint": size_cutpoints[1],
                   "basis": "development eligible MSA median predictor-year ACS population"}]
                 ).to_csv(TABLE_DIR / "a6_final_msa_size_cutpoints.csv", index=False)
    _write_research_mapping(TABLE_DIR / "a6_final_research_question_mapping.csv", performance, by_sector)
    figures = _figures(performance, hold, oof, p_logit, p_hgb, calibration, by_year, by_size)
    _write_report(performance, threshold_diagnostics, predictions, calibration, by_year, by_sector, by_size,
                  dev_audit, hold_audit, cutoff, train_prevalence, training_residuals,
                  logistic, figures)


def _figures(performance, hold, oof, p_logit, p_hgb, calibration, by_year, by_size):
    made = []

    def save(name, fig):
        fig.tight_layout()
        fig.savefig(FIGURE_DIR / f"a6_final_{name}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)
        made.append(f"a6_final_{name}.png")

    comparisons = [("AP", "Average precision", "ap"), ("ROC_AUC", "ROC-AUC", "roc_auc"),
                   ("Brier", "Brier score", "brier")]
    dev_ref = {"logistic": performance.query("dataset == 'development_oof' and model == 'logistic'").iloc[0],
               "hist_gradient_boosting": performance.query("dataset == 'development_oof' and model == 'hist_gradient_boosting'").iloc[0]}
    hold_ref = {"logistic": performance.query("dataset == 'holdout' and model == 'logistic'").iloc[0],
                "hist_gradient_boosting": performance.query("dataset == 'holdout' and model == 'hist_gradient_boosting'").iloc[0]}
    for metric, title, name in comparisons:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        x = np.arange(2)
        width = .34
        for j, model_name in enumerate(("logistic", "hist_gradient_boosting")):
            vals = [dev_ref[model_name][metric], hold_ref[model_name][metric]]
            ax.bar(x + (j - .5) * width, vals, width, label=model_name.replace("_", " ").title())
        ax.set_xticks(x, ["Development OOF", "Final holdout"])
        ax.set(title=f"Development versus holdout {title}", ylabel=title)
        ax.legend(frameon=False)
        save(f"{name}_comparison", fig)

    fig, ax = plt.subplots(figsize=(6.5, 5))
    for model, col in [("Logistic", "predicted_probability_logistic"),
                       ("HistGradientBoosting", "predicted_probability_hgb")]:
        recall, precision, _, _ = ranking_curve(hold.gap_p20, hold[col].to_numpy())
        ax.plot(recall, precision, label=model)
    ax.axhline(hold.gap_p20.mean(), linestyle="--", color="gray", label="Holdout prevalence")
    ax.set(title="Final holdout precision-recall", xlabel="Recall", ylabel="Precision", xlim=(0, 1), ylim=(0, 1))
    ax.legend(frameon=False)
    save("precision_recall", fig)

    fig, ax = plt.subplots(figsize=(6.5, 5))
    for model, col in [("Logistic", "predicted_probability_logistic"),
                       ("HistGradientBoosting", "predicted_probability_hgb")]:
        fpr, tpr, _ = roc_curve(hold.gap_p20, hold[col])
        ax.plot(fpr, tpr, label=model)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.set(title="Final holdout ROC curve", xlabel="False-positive rate", ylabel="True-positive rate", xlim=(0, 1), ylim=(0, 1))
    ax.legend(frameon=False)
    save("roc_curve", fig)

    fig, ax = plt.subplots(figsize=(6.5, 5))
    for model, group in calibration.groupby("model"):
        ax.plot(group.mean_predicted_probability, group.observed_gap_prevalence, marker="o", label=model.replace("_", " ").title())
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.set(title="Final holdout calibration deciles", xlabel="Mean predicted probability", ylabel="Observed gap prevalence", xlim=(0, 1), ylim=(0, 1))
    ax.legend(frameon=False)
    save("calibration", fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for model, group in calibration.groupby("model"):
        ax.plot(group.risk_bin, group.observed_gap_prevalence, marker="o", label=model.replace("_", " ").title())
    ax.set(title="Observed gaps by holdout risk decile", xlabel="Risk decile (low to high)", ylabel="Observed gap prevalence")
    ax.legend(frameon=False)
    save("risk_deciles", fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    from regional_entrepreneurship_intelligence.models.baseline import lift_table
    for model, col in [("Logistic", "predicted_probability_logistic"),
                       ("HistGradientBoosting", "predicted_probability_hgb")]:
        lift = lift_table(hold.gap_p20, hold[col].to_numpy(), cuts=(.10, .20, .25))
        ax.plot(lift.risk_cut * 100, lift.lift_ratio, marker="o", label=model)
    ax.axhline(1, linestyle="--", color="gray")
    ax.set(title="Final holdout top-risk lift", xlabel="Selected highest-risk share (%)", ylabel="Lift")
    ax.legend(frameon=False)
    save("lift", fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for model, group in by_year.groupby("model"):
        ax.plot(group.target_year, group.AP, marker="o", label=model.replace("_", " ").title())
    ax.set(title="Holdout average precision by target year", xlabel="Target year", ylabel="Average precision")
    ax.legend(frameon=False)
    save("by_year", fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for model, group in by_size.groupby("model"):
        ax.plot(group.msa_size_group, group.AP, marker="o", label=model.replace("_", " ").title())
    ax.set(title="Holdout average precision by MSA size", xlabel="Development-defined MSA population group", ylabel="Average precision")
    ax.legend(frameon=False)
    save("by_msa_size", fig)
    return made


def _markdown(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)

    def format_value(value) -> str:
        if pd.isna(value):
            return ""
        if isinstance(value, (float, np.floating)):
            return f"{value:.3f}"
        return str(value)

    rows = [[format_value(value) for value in row]
            for row in frame.itertuples(index=False, name=None)]
    lines = ["| " + " | ".join(columns) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _write_research_mapping(path: Path, performance: pd.DataFrame, sectors: pd.DataFrame) -> None:
    logit = performance.query("dataset == 'holdout' and model == 'logistic'").iloc[0]
    baseline = performance.query("dataset == 'holdout' and model == 'prevalence_benchmark'").iloc[0]
    mapping = pd.DataFrame([
        {"research_item": "Primary research question", "status": "supported" if logit.AP > logit.prevalence and logit.ROC_AUC > .5 else "not supported",
         "evidence": "Holdout AP relative to natural prevalence and secondary ranking discrimination", "interpretation": "Predictive association only; no causal claim."},
        {"research_item": "H1: predictors improve over baseline", "status": "supported" if logit.AP > baseline.AP and logit.Brier < baseline.Brier else "partially supported",
         "evidence": "Locked logistic compared with development-prevalence benchmark on identical holdout rows", "interpretation": "Incremental predictive value, conditional on complete cases."},
        {"research_item": "H2: industry growth positively associated with entrepreneurship", "status": "descriptive support only",
         "evidence": "A5 descriptive association and A6.2 expected-startup specification", "interpretation": "Association does not establish that growth causes entrepreneurship."},
        {"research_item": "H3: prior entrepreneurship reduces future gap risk", "status": "descriptive support only",
         "evidence": "Lag-1 startup-rate predictor and A6.6 startup-history sensitivity", "interpretation": "Predictive signal is not a causal effect."},
        {"research_item": "H4: industry relationships vary by sector", "status": "partially supported" if sectors.sufficient_sample_flag.any() else "not supported",
         "evidence": "Development sector ablation and supported-event holdout sector metrics", "interpretation": "Subgroup estimates are descriptive and may be unstable."},
    ])
    mapping.to_csv(path, index=False)


def _write_report(performance, threshold_diagnostics, predictions, calibration, by_year, by_sector, by_size,
                  dev_audit, hold_audit, cutoff, train_prevalence, training_residuals,
                  logistic, figures):
    final = performance.query("dataset == 'holdout'")
    logit = final[final.model.eq("logistic")].iloc[0]
    hgb = final[final.model.eq("hist_gradient_boosting")].iloc[0]
    base = final[final.model.eq("prevalence_benchmark")].iloc[0]
    dev_logit = performance.query("dataset == 'development_oof' and model == 'logistic'").iloc[0]
    dev_hgb = performance.query("dataset == 'development_oof' and model == 'hist_gradient_boosting'").iloc[0]
    mapping = pd.read_csv(TABLE_DIR / "a6_final_research_question_mapping.csv")
    evidence = "strong" if logit.AP >= max(logit.prevalence * 2, dev_logit.AP * .9) and logit.ROC_AUC >= .70 else (
        "meaningful" if logit.AP > logit.prevalence * 1.5 and logit.ROC_AUC > .60 else (
            "modest" if logit.AP > logit.prevalence and logit.ROC_AUC > .5 else "weak"))
    declines = {"AP": logit.AP - dev_logit.AP, "ROC_AUC": logit.ROC_AUC - dev_logit.ROC_AUC,
                "Brier": logit.Brier - dev_logit.Brier, "top10_lift": logit.top10_lift - dev_logit.top10_lift}
    report = f"""# Assignment 6 Final Analytics Engine

## Executive Summary

The locked simple logistic model achieved holdout AP {logit.AP:.3f} at {logit.prevalence:.1%} prevalence (AP/prevalence {logit.AP / logit.prevalence:.2f}), ROC-AUC {logit.ROC_AUC:.3f}, Brier {logit.Brier:.3f}, and top-decile lift {logit.top10_lift:.2f}x. Evidence classification: **{evidence}**. The final temporal test covers {int(hold_audit['complete_case_eligible_pairs']):,} complete-case MSA-sector-year observations from {hold_audit['msa_n']} MSAs and {hold_audit['sector_n']} sectors. The model was not changed after evaluation.

## Research Objective

Predict whether an MSA-industry combination will fall below its expected entrepreneurial activity exactly three years later. The operational outcome is BDS firm startup rate relative to an expected-rate benchmark, not all dimensions of entrepreneurship.

## Final Locked Design

The lock was committed before holdout scoring in `docs/ASSIGNMENT6_FINAL_MODEL_LOCK.md`. Model A is the OLS expected-startup model; the primary predictive model is A6.4 Baseline 1 logistic (`startup_rate`, `startup_rate_lag1`, `employment_growth`, sector contrasts, standardized predictor-year trend). ACS controls are not predictors of the primary model. The frozen A6.5 HistGradientBoosting model is a sensitivity and uses its extended feature family/configuration. Both models use the same A6.4 complete-case analysis population. No tuning, threshold selection, or feature change used holdout outcomes.

## Final Training Population

Development target years end in 2020; classifier predictors end in 2017. There are {dev_audit['candidate_pairs']:,} exact candidate pairs, {dev_audit['complete_case_eligible_pairs']:,} complete-case eligible training pairs from {dev_audit['msa_n']} MSAs. The classifier sample requires the frozen A6.4 extended completeness rule, although the primary logistic fit itself uses only its locked simple predictors.

## Holdout Construction

Pairs match the same CBSA and sector at predictor year `t` and target year `t+3`. The expected model was fit only on complete observations through 2020. The final p20 threshold is **{cutoff:.6f}** startup-rate points, calculated as the linear-interpolated 20th percentile of {len(training_residuals):,} in-sample development residuals. For 2021-2023 expected values, the training year-effect rule carries 2020 forward. Target-year covariates are confined to label construction and never enter classifier `X_t`.

## Holdout Sample

There are {hold_audit['candidate_pairs']:,} exact calendar candidate pairs; {hold_audit['target_label_eligible_pairs']:,} have eligible expected-model target labels; {hold_audit['complete_case_eligible_pairs']:,} are complete-case eligible for the locked model comparison. Excluded: {hold_audit['excluded_pairs']:,} ({hold_audit['exclusion_share']:.1%}). Holdout prevalence is {hold_audit['prevalence']:.1%}; predictors {hold_audit['predictor_year_min']}-{hold_audit['predictor_year_max']} map exactly to outcomes {hold_audit['target_year_min']}-{hold_audit['target_year_max']}. Development and holdout use identical feature eligibility rules.

## Final Logistic Model

The regularized binomial GLM uses training-only means/scales and sector contrasts. The primary diagnostic probability threshold is the final development label prevalence ({train_prevalence:.4f}); 0.50 is also retained as a diagnostic, not optimized for deployment. The primary threshold metrics in the tables use the frozen prevalence policy.

## Holdout Predictive Performance

{_markdown(final[['model','N','prevalence','AP','ROC_AUC','Brier','recall','precision','f1','balanced_accuracy','top10_lift','top20_lift','top25_lift']])}

Holdout AP is interpreted relative to the observed {logit.prevalence:.1%} prevalence. Logistic AP is {logit.AP / logit.prevalence:.2f} times prevalence; AP remains a ranking metric, not a probability-calibration statistic. ROC-AUC {logit.ROC_AUC:.3f} is above random ranking (0.50), without treating 0.80 as a pass/fail rule. The development-prevalence benchmark's holdout AP is {base.AP:.3f}, equal to the natural prevalence up to tie behavior.

## Comparison with Development

| Metric | Logistic holdout | HGB holdout | Logistic development OOF | Holdout minus development logistic |
| --- | ---: | ---: | ---: | ---: |
| AP | {logit.AP:.3f} | {hgb.AP:.3f} | {dev_logit.AP:.3f} | {declines['AP']:+.3f} |
| ROC-AUC | {logit.ROC_AUC:.3f} | {hgb.ROC_AUC:.3f} | {dev_logit.ROC_AUC:.3f} | {declines['ROC_AUC']:+.3f} |
| Brier | {logit.Brier:.3f} | {hgb.Brier:.3f} | {dev_logit.Brier:.3f} | {declines['Brier']:+.3f} |
| Top-10 lift | {logit.top10_lift:.3f} | {hgb.top10_lift:.3f} | {dev_logit.top10_lift:.3f} | {declines['top10_lift']:+.3f} |

Comparisons reference development OOF from the pre-existing A6.4/A6.5 outputs, which use fold-local targets and fold-specific training-prevalence thresholds. The final refit uses one development-only threshold and its resulting unique development labels; that distinction is retained rather than falsely treating the two label constructions as identical.

## HistGradientBoosting Sensitivity

HGB AP is {hgb.AP:.3f}, ROC-AUC {hgb.ROC_AUC:.3f}, Brier {hgb.Brier:.3f}, top-10 lift {hgb.top10_lift:.2f}x. Its AP difference from logistic is {hgb.AP - logit.AP:+.3f}. This does not trigger a model switch: complexity was not selected on the holdout, and one temporal result is insufficient to replace the interpretable reference.

## Calibration

Calibration uses score-ranked equal-count deciles; outcomes contribute only the observed rate. See `a6_final_holdout_calibration.csv`. Deviations between mean predicted risk and observed prevalence describe calibration limitations; no holdout recalibration was performed.

## Lift

The lift table reports tie-aware observed prevalence in the top 10%, 20%, and 25%, divided by overall holdout prevalence. Selected counts use ceiling of the corresponding sample fraction. These are prioritization statistics, not causal treatment effects.

## Recall / Precision

At the frozen development-prevalence diagnostic threshold, logistic recall is {logit.recall:.3f}, precision {logit.precision:.3f}, F1 {logit.f1:.3f}, and balanced accuracy {logit.balanced_accuracy:.3f}; confusion counts are in `a6_final_model_performance.csv`. Threshold 0.50 was also evaluated without selecting between thresholds based on holdout outcomes.

Fixed 0.50 diagnostic results:

{_markdown(threshold_diagnostics)}

## Performance by Year

{_markdown(by_year)}

Target years 2021, 2022, and 2023 reflect pandemic and post-pandemic conditions. Year-specific fluctuations are descriptive; they are neither removed nor used for retuning and do not establish causal pandemic effects.

## Performance by Sector

{_markdown(by_sector)}

Sector metrics are withheld where positive events are below {MIN_SECTOR_EVENTS} or no negative cases remain. Sector heterogeneity is informative, but some cell metrics remain unstable.

## Performance by MSA Size

{_markdown(by_size)}

Size groups follow A6.6: MSA-level median predictor-year population among eligible development MSAs defines 1/3 and 2/3 cutpoints, then holdout predictor-year population is assigned to small/middle/large. Cutpoints are training-only; differences are conditional on complete cases.

## Robustness Summary

A6.6 found p10/p25/mean-minus-SD target definitions retained ranking signal; Huber-based labels agreed about 96% with OLS labels; sector identity was strongly informative; high-risk lift persisted; and geographic/size performance varied. Complete-case selection was patterned. These findings motivate qualified claims, not certainty.

## Research Question and Hypothesis Assessment

{_markdown(mapping)}

H1 is evaluated against the natural-prevalence benchmark on the same holdout sample. H2-H4 are assessed as descriptive/predictive associations using the prior A5/A6 analyses; none is a causal test.

## Practical Interpretation

The model is an early-warning and prioritization aid for identifying MSA-industry combinations that appear at elevated risk of future entrepreneurial under-response relative to observable economic conditions. It is not deterministic and should not be used as an automatic allocation rule.

## Limitations

Firm startup rate is narrower than entrepreneurship broadly; sectors are aggregated to 2-digit NAICS; complete-case selection excludes a patterned subset; metro and sector coverage is uneven; and the historical 2010-2023 period may not generalize to future regimes. Calibration and subgroup performance need scrutiny. Predictive associations do not identify interventions or causes.

## What the Model Can Claim

- Within this eligible historical holdout, it can rank future gap risk above the natural-prevalence-only benchmark when AP exceeds prevalence and lift is above one.
- Sector and entrepreneurial history contain predictive information in the analyzed sample.
- The top-risk groups can concentrate observed future gaps, subject to reported lift and calibration.

## What the Model Cannot Claim

- It cannot claim causality, universal generalizability, perfect case identification, comprehensive entrepreneurship coverage, or equal performance across all MSAs/sectors.
- It cannot guarantee performance outside the observed historical context without new validation.
- It does not measure every startup outcome or within-sector variation below 2-digit NAICS.

## Assignment 6 Completion

The final holdout was evaluated only after the model lock commit. No post-holdout model changes or Assignment 7/dashboard work are included. Outputs are reproducible from the locked runner; historical A6.1-A6.6 artifacts remain frozen.

Figures: {', '.join(f'`reports/figures/{name}`' for name in figures)}
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def output_hashes() -> dict[str, str]:
    """SHA-256 hashes for deterministic final CSV reproducibility checks."""
    paths = sorted(TABLE_DIR.glob("a6_final_*.csv"))
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-development-threshold", action="store_true",
                        help="Read only panel years through 2020 and freeze the final p20 target cutoff")
    parser.add_argument("--database", type=Path, default=DEFAULT_EDA_DATABASE)
    args = parser.parse_args()
    if args.freeze_development_threshold:
        result = freeze_development_threshold(args.database)
        print(pd.Series(result).to_string())
    else:
        result = evaluate_final(args.database)
        print(result["performance"].query("dataset == 'holdout'").to_string(index=False))
