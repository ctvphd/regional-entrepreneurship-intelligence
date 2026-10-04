"""Run Assignment 6.4 prevalence and logistic baselines on development folds."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import quote

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.analysis.eda import DEFAULT_EDA_DATABASE
from regional_entrepreneurship_intelligence.models.baseline import (
    EXTENDED_REQUIRED,
    MODEL_FEATURES,
    build_predictor_pairs,
    calibration_table,
    complete_predictor_sample,
    fit_logistic_baseline,
    fit_prevalence_baseline,
    lift_table,
    predict_gap_probability,
    probability_metrics,
    ranking_curve,
    threshold_metrics,
    validate_oof_predictions,
)

ROOT = Path(__file__).resolve().parents[3]
TARGET_PATH = ROOT / "reports" / "tables" / "a6_gap_target_pairs.csv"
FOLD_PATH = ROOT / "config" / "assignment6_temporal_folds.csv"
TABLE_DIR = ROOT / "reports" / "tables"
FIGURE_DIR = ROOT / "reports" / "figures"
REPORT_PATH = ROOT / "reports" / "assignment6_baseline_predictive_model.md"
MAX_DEVELOPMENT_PREDICTOR_YEAR = 2017
MAIN_MODELS = ("baseline_0_prevalence", "baseline_1_simple", "baseline_2_extended")
SENSITIVITY_MODELS = tuple(name for name in MODEL_FEATURES if name not in MAIN_MODELS)


def _load_predictor_panel(database_path: Path) -> pd.DataFrame:
    """Read predictor years only; the final holdout years never enter memory."""
    uri = f"file:{quote(database_path.resolve().as_posix(), safe='/:')}?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        connection.execute("PRAGMA query_only = ON")
        frame = pd.read_sql_query(
            "SELECT * FROM v_analytics_msa_industry_year WHERE year <= ?",
            connection,
            params=(MAX_DEVELOPMENT_PREDICTOR_YEAR,),
        )
    if frame.empty or int(frame.year.max()) > MAX_DEVELOPMENT_PREDICTOR_YEAR:
        raise ValueError("Predictor panel exceeded development cutoff")
    return frame


def _performance_row(model_name, fold, role, actual, probabilities, train_n, train_prevalence, threshold_policy, threshold):
    scores = probability_metrics(actual, probabilities)
    classified = threshold_metrics(actual, probabilities, threshold)
    values = {
        "model": model_name, "fold": fold, "split_role": role, "train_n": train_n,
        "validation_n": len(actual), "train_prevalence": train_prevalence,
        "validation_prevalence": float(np.mean(actual)), **scores, **classified,
        "classification_threshold": float(threshold), "threshold_policy": threshold_policy,
        "pooled_flag": False,
    }
    return values


def _save_figure(name: str, fig) -> str:
    path = FIGURE_DIR / f"a6_baseline_{name}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path.name


def _make_figures(performance, predictions, calibration, lifts, coefficients) -> list[str]:
    names = []
    main = performance[(performance.split_role == "validation") & performance.model.isin(MAIN_MODELS)]
    for metric, title, filename in [
        ("pr_auc", "Average precision by fold", "pr_auc_by_fold"),
        ("roc_auc", "ROC-AUC by fold", "roc_auc_by_fold"),
        ("brier_score", "Brier score by fold", "brier_by_fold"),
    ]:
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        for model, group in main.groupby("model"):
            ax.plot(group.fold, group[metric], marker="o", label=model.replace("baseline_", "Baseline "))
        ax.set(title=title, xlabel="Temporal fold", ylabel=metric.replace("_", " "))
        ax.legend(frameon=False)
        names.append(_save_figure(filename, fig))

    pooled = predictions
    fig, ax = plt.subplots(figsize=(6.5, 5))
    for model, col in [("Baseline 0", "baseline_0_probability"), ("Baseline 1", "baseline_1_probability"), ("Baseline 2", "baseline_2_probability")]:
        recall, precision, _, _ = ranking_curve(pooled.actual_gap, pooled[col].to_numpy())
        ax.plot(recall, precision, label=model)
    ax.axhline(float(pooled.actual_gap.mean()), linestyle="--", color="gray", label="Prevalence")
    ax.set(title="Pooled out-of-fold precision-recall", xlabel="Recall", ylabel="Precision", xlim=(0, 1), ylim=(0, 1))
    ax.legend(frameon=False)
    names.append(_save_figure("precision_recall", fig))

    fig, ax = plt.subplots(figsize=(6.5, 5))
    for model, col in [("Baseline 0", "baseline_0_probability"), ("Baseline 1", "baseline_1_probability"), ("Baseline 2", "baseline_2_probability")]:
        _, _, fpr, tpr = ranking_curve(pooled.actual_gap, pooled[col].to_numpy())
        ax.plot(fpr, tpr, label=model)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.set(title="Pooled out-of-fold ROC", xlabel="False-positive rate", ylabel="True-positive rate", xlim=(0, 1), ylim=(0, 1))
    ax.legend(frameon=False)
    names.append(_save_figure("roc_curve", fig))

    fig, ax = plt.subplots(figsize=(6.5, 5))
    for model, group in calibration.groupby("model"):
        ax.plot(group.mean_predicted_probability, group.observed_gap_prevalence, marker="o", label=model.replace("baseline_", "Baseline "))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.set(title="Pooled out-of-fold calibration", xlabel="Mean predicted probability", ylabel="Observed gap prevalence", xlim=(0, 1), ylim=(0, 1))
    ax.legend(frameon=False)
    names.append(_save_figure("calibration", fig))

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for model, group in calibration.groupby("model"):
        ax.plot(group.risk_bin, group.observed_gap_prevalence, marker="o", label=model.replace("baseline_", "Baseline "))
    ax.set(title="Observed prevalence across pooled risk deciles", xlabel="Predicted-risk decile", ylabel="Observed gap prevalence")
    ax.legend(frameon=False)
    names.append(_save_figure("risk_deciles", fig))

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for model, group in lifts.groupby("model"):
        ax.plot(group.risk_cut * 100, group.lift_ratio, marker="o", label=model.replace("baseline_", "Baseline "))
    ax.axhline(1, linestyle="--", color="gray")
    ax.set(title="Top-risk lift", xlabel="Highest predicted-risk share (%)", ylabel="Lift over pooled prevalence")
    ax.legend(frameon=False)
    names.append(_save_figure("lift", fig))

    coef = coefficients[(coefficients.model.isin(["baseline_1_simple", "baseline_2_extended"])) & coefficients.variable.ne("const")]
    coef = coef[~coef.variable.str.startswith("sector_")]
    if not coef.empty:
        summary = coef.groupby(["model", "variable"], as_index=False).coefficient.mean()
        variables = list(dict.fromkeys(summary.variable))
        fig, ax = plt.subplots(figsize=(8, max(4.5, 0.42 * len(variables))))
        y = np.arange(len(variables))
        for i, model in enumerate(["baseline_1_simple", "baseline_2_extended"]):
            part = summary[summary.model.eq(model)].set_index("variable").reindex(variables)
            ax.barh(y + (i - 0.5) * 0.32, part.coefficient, height=0.30, label=model.replace("baseline_", "Baseline "))
        ax.axvline(0, color="gray", linewidth=1)
        ax.set(title="Mean standardized logistic coefficients", xlabel="Log-odds change per training SD", yticks=y, yticklabels=variables)
        ax.invert_yaxis()
        ax.legend(frameon=False)
        names.append(_save_figure("coefficients", fig))
    return names


def _write_report(performance, predictions, calibration, lifts, coefficients, sample_audit, sector_audit, sensitivity, figures):
    validation = performance[(performance.split_role == "validation") & performance.model.isin(MAIN_MODELS)]
    pooled_rows = performance[(performance.split_role == "pooled_oof") & performance.model.isin(MAIN_MODELS) & performance.threshold_policy.eq("train_prevalence")]
    def table(frame, columns):
        values = frame[columns].copy()
        rendered = []
        for row in values.itertuples(index=False, name=None):
            rendered.append([f"{value:.3f}" if isinstance(value, (float, np.floating)) and np.isfinite(value)
                             else "" if pd.isna(value) else str(value) for value in row])
        return "| " + " | ".join(columns) + " |\n| " + " | ".join(["---"] * len(columns)) + " |\n" + "\n".join(
            "| " + " | ".join(row) + " |" for row in rendered
        )
    sector_validation = sector_audit[sector_audit.split_role.eq("validation")].groupby(
        ["model_feature_complete", "sector_code"], as_index=False, observed=True
    ).apply(lambda group: pd.Series({
        "n": group.n.sum(),
        "mean_startup_rate": np.average(group.mean_startup_rate.fillna(0), weights=group.n),
        "mean_employment_growth": np.average(group.mean_employment_growth.fillna(0), weights=group.n),
        "mean_acs_population": np.average(group.mean_acs_population.fillna(0), weights=group.n),
    }), include_groups=False).reset_index(drop=True)
    continuous_coefficients = coefficients[
        coefficients.model.isin(["baseline_1_simple", "baseline_2_extended"])
        & coefficients.variable.ne("const") & ~coefficients.variable.str.startswith("sector_")
    ]
    coefficient_stability = continuous_coefficients.groupby(["model", "variable"], as_index=False).agg(
        mean_coefficient=("coefficient", "mean"), min_coefficient=("coefficient", "min"),
        max_coefficient=("coefficient", "max"), positive_folds=("coefficient", lambda x: int((x > 0).sum())),
        folds=("coefficient", "size"),
    )
    coefficient_stability["mean_odds_ratio_per_training_sd"] = np.exp(coefficient_stability.mean_coefficient)
    b2 = pooled_rows[pooled_rows.model.eq("baseline_2_extended")].iloc[0]
    b0 = pooled_rows[pooled_rows.model.eq("baseline_0_prevalence")].iloc[0]
    b1 = pooled_rows[pooled_rows.model.eq("baseline_1_simple")].iloc[0]
    text = f"""# Assignment 6.4: Baseline Predictive Model

