"""Run fold-safe nonlinear model comparisons for Assignment 6.5."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.analysis.eda import DEFAULT_EDA_DATABASE
from regional_entrepreneurship_intelligence.models.advanced import (
    ABLATIONS,
    MODEL_NAMES,
    TREE_FEATURES,
    evaluate_predictions,
    feature_ablation,
    fit_advanced_model,
    make_inner_temporal_split,
    partial_dependence_grid,
    predict_gap_probability,
    tune_advanced_model,
    validate_advanced_oof,
    validation_permutation_importance,
)
from regional_entrepreneurship_intelligence.models.baseline import (
    build_predictor_pairs,
    calibration_table,
    complete_predictor_sample,
    fit_prevalence_baseline,
    lift_table,
    threshold_metrics,
)
from regional_entrepreneurship_intelligence.models.run_baseline import (
    FOLD_PATH,
    MAX_DEVELOPMENT_PREDICTOR_YEAR,
    ROOT,
    TARGET_PATH,
    _load_predictor_panel,
)

TABLE_DIR = ROOT / "reports" / "tables"
FIGURE_DIR = ROOT / "reports" / "figures"
REPORT_PATH = ROOT / "reports" / "assignment6_advanced_predictive_models.md"
KEYS = ["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"]


def _performance(actual, probabilities, *, model, fold, train_n, train_prevalence):
    return {
        "model": model,
        "fold": fold,
        "split_role": "validation",
        "train_n": train_n,
        "validation_n": len(actual),
        "train_prevalence": train_prevalence,
        "validation_prevalence": float(np.mean(actual)),
        **evaluate_predictions(actual, probabilities),
        **threshold_metrics(actual, probabilities, train_prevalence),
        "threshold_policy": "training_prevalence",
        "classification_threshold": train_prevalence,
    }


def _figures(performance, predictions, calibration, importance, pdp, selected):
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    made = []

    def save(name, fig):
        path = FIGURE_DIR / f"a6_advanced_{name}.png"
        fig.tight_layout()
        fig.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        made.append(path.name)

    for metric, name, title in [
        ("pr_auc", "ap_by_fold", "Average precision by temporal fold"),
        ("roc_auc", "roc_auc_by_fold", "ROC-AUC by temporal fold"),
        ("brier_score", "brier_by_fold", "Brier score by temporal fold"),
    ]:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for model, group in performance[performance.fold.ne("pooled_oof")].groupby("model"):
            ax.plot(group.fold, group[metric], marker="o", label=model)
        ax.set(title=title, xlabel="Temporal fold", ylabel=metric.replace("_", " "))
        ax.legend(frameon=False)
        save(name, fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    pooled = performance[performance.fold.eq("pooled_oof")]
    labels = {"baseline_1_simple": "Logistic", "random_forest": "Random Forest",
              "hist_gradient_boosting": "HistGradientBoosting"}
    ax.bar([labels[name] for name in pooled.model], pooled.pr_auc, color=["#4b8064", "#bc6c4a", "#5580a5"])
    ax.axhline(float(predictions.actual_gap.mean()), color="black", linestyle="--", label="OOF prevalence")
    ax.set(title="Pooled out-of-fold average precision", ylabel="Average precision")
    ax.legend(frameon=False, loc="upper left")
    save("pooled_ap", fig)

    fig, ax = plt.subplots(figsize=(6.5, 5))
    for model, col in [("baseline_1_simple", "baseline_1_probability"),
                       ("random_forest", "random_forest_probability"),
                       ("hist_gradient_boosting", "hist_gradient_boosting_probability")]:
        order = np.argsort(predictions[col].to_numpy())
        y = predictions.actual_gap.to_numpy()[order]
        p = predictions[col].to_numpy()[order]
        chunks = np.array_split(np.arange(len(y)), 10)
        ax.plot([float(p[x].mean()) for x in chunks], [float(y[x].mean()) for x in chunks], marker="o", label=model)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.set(title="Pooled OOF calibration", xlabel="Mean predicted probability", ylabel="Observed gap prevalence")
    ax.legend(frameon=False)
    save("calibration", fig)

    fig, ax = plt.subplots(figsize=(7.5, 5))
    top = importance.groupby("feature").importance_value.mean().nlargest(12).sort_values()
    ax.barh(top.index, top.values, color="#5580a5")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set(title="Mean outer-validation permutation importance", xlabel="AP decrease after permutation")
    save("permutation_importance", fig)

    selected_pdp = pdp[pdp.model.eq(selected)]
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    for ax, (feature, group) in zip(axes.flat, selected_pdp.groupby("feature", sort=False)):
        curve = group.groupby("feature_value", as_index=False).mean(numeric_only=True)
        ax.plot(curve.feature_value, curve.mean_predicted_probability, marker="o", color="#4b8064")
        ax.set(title=feature.replace("_", " "), xlabel="Training-support value", ylabel="Mean predicted risk")
    save("partial_dependence", fig)
    return made


def _write_report(performance, tuning, ablations, importance, calibration, lifts, pdp, sample_n, baseline_n, selected, figures):
    pooled = performance[performance.fold.eq("pooled_oof")].set_index("model")
    folds = performance[performance.fold.ne("pooled_oof")]
    adv = folds[folds.model.eq(selected)].set_index("fold")
    logistic = folds[folds.model.eq("baseline_1_simple")].set_index("fold")

    def md(frame, columns):
        view = frame[columns]
        rows = []
        for row in view.itertuples(index=False, name=None):
            rows.append([f"{value:.3f}" if isinstance(value, (float, np.floating)) and np.isfinite(value)
                         else str(value) for value in row])
        return "| " + " | ".join(columns) + " |\n| " + " | ".join(["---"] * len(columns)) + " |\n" + "\n".join(
            "| " + " | ".join(row) + " |" for row in rows
        )

    comparison = performance[["model", "fold", "validation_n", "validation_prevalence", "pr_auc", "roc_auc", "brier_score", "recall", "precision", "f1"]]
    ablation_view = ablations.groupby(["model", "ablation"], as_index=False).agg(
        full_ap=("full_model_ap", "mean"), mean_ap=("pr_auc", "mean"),
        delta_ap=("delta_ap", "mean"), mean_brier=("brier_score", "mean"), folds=("fold", "nunique"))
    importance_view = importance.groupby(["model", "feature"], as_index=False).importance_value.mean().sort_values(
        ["model", "importance_value"], ascending=[True, False])
    calibration_view = calibration[calibration.model.eq(selected)]
    lift_view = lifts[lifts.model.eq(selected)]
    ap_gain = pooled.loc[selected, "pr_auc"] - pooled.loc["baseline_1_simple", "pr_auc"]
    fold_wins = int((adv.pr_auc > logistic.pr_auc).sum())
    text = f"""# Assignment 6.5: Advanced Predictive Models

## Scope and safeguards

Random Forest and HistGradientBoosting are compared with the locked A6.4 simple logistic model on the exact same {sample_n:,} complete-case development population and {baseline_n:,} outer-validation OOF keys. The final holdout was not loaded: predictors are queried only through 2017, OOF targets are limited to 2020, and validation results are diagnostic. No A6.6 geographic holdout or sensitivity analysis was performed.

All models predict the unchanged binary `gap_p20` outcome at exact t+3. The frozen A6.3 temporal folds and Baseline 2 complete-case filter are retained. Predictors are the A6.4 extended set: current and lagged startup rate, employment growth, five ACS controls, sector, and predictor year. Preprocessing is fitted within each training split. Class weights, resampling, and threshold optimization are not used.

Each outer fold has a small four-candidate grid search using only the latest predictor-year slice of that fold's training rows as a forward inner validation; candidate selection uses average precision (AP). The winning configuration is refit on the entire outer training fold. Outer validation AP is used only for reporting and permutation diagnostics, never for tuning.

## OOF performance

The baseline probability column is the locked A6.4 Baseline 1 prediction joined by full fold, geography, sector, predictor-year, and target-year keys. AP is primary; ROC-AUC and Brier are secondary. Recall, precision, and F1 use each outer fold's natural training prevalence as a descriptive threshold, not a selected operating rule.

{md(comparison, ['model','fold','validation_n','validation_prevalence','pr_auc','roc_auc','brier_score','recall','precision','f1'])}