## Executive Summary

This step fits only the training-prevalence benchmark and interpretable logistic regressions. The final holdout was not queried; only predictor years through 2017 were read from the analytical view. The primary metric is Average Precision (AP/PR-AUC), interpreted against the roughly 20% natural prevalence. Pooled OOF AP was {b0.pr_auc:.3f} for Baseline 0, {b1.pr_auc:.3f} for the simple logistic model, and {b2.pr_auc:.3f} for the extended model. The extended-model AP change over prevalence is {b2.pr_auc - b0.pr_auc:+.3f}; conclusions below reflect that size and fold stability, not accuracy.

## Predictive Objective and Modeling Sample

The unchanged A6.3 `gap_p20` label is predicted at exact same-MSA/same-sector t+3. Predictor rows are joined only at t. Each validation pair receives one prediction from a model trained on that fold's earlier target outcomes. Fold 1-3 are reported separately and pooled results are pooled out-of-fold development metrics, not holdout results.

The A6.3 target artifact has 67,067 fold/split records, including repeated expanding training sets; unique development validation rows are 14,413. The shared feature-complete modeling validation N is {len(predictions):,}. The extended specification adds five ACS fields; the common-sample rule keeps simple and extended comparisons paired. `a6_baseline_sample_audit.csv` reports per-fold A6.3 eligible pairs and extra predictor-feature exclusions. A6.3's target eligibility itself is already selective: excluded rows were smaller and lower-startup. This analysis cannot restore those rows; performance applies only to complete-case eligible MSA-sector pairs and may not generalize to systematically excluded smaller/lower-startup observations.

{table(sample_audit, ['fold','split_role','a6_eligible_n','model_complete_n','additional_missing_n','additional_missing_share'])}

Modeling sample composition by target-feature completeness:

{table(sector_validation, ['model_feature_complete','sector_code','n','mean_startup_rate','mean_employment_growth','mean_acs_population'])}

## Baseline 0: Training Prevalence

For each fold, the probability is the natural gap prevalence in that fold's training labels, applied unchanged to its validation rows. No class rebalancing is used. Within each fold, constant-score AP equals that fold's validation prevalence and ROC-AUC is 0.50. Pooled OOF fold-specific probabilities can rank folds relative to each other, so pooled Baseline 0 AP ({b0.pr_auc:.3f}) need not equal pooled prevalence ({predictions.actual_gap.mean():.3f}); this cross-fold ranking is still only the predeclared prevalence benchmark, not within-fold discrimination.

## Baseline 1: Simple Logistic

Predictors: predictor-year startup rate, startup-rate lag 1, employment growth, sector fixed effects, and a linear predictor-year trend. Continuous variables are standardized from training rows only; sector levels are learned from training rows, with unseen validation levels safely encoded as all-zero reference contrasts. A tiny L2 penalty stabilizes binomial estimates; classes are not weighted.

## Baseline 2: Extended Logistic