Selected advanced model: **{selected}**. Its pooled OOF AP difference versus the locked simple logistic model is **{ap_gain:+.3f}**, and it exceeds logistic AP in {fold_wins} of 3 folds. Selection is conservative: the nonlinear model is treated as a diagnostic challenger, not a replacement absent a clear, consistent advantage.

## Inner tuning

{md(tuning, ['model','fold','candidate_id','inner_ap','inner_fit_n','inner_validation_n','inner_predictor_cutoff','inner_fit_target_max','inner_validation_target_min'])}

Winning parameters are recorded in the tuning CSV. The search is intentionally limited to these candidates and is not evidence of exhaustive optimization.

## Calibration, lift, ablation, and interpretation

Calibration deciles and top-risk lift are based on pooled OOF predictions and should be interpreted with fold-wise results because prevalence changes over time. Permutation importance is calculated on outer validation solely as a descriptive diagnostic; it does not select features or hyperparameters. Ablations retain the same rows and use the full model's selected fold parameters. Partial dependence is descriptive, fold-specific, and restricted to the training-support 5th–95th percentile range; it is not causal.

{md(ablation_view, ['model','ablation','folds','full_ap','mean_ap','delta_ap','mean_brier'])}

{md(importance_view.head(24), ['model','feature','importance_value'])}

{md(calibration_view, ['risk_bin','n','mean_predicted_probability','observed_gap_prevalence'])}

{md(lift_view, ['risk_cut','selected_n','observed_gap_prevalence','overall_prevalence','lift_ratio'])}

## Decision and limitations

The locked logistic model remains the reference. The selected nonlinear model's advantage is {ap_gain:+.3f} pooled AP with {fold_wins}/3 fold wins; this is not treated as a final model-selection or deployment decision. Complete-case selection limits the estimand to the retained sample. Temporal OOF results do not establish final holdout generalization. Features are predictive associations, not causal effects.

## Outputs