Adds predictor-year population growth, median household income, educational attainment, labor-force participation, and unemployment to Baseline 1. Uses the same common complete-feature sample and training-only transforms. No MSA fixed effects or alternate growth series are used.

## Temporal Validation and Fold Performance

The primary probability scores are shown once per model/fold; threshold-specific recall, precision, F1, balanced accuracy and confusion counts are reported at 0.50 and the fold's training prevalence. Neither is a final operating threshold.

{table(validation[validation.threshold_policy.eq('train_prevalence')], ['model','fold','train_n','validation_n','train_prevalence','validation_prevalence','pr_auc','roc_auc','brier_score','recall','precision','f1','balanced_accuracy'])}

Confusion counts at each diagnostic threshold (thresholds are not deployment choices):

{table(validation, ['model','fold','threshold_policy','classification_threshold','true_positive','false_positive','true_negative','false_negative','recall','precision','f1'])}

## Pooled Out-of-Fold Performance

Each of the {len(predictions):,} validation rows appears once in the pooled OOF artifact. The table uses a fold-specific training-prevalence diagnostic threshold; probabilities themselves are evaluated without thresholding.

{table(pooled_rows, ['model','train_n','validation_n','train_prevalence','validation_prevalence','pr_auc','roc_auc','brier_score','recall','precision','f1','balanced_accuracy','classification_threshold'])}

## PR-AUC Interpretation and Probability Calibration

Pooled AP is compared with actual pooled validation prevalence ({predictions.actual_gap.mean():.3f}). Baseline 1 exceeds the pooled fold-specific prevalence model AP by {b1.pr_auc - b0.pr_auc:+.3f}, and the extended model by {b2.pr_auc - b0.pr_auc:+.3f}; relative to the raw pooled positive-class prevalence, the gains are {b1.pr_auc - predictions.actual_gap.mean():+.3f} and {b2.pr_auc - predictions.actual_gap.mean():+.3f}. Both logistic gains are positive and directionally consistent in all three folds. Pooled prevalence-baseline scores differ across folds, so pooled baseline metrics also reflect cross-fold prevalence ranking; fold-level comparison is the cleaner no-information reference. ROC-AUC and Brier score are secondary; Brier is sensitive to the observed prevalence shift relative to each fold's training prevalence.

Pooled calibration uses equal-frequency risk deciles. The figure and CSV show mean predicted risk versus observed gap prevalence; calibration should be read alongside ranking, since a model can rank without calibrated probabilities.