- Performance and OOF predictions: `reports/tables/a6_advanced_model_performance.csv`, `reports/tables/a6_advanced_oof_predictions.csv`
- Tuning, ablations, importance, calibration, lift, and partial dependence: `reports/tables/a6_advanced_tuning.csv`, `reports/tables/a6_advanced_ablation.csv`, `reports/tables/a6_advanced_permutation_importance.csv`, `reports/tables/a6_advanced_calibration.csv`, `reports/tables/a6_advanced_lift.csv`, `reports/tables/a6_advanced_partial_dependence.csv`
- Figures: {', '.join(f'`reports/figures/{name}`' for name in figures)}
"""
    REPORT_PATH.write_text(text, encoding="utf-8")


def run_advanced(database_path: Path = DEFAULT_EDA_DATABASE):
    targets = pd.read_csv(TARGET_PATH)
    targets = targets.loc[targets.target_year.le(2020)].copy()
    if targets.empty or targets.predictor_year.max() > MAX_DEVELOPMENT_PREDICTOR_YEAR:
        raise ValueError("A6.5 target sample crossed the untouched holdout boundary")
    folds_config = pd.read_csv(FOLD_PATH).query("final_holdout == False")
    panel = _load_predictor_panel(Path(database_path))
    pairs = build_predictor_pairs(targets, panel)
    complete, _ = complete_predictor_sample(pairs)
    complete = complete.copy()
    complete["fold"] = complete.fold.astype(str)
    complete["split_role"] = complete.split_role.astype(str)

    baseline_path = TABLE_DIR / "a6_baseline_oof_predictions.csv"
    baseline = pd.read_csv(baseline_path, dtype={"cbsa_code": str, "sector_code": str, "fold": str})
    baseline["predictor_year"] = baseline.predictor_year.astype(int)
    baseline["target_year"] = baseline.target_year.astype(int)
    expected = complete[complete.split_role.eq("validation")][KEYS + ["gap_p20"]].copy()
    expected = expected.rename(columns={"gap_p20": "actual_gap"})
    comparison = expected.merge(baseline[KEYS + ["actual_gap", "baseline_1_probability"]], on=KEYS,
                                how="outer", validate="one_to_one", indicator=True)
    if not comparison._merge.eq("both").all() or not comparison.actual_gap_x.eq(comparison.actual_gap_y).all():
        raise ValueError("A6.5 does not match the exact A6.4 OOF keys and labels")

    predictions, performances, tuning_frames, ablation_rows, importance_frames, pdp_frames = [], [], [], [], [], []
    for fold in folds_config.fold.astype(str):
        train = complete[(complete.fold == fold) & complete.split_role.eq("training")].copy()
        validation = complete[(complete.fold == fold) & complete.split_role.eq("validation")].copy()
        train_prev = fit_prevalence_baseline(train.gap_p20)
        base_fold = baseline[baseline.fold.eq(fold)][KEYS + ["baseline_1_probability"]]
        val = validation.merge(base_fold, on=KEYS, how="left", validate="one_to_one")
        if val.baseline_1_probability.isna().any():
            raise ValueError(f"Missing locked logistic predictions in {fold}")
        pred = val[KEYS].copy()
        pred["actual_gap"] = val.gap_p20.astype(int).to_numpy()
        pred["baseline_1_probability"] = val.baseline_1_probability.to_numpy()
        performances.append(_performance(pred.actual_gap, pred.baseline_1_probability.to_numpy(), model="baseline_1_simple",
                                          fold=fold, train_n=len(train), train_prevalence=train_prev))
        fold_models = {}
        for model_name in MODEL_NAMES:
            params, tuning = tune_advanced_model(train, model_name=model_name)
            tuning.insert(1, "fold", fold)
            tuning["selected"] = tuning.candidate_id.eq(int(tuning.iloc[0].candidate_id))
            tuning_frames.append(tuning)
            fitted = fit_advanced_model(train, model_name=model_name, params=params)
            probabilities = predict_gap_probability(fitted, val)
            pred[f"{model_name}_probability"] = probabilities
            performances.append(_performance(pred.actual_gap, probabilities, model=model_name, fold=fold,
                                              train_n=len(train), train_prevalence=train_prev))
            importance_frames.append(validation_permutation_importance(fitted, val, model_name=model_name, fold=fold))
            fold_models[model_name] = (fitted, params)
            for ablation, omitted in ABLATIONS.items():
                features = feature_ablation(model_name, TREE_FEATURES, omitted)
                ablated = fit_advanced_model(train, model_name=model_name, params=params, features=features)
                p = predict_gap_probability(ablated, val, features=features)
                full_metrics = evaluate_predictions(val.gap_p20, probabilities)
                ablated_metrics = evaluate_predictions(val.gap_p20, p)
                ablation_rows.append({"model": model_name, "fold": fold, "ablation": ablation,
                                      "full_model_ap": full_metrics["pr_auc"], "delta_ap": ablated_metrics["pr_auc"] - full_metrics["pr_auc"],
                                      "pr_auc": ablated_metrics["pr_auc"],
                                      "roc_auc": ablated_metrics["roc_auc"],
                                      "brier_score": ablated_metrics["brier_score"]})
        # PDPs are reported for each advanced model, using only its outer training rows.
        for model_name, (fitted, _) in fold_models.items():
            curves = partial_dependence_grid(fitted, train, model_name=model_name)
            curves.insert(1, "fold", fold)
            pdp_frames.append(curves)
        predictions.append(pred)

    oof = pd.concat(predictions, ignore_index=True)
    validate_advanced_oof(oof)
    if len(oof) != len(baseline) or set(map(tuple, oof[KEYS].to_numpy())) != set(map(tuple, baseline[KEYS].to_numpy())):
        raise ValueError("Advanced OOF sample differs from the A6.4 paired sample")
    performance = pd.DataFrame(performances)
    fold_cutoffs = performance[performance.fold.ne("pooled_oof") & performance.model.eq("baseline_1_simple")].set_index("fold").train_prevalence
    for model, col in [("baseline_1_simple", "baseline_1_probability"), *[(name, f"{name}_probability") for name in MODEL_NAMES]]:
        probs = oof[col].to_numpy()
        predicted = np.zeros(len(oof), dtype=bool)
        for fold, cutoff in fold_cutoffs.items():
            mask = oof.fold.eq(fold).to_numpy()
            predicted[mask] = probs[mask] >= float(cutoff)
        actual = oof.actual_gap.to_numpy()
        tp, fp = int(np.sum(predicted & (actual == 1))), int(np.sum(predicted & (actual == 0)))
        tn, fn = int(np.sum(~predicted & (actual == 0))), int(np.sum(~predicted & (actual == 1)))
        recall = tp / (tp + fn) if tp + fn else 0.0
        precision = tp / (tp + fp) if tp + fp else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        specificity = tn / (tn + fp) if tn + fp else 0.0
        performance.loc[len(performance)] = {
            "model": model, "fold": "pooled_oof", "split_role": "pooled_oof", "train_n": np.nan,
            "validation_n": len(oof), "train_prevalence": np.nan,
            "validation_prevalence": float(oof.actual_gap.mean()), **evaluate_predictions(oof.actual_gap, probs),
            "true_positive": tp, "false_positive": fp, "true_negative": tn, "false_negative": fn,
            "recall": recall, "precision": precision, "f1": f1, "balanced_accuracy": (recall + specificity) / 2,
            "threshold_policy": "fold_training_prevalence", "classification_threshold": np.nan,
        }

    pooled_ap = performance[performance.fold.eq("pooled_oof")].set_index("model").pr_auc
    fold_results = performance[performance.fold.ne("pooled_oof")]
    candidates = list(MODEL_NAMES)
    # Prefer a challenger only when pooled AP improves and the gain is present in most folds.
    best = max(candidates, key=lambda m: pooled_ap[m])
    best_folds = fold_results[fold_results.model.eq(best)].set_index("fold").pr_auc
    base_folds = fold_results[fold_results.model.eq("baseline_1_simple")].set_index("fold").pr_auc
    selected = best if pooled_ap[best] > pooled_ap["baseline_1_simple"] and int((best_folds > base_folds).sum()) >= 2 else "baseline_1_simple"

    importance = pd.concat(importance_frames, ignore_index=True)
    ablations = pd.DataFrame(ablation_rows)
    tuning_all = pd.concat(tuning_frames, ignore_index=True)
    pdp_all = pd.concat(pdp_frames, ignore_index=True)
    calibration_frames, lift_frames = [], []
    for model, col in [("baseline_1_simple", "baseline_1_probability"), *[(m, f"{m}_probability") for m in MODEL_NAMES]]:
        cal = calibration_table(oof.actual_gap, oof[col].to_numpy())
        cal.insert(0, "model", model)
        calibration_frames.append(cal)
        lift = lift_table(oof.actual_gap, oof[col].to_numpy())
        lift.insert(0, "model", model)
        lift_frames.append(lift)
    calibration, lifts = pd.concat(calibration_frames, ignore_index=True), pd.concat(lift_frames, ignore_index=True)

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    performance.to_csv(TABLE_DIR / "a6_advanced_model_performance.csv", index=False)
    oof.to_csv(TABLE_DIR / "a6_advanced_oof_predictions.csv", index=False)
    tuning_all.to_csv(TABLE_DIR / "a6_advanced_tuning.csv", index=False)
    ablations.to_csv(TABLE_DIR / "a6_advanced_ablation.csv", index=False)
    importance.to_csv(TABLE_DIR / "a6_advanced_permutation_importance.csv", index=False)
    calibration.to_csv(TABLE_DIR / "a6_advanced_calibration.csv", index=False)
    lifts.to_csv(TABLE_DIR / "a6_advanced_lift.csv", index=False)
    pdp_all.to_csv(TABLE_DIR / "a6_advanced_partial_dependence.csv", index=False)
    figures = _figures(performance, oof, calibration, importance, pdp_all, selected)
    _write_report(performance, tuning_all, ablations, importance, calibration, lifts, pdp_all,
                  len(complete), len(oof), selected, figures)
    print(performance[["model", "fold", "pr_auc", "roc_auc", "brier_score"]].to_string(index=False))
    print(f"OOF N={len(oof):,}; selected diagnostic={selected}; report={REPORT_PATH}")
    return {"performance": performance, "predictions": oof, "tuning": tuning_all,
            "ablation": ablations, "importance": importance, "calibration": calibration,
            "lift": lifts, "partial_dependence": pdp_all, "selected_model": selected}


if __name__ == "__main__":
    run_advanced()