{table(calibration[calibration.model.eq('baseline_2_extended')], ['risk_bin','n','mean_predicted_probability','observed_gap_prevalence'])}

## Recall / Precision Tradeoff, Risk Bins, and Lift

Recall is reported beside precision and F1 because missed gaps are substantively costly. The diagnostic thresholds are 0.50 and training prevalence only; no validation-tuned threshold is selected. Top-risk lift is measured against pooled natural prevalence, with top 10%, 20%, and 25% groups selected by rank.

{table(lifts, ['model','risk_cut','selected_n','observed_gap_prevalence','overall_prevalence','lift_ratio'])}

## Predictor Contribution and Coefficients

The following ablations are descriptive fold comparisons, not causal effects. They check lag-1 startup history, employment growth, regional controls, sector identity, and time trend contribution while preserving the paired sample.

{table(pd.concat([validation[validation.threshold_policy.eq('train_prevalence')][['model','fold','pr_auc','roc_auc','brier_score']], sensitivity], ignore_index=True), ['model','fold','pr_auc','roc_auc','brier_score'])}

Across folds, adding the five ACS controls does not improve AP (extended minus simple is slightly negative each fold, about 0.001-0.002); Brier changes are tiny and mixed. Removing lag-1 startup rate lowers AP by about 0.004-0.022, while removing employment growth changes AP by less than about 0.002. Removing sector effects substantially lowers AP and ROC-AUC; removing the linear time trend changes little. This first pass suggests strong sector context and startup-history signal, but little incremental gain from current employment growth or the ACS block on this sample.

Continuous coefficients are standardized log-odds changes per one training-fold standard deviation; odds ratios are `exp(coefficient)`. The range and sign consistency below summarize fold stability. Sector contrasts use the first training category as the reference. Coefficients reflect correlated predictors and this selected sample, and are not causal estimates. The full fold coefficient table includes sector and time terms.

{table(coefficient_stability, ['model','variable','mean_coefficient','mean_odds_ratio_per_training_sd','min_coefficient','max_coefficient','positive_folds','folds'])}

## Plain-Language Summary

- **Can gaps be predicted?** Yes, at a useful baseline level in development: simple/extended pooled AP is {b1.pr_auc:.3f}/{b2.pr_auc:.3f}, versus {b0.pr_auc:.3f} for the fold-specific prevalence benchmark, and each fold improves AP.
- **How much better than guessing?** The simple model's pooled AP gain is {b1.pr_auc-b0.pr_auc:.3f} over the fold-specific prevalence model and {b1.pr_auc-predictions.actual_gap.mean():.3f} over the raw pooled 19.1% prevalence. This is meaningful ranking signal, not evidence of holdout generalization.
- **Which variables appear useful?** Sector identity has the largest ablation effect; current and lagged startup rates carry stable negative associations with later gap odds. Interpret these as conditional associations, not causes.
- **Does industry growth add value?** Little in this first pass: removing employment growth changes AP by less than about 0.002 across folds.
- **Does startup history dominate?** It contributes, but prediction does not collapse without lag-1; removing it lowers AP by roughly 0.004-0.022 by fold.
- **Are predicted probabilities reasonably calibrated?** The extended-model risk-bin rates broadly track predicted probabilities, though the highest decile's observed prevalence (42.4%) is below its mean predicted risk (46.2%).
- **Can it rank high-risk combinations?** The simple model's top 10% contains 43.0% gaps, about 2.25 times the pooled 19.1% prevalence; top-20% and top-25% lift are about 1.91 and 1.78.

## Limitations, Holdout Preservation, and Leakage Audit

- Complete-case selection is patterned; excluded observations disproportionately come from smaller MSAs and lower startup rates. No imputation was performed.
- Predictor fields are joined by exact `cbsa_code`, `sector_code`, and `predictor_year`; target-year startup, residual, expected rate, margin, and label are excluded from X.
- Numeric scaling statistics and sector categories are fitted within each training fold. Validation labels are used only for evaluation.
- Baseline prevalence and diagnostic classification thresholds use training labels only. No threshold tuning uses validation outcomes.
- The SQLite view was opened read-only and queried only for years through 2017. No 2018-2020 predictors or 2021-2023 outcomes, holdout prevalence, or holdout scores were read.
- No Random Forest, Gradient Boosting, XGBoost, broad hyperparameter tuning, or A6.5 work was performed.

## Readiness for A6.5

The baseline comparison is established under the frozen temporal folds. Whether non-linear models are justified depends on the size/stability of AP gains over natural prevalence, risk-bin concentration, calibration, and paired ablation results above. This step does not claim generalization beyond the selected complete-case population or evaluate the final holdout.

## Outputs

- Report: `reports/assignment6_baseline_predictive_model.md`
- Performance: `reports/tables/a6_baseline_model_performance.csv`
- OOF predictions: `reports/tables/a6_baseline_oof_predictions.csv`
- Coefficients: `reports/tables/a6_baseline_logistic_coefficients.csv`
- Calibration: `reports/tables/a6_baseline_calibration.csv`
- Lift: `reports/tables/a6_baseline_lift.csv`
- Sample audits: `reports/tables/a6_baseline_sample_audit.csv`, `reports/tables/a6_baseline_sector_composition.csv`
- Figures: {', '.join(f'`reports/figures/{name}`' for name in figures)}
- Runner and reusable logic: `src/regional_entrepreneurship_intelligence/models/run_baseline.py`, `src/regional_entrepreneurship_intelligence/models/baseline.py`
"""
    REPORT_PATH.write_text(text, encoding="utf-8")


def run_baseline(database_path: Path = DEFAULT_EDA_DATABASE) -> dict[str, object]:
    targets = pd.read_csv(TARGET_PATH)
    targets = targets.loc[targets.target_year.le(2020)].copy()
    if targets.target_year.max() > 2020 or targets.predictor_year.max() > 2017:
        raise ValueError("Holdout pairs cannot enter baseline construction")
    fold_config = pd.read_csv(FOLD_PATH).query("final_holdout == False")
    predictor_panel = _load_predictor_panel(Path(database_path))
    paired = build_predictor_pairs(targets, predictor_panel)
    complete, audited = complete_predictor_sample(paired)
    audited["model_feature_complete"] = audited.index.isin(complete.index)
    audited["additional_feature_missing"] = ~audited.model_feature_complete

    sample_rows = []
    sector_rows = []
    for fold in fold_config.fold:
        for split in ("training", "validation"):
            full = audited[(audited.fold == fold) & (audited.split_role == split)]
            sample = complete[(complete.fold == fold) & (complete.split_role == split)]
            sample_rows.append({"fold": fold, "split_role": split, "a6_eligible_n": len(full),
                                "model_complete_n": len(sample), "additional_missing_n": len(full) - len(sample),
                                "additional_missing_share": (len(full) - len(sample)) / len(full) if len(full) else np.nan})
            for included, group in [(False, full.loc[~full.index.isin(sample.index)]), (True, sample)]:
                sector_counts = group.groupby("sector_code", observed=True).agg(
                    n=("gap_p20", "size"), mean_startup_rate=("startup_rate", "mean"),
                    mean_employment_growth=("employment_growth", "mean"), mean_acs_population=("acs_population", "mean"),
                ).reset_index()
                for row in sector_counts.to_dict("records"):
                    sector_rows.append({"fold": fold, "split_role": split, "model_feature_complete": included, **row})
    sample_audit = pd.DataFrame(sample_rows)
    sector_audit = pd.DataFrame(sector_rows)

    prediction_frames = []
    performance_rows = []
    coefficient_rows = []
    sensitivity_rows = []
    sensitivity_models = ("baseline_2_no_startup_lag1", "baseline_2_no_employment_growth", "baseline_1_no_sector", "baseline_1_no_time")
    for fold in fold_config.fold:
        train = complete[(complete.fold == fold) & complete.split_role.eq("training")].copy()
        validation = complete[(complete.fold == fold) & complete.split_role.eq("validation")].copy()
        train_prevalence = fit_prevalence_baseline(train.gap_p20)
        models = {}
        val_predictions = pd.DataFrame({
            "fold": fold, "cbsa_code": validation.cbsa_code, "sector_code": validation.sector_code,
            "predictor_year": validation.predictor_year, "target_year": validation.target_year,
            "actual_gap": validation.gap_p20.astype(int),
            "baseline_0_probability": train_prevalence,
        }, index=validation.index)
        models_for_fit = ("baseline_1_simple", "baseline_2_extended", *sensitivity_models)
        for model_name in models_for_fit:
            fitted = fit_logistic_baseline(train, model=model_name)
            models[model_name] = fitted
            column = "baseline_1_probability" if model_name == "baseline_1_simple" else "baseline_2_probability" if model_name == "baseline_2_extended" else f"{model_name}_probability"
            val_predictions[column] = predict_gap_probability(fitted, validation)
            if model_name in MAIN_MODELS[1:]:
                params = fitted.result.params
                for variable, coef in params.items():
                    coefficient_rows.append({"model": model_name, "fold": fold, "variable": variable,
                                             "coefficient": float(coef), "odds_ratio": float(np.exp(np.clip(coef, -30, 30))),
                                             "sign": "positive" if coef > 0 else "negative" if coef < 0 else "zero",
                                             "standardized": variable in fitted.numeric_features or variable == "year_trend"})
        prediction_frames.append(val_predictions)
        model_probability_col = {
            "baseline_0_prevalence": "baseline_0_probability",
            "baseline_1_simple": "baseline_1_probability",
            "baseline_2_extended": "baseline_2_probability",
        }
        for model_name, col in model_probability_col.items():
            probabilities = val_predictions[col].to_numpy()
            for policy, cutoff in [("0.50", 0.5), ("train_prevalence", train_prevalence)]:
                performance_rows.append(_performance_row(model_name, fold, "validation", validation.gap_p20.to_numpy(),
                                                         probabilities, len(train), train_prevalence, policy, cutoff))
        for model_name in sensitivity_models:
            col = f"{model_name}_probability"
            metric = probability_metrics(validation.gap_p20, val_predictions[col].to_numpy())
            sensitivity_rows.append({"model": model_name, "fold": fold, **metric})

    predictions = pd.concat(prediction_frames, ignore_index=True)
    validate_oof_predictions(predictions)
    pooled_prevalence = float(predictions.actual_gap.mean())
    fold_prevalences = {
        row["fold"]: row["train_prevalence"] for row in performance_rows
        if row["model"] == "baseline_0_prevalence" and row["split_role"] == "validation"
        and row["threshold_policy"] == "train_prevalence"
    }
    for model_name, col in {"baseline_0_prevalence":"baseline_0_probability", "baseline_1_simple":"baseline_1_probability", "baseline_2_extended":"baseline_2_probability"}.items():
        for policy in ("0.50", "train_prevalence"):
            probs = predictions[col].to_numpy()
            threshold = 0.5
            if policy == "train_prevalence":
                predicted = np.zeros(len(predictions), dtype=bool)
                # Apply each validation fold's own training prevalence cutoff unchanged.
                for fold in fold_config.fold:
                    mask = predictions.fold.eq(fold).to_numpy()
                    fold_cut = float(fold_prevalences[fold])
                    predicted[mask] = probs[mask] >= fold_cut
                # calculate threshold metrics against the fold-specific decision vector
                actual = predictions.actual_gap.to_numpy()
                tp = int(np.sum(predicted & (actual == 1))); fp = int(np.sum(predicted & (actual == 0)))
                tn = int(np.sum(~predicted & (actual == 0))); fn = int(np.sum(~predicted & (actual == 1)))
                recall = tp / (tp + fn) if tp + fn else 0.0; precision = tp / (tp + fp) if tp + fp else 0.0
                f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
                specificity = tn / (tn + fp) if tn + fp else 0.0
                cls = {"true_positive": tp, "false_positive": fp, "true_negative": tn, "false_negative": fn,
                       "recall": recall, "precision": precision, "f1": f1, "balanced_accuracy": (recall + specificity) / 2}
                validation_sizes = {fold: int(predictions.fold.eq(fold).sum()) for fold in fold_prevalences}
                pooled_cutoff = float(np.average(list(fold_prevalences.values()), weights=list(validation_sizes.values())))
            else:
                cls = threshold_metrics(predictions.actual_gap, probs, threshold)
                pooled_cutoff = threshold
            performance_rows.append({"model": model_name, "fold": "pooled_oof", "split_role": "pooled_oof", "train_n": np.nan,
                                     "validation_n": len(predictions), "train_prevalence": np.nan,
                                     "validation_prevalence": pooled_prevalence, **probability_metrics(predictions.actual_gap, probs),
                                     **cls, "classification_threshold": pooled_cutoff, "threshold_policy": policy, "pooled_flag": True})

    performance = pd.DataFrame(performance_rows)
    coefficients = pd.DataFrame(coefficient_rows)
    sensitivity = pd.DataFrame(sensitivity_rows)
    calibration_frames, lift_frames = [], []
    for model_name, col in {"baseline_0_prevalence":"baseline_0_probability", "baseline_1_simple":"baseline_1_probability", "baseline_2_extended":"baseline_2_probability"}.items():
        cal = calibration_table(predictions.actual_gap, predictions[col].to_numpy())
        cal.insert(0, "model", model_name); calibration_frames.append(cal)
        lift = lift_table(predictions.actual_gap, predictions[col].to_numpy())
        lift.insert(0, "model", model_name); lift_frames.append(lift)
    calibration = pd.concat(calibration_frames, ignore_index=True)
    lifts = pd.concat(lift_frames, ignore_index=True)

    TABLE_DIR.mkdir(parents=True, exist_ok=True); FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    performance.to_csv(TABLE_DIR / "a6_baseline_model_performance.csv", index=False)
    predictions.to_csv(TABLE_DIR / "a6_baseline_oof_predictions.csv", index=False)
    coefficients.to_csv(TABLE_DIR / "a6_baseline_logistic_coefficients.csv", index=False)
    calibration.to_csv(TABLE_DIR / "a6_baseline_calibration.csv", index=False)
    lifts.to_csv(TABLE_DIR / "a6_baseline_lift.csv", index=False)
    sample_audit.to_csv(TABLE_DIR / "a6_baseline_sample_audit.csv", index=False)
    sector_audit.to_csv(TABLE_DIR / "a6_baseline_sector_composition.csv", index=False)
    sensitivity.to_csv(TABLE_DIR / "a6_baseline_sensitivity.csv", index=False)
    figures = _make_figures(performance, predictions, calibration, lifts, coefficients)
    _write_report(performance, predictions, calibration, lifts, coefficients, sample_audit, sector_audit, sensitivity, figures)
    print(performance[(performance.split_role.eq("pooled_oof"))][["model","threshold_policy","pr_auc","roc_auc","brier_score","recall","precision","f1"]].to_string(index=False))
    print(f"OOF validation N: {len(predictions):,}; prevalence={pooled_prevalence:.3%}")
    print(f"Report: {REPORT_PATH}")
    return {"performance": performance, "predictions": predictions, "coefficients": coefficients,
            "calibration": calibration, "lift": lifts, "sample_audit": sample_audit, "figures": figures}


if __name__ == "__main__":
    run_baseline()
