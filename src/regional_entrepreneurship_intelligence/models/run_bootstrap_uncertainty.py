"""Generate A6.8B MSA-cluster bootstrap uncertainty from frozen holdout scores."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "rei-matplotlib-cache"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from regional_entrepreneurship_intelligence.models.bootstrap import (
    BootstrapResult,
    paired_cluster_bootstrap_ap,
)


ROOT = Path(__file__).resolve().parents[3]
PREDICTIONS = ROOT / "reports" / "tables" / "a6_final_holdout_predictions.csv"
ADVANCED_PERFORMANCE = ROOT / "reports" / "tables" / "a6_advanced_model_performance.csv"
OUTPUT_TABLE = ROOT / "reports" / "tables" / "a6_holdout_ap_cluster_bootstrap.csv"
OUTPUT_FIGURE = ROOT / "reports" / "figures" / "a6_holdout_ap_difference_bootstrap.png"
OUTPUT_REPORT = ROOT / "reports" / "assignment6_bootstrap_uncertainty.md"
SEED = 754
REPLICATIONS = 5_000
PREDICTION_COLUMNS = {
    "Logistic AP": "predicted_probability_logistic",
    "HGB AP": "predicted_probability_hgb",
}
COMPARISON = ("HGB AP", "Logistic AP")
DIFFERENCE_NAME = "HGB AP_minus_Logistic AP"
MODEL_SWITCH_RULE = (
    "Replace Logistic only if the paired 95% MSA-cluster bootstrap CI for HGB minus "
    "Logistic AP is entirely above zero, the observed AP gain is at least 0.02, and "
    "the advantage is directionally stable across target years and existing robustness checks."
)


def _load_frozen_predictions(path: Path = PREDICTIONS) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"cbsa_code": str, "sector_code": str})
    required = {
        "cbsa_code",
        "sector_code",
        "target_year",
        "actual_gap",
        *PREDICTION_COLUMNS.values(),
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Frozen holdout prediction fields are missing: {missing}")
    if frame.duplicated(["cbsa_code", "sector_code", "target_year"]).any():
        raise ValueError("Frozen holdout predictions contain duplicate evaluation keys")
    if not frame.target_year.isin([2021, 2022, 2023]).all():
        raise ValueError("Frozen holdout predictions must contain only target years 2021-2023")
    return frame


def _observed_ap_by_year(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, group in frame.groupby("target_year", sort=True):
        for model, column in PREDICTION_COLUMNS.items():
            rows.append(
                {
                    "target_year": int(year),
                    "model": model,
                    "n": int(len(group)),
                    "prevalence": float(group.actual_gap.mean()),
                    "average_precision": float(
                        average_precision_score(group.actual_gap, group[column])
                    ),
                }
            )
    return pd.DataFrame(rows)


def _development_stability(path: Path = ADVANCED_PERFORMANCE) -> dict[str, object]:
    frame = pd.read_csv(path)
    folds = frame[
        frame.model.isin(["baseline_1_simple", "hist_gradient_boosting"])
        & frame.fold.isin(["fold_1", "fold_2", "fold_3"])
    ].pivot(index="fold", columns="model", values="pr_auc")
    if len(folds) != 3 or folds.isna().any().any():
        raise ValueError("Frozen development performance lacks the three paired temporal folds")
    differences = folds.hist_gradient_boosting - folds.baseline_1_simple
    pooled = frame[
        frame.model.isin(["baseline_1_simple", "hist_gradient_boosting"])
        & frame.fold.eq("pooled_oof")
    ].set_index("model").pr_auc
    if len(pooled) != 2:
        raise ValueError("Frozen development performance lacks paired pooled OOF AP")
    return {
        "fold_differences": {name: float(value) for name, value in differences.items()},
        "hgb_fold_wins": int((differences > 0).sum()),
        "fold_count": int(len(differences)),
        "all_folds_positive": bool((differences > 0).all()),
        "pooled_difference": float(
            pooled.loc["hist_gradient_boosting"] - pooled.loc["baseline_1_simple"]
        ),
    }


def _write_figure(result: BootstrapResult) -> None:
    difference = result.replications[DIFFERENCE_NAME]
    summary = result.summary.set_index("estimand").loc[DIFFERENCE_NAME]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(difference, bins=45, color="#4C78A8", edgecolor="white", linewidth=0.4)
    ax.axvline(0, color="#333333", linewidth=1.2, label="No AP difference")
    ax.axvline(summary.observed, color="#B4463A", linewidth=1.8, label="Observed difference")
    ax.axvspan(summary.ci_low, summary.ci_high, color="#4C78A8", alpha=0.16, label="95% percentile CI")
    ax.set(
        title="Paired MSA-cluster bootstrap: HGB minus Logistic AP",
        xlabel="Average Precision difference",
        ylabel="Bootstrap replications",
    )
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    OUTPUT_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_FIGURE, dpi=180)
    plt.close(fig)


def _write_report(
    frame: pd.DataFrame,
    result: BootstrapResult,
    by_year: pd.DataFrame,
    development_stability: dict[str, object],
) -> None:
    summary = result.summary.set_index("estimand")
    logistic = summary.loc["Logistic AP"]
    hgb = summary.loc["HGB AP"]
    difference = summary.loc[DIFFERENCE_NAME]
    diagnostics = result.diagnostics
    prevalence = float(frame.actual_gap.mean())
    counts = frame.groupby("cbsa_code").size()
    one_row_label = "MSA has" if int((counts == 1).sum()) == 1 else "MSAs have"
    year_lines = []
    for year in sorted(by_year.target_year.unique()):
        rows = by_year[by_year.target_year.eq(year)].set_index("model")
        year_lines.append(
            f"- {year}: Logistic {rows.loc['Logistic AP', 'average_precision']:.3f}; "
            f"HGB {rows.loc['HGB AP', 'average_precision']:.3f}; "
            f"N={int(rows.loc['Logistic AP', 'n']):,}."
        )
    ci_clears_zero = bool(difference.ci_low > 0)
    gain_clears_threshold = bool(difference.observed >= 0.02)
    year_differences = by_year.pivot(index="target_year", columns="model", values="average_precision")
    stable_year_direction = bool((year_differences["HGB AP"] > year_differences["Logistic AP"]).all())
    stable_development_folds = bool(development_stability["all_folds_positive"])
    switch_rule_met = (
        ci_clears_zero
        and gain_clears_threshold
        and stable_year_direction
        and stable_development_folds
    )
    interpretation = (
        "The interval is entirely above zero, so the observed HGB advantage is distinguishable "
        "from zero under this bootstrap."
        if ci_clears_zero
        else "The interval crosses zero, so the observed HGB advantage is not clearly distinguishable "
        "from MSA-cluster sampling variation."
    )
    sections = [
        "# Assignment 6.8B: Bootstrap Uncertainty for Holdout Average Precision",
        "",
        "## Purpose",
        "",
        "This post-assignment instructor-feedback remediation quantifies sampling uncertainty around the frozen final-holdout Average Precision values. It does not refit either model, alter probabilities, relabel outcomes, or change the evaluation sample.",
        "",
        "## Bootstrap Design",
        "",
        f"A paired cluster bootstrap sampled the {frame.cbsa_code.nunique()} observed MSAs with replacement and retained every holdout row belonging to each selected MSA. Repeatedly selected MSAs contributed repeated complete row clusters. Both models were evaluated on each identical resample. Seed `{SEED}` requested {REPLICATIONS:,} replications; {int(diagnostics['valid_replications']):,} were valid and {int(diagnostics['invalid_replications']):,} were excluded for containing only one target class.",
        "",
        "The primary interval is the 2.5th-97.5th percentile interval. No BCa adjustment or row-level independence assumption is used. A target-year-stratified bootstrap was not added because resampling the same MSA separately within years would break its longitudinal cluster membership; the primary whole-MSA bootstrap preserves that dependence.",
        "",
        "## Cluster Choice",
        "",
        f"The holdout contains {frame.cbsa_code.nunique()} MSAs. Rows per MSA range from {int(counts.min())} to {int(counts.max())}, with quartiles {counts.quantile(.25):.0f}, {counts.median():.0f}, and {counts.quantile(.75):.0f}; {int((counts == 1).sum())} {one_row_label} one row. MSA clustering reflects shared economic and institutional conditions across sector-year rows within a metro.",
        "",
        "## Holdout Sample",
        "",
        f"The unchanged artifact has {len(frame):,} rows, {frame.cbsa_code.nunique()} MSAs, target years {int(frame.target_year.min())}-{int(frame.target_year.max())}, and prevalence {prevalence:.3f}. Logistic AP/prevalence is {logistic.observed / prevalence:.2f}; HGB AP/prevalence is {hgb.observed / prevalence:.2f}.",
        "",
        "## Logistic AP Interval",
        "",
        f"Observed AP is {logistic.observed:.6f}. Bootstrap mean is {logistic.bootstrap_mean:.6f}, median {logistic.bootstrap_median:.6f}, SE {logistic.bootstrap_se:.6f}, and 95% percentile CI [{logistic.ci_low:.6f}, {logistic.ci_high:.6f}].",
        "",
        "## HGB AP Interval",
        "",
        f"Observed AP is {hgb.observed:.6f}. Bootstrap mean is {hgb.bootstrap_mean:.6f}, median {hgb.bootstrap_median:.6f}, SE {hgb.bootstrap_se:.6f}, and 95% percentile CI [{hgb.ci_low:.6f}, {hgb.ci_high:.6f}].",
        "",
        "## Paired Difference",
        "",
        f"Observed HGB minus Logistic AP is {difference.observed:.6f}. Bootstrap mean is {difference.bootstrap_mean:.6f}, median {difference.bootstrap_median:.6f}, SE {difference.bootstrap_se:.6f}, and 95% percentile CI [{difference.ci_low:.6f}, {difference.ci_high:.6f}]. HGB exceeds Logistic in {float(diagnostics['proportion_HGB AP_greater_Logistic AP']):.1%} of valid replications; Logistic exceeds HGB in {float(diagnostics['proportion_Logistic AP_greater_HGB AP']):.1%}. The difference exceeds 0.01, 0.02, and 0.05 in {float(diagnostics['proportion_difference_gt_0_01']):.1%}, {float(diagnostics['proportion_difference_gt_0_02']):.1%}, and {float(diagnostics['proportion_difference_gt_0_05']):.1%} of valid replications.",
        "",
        "## Target-Year Context",
        "",
        *year_lines,
        "",
        "These are observed subgroup AP values, not separately bootstrapped estimates.",
        "",
        "The frozen development comparison is less uniform: HGB exceeded Logistic in "
        f"{development_stability['hgb_fold_wins']} of {development_stability['fold_count']} temporal folds, "
        f"and its pooled OOF AP gain was {float(development_stability['pooled_difference']):.3f}. "
        "No models were refit for this comparison.",
        "",
        "## Model-Switch Rule",
        "",
        MODEL_SWITCH_RULE,
        "",
        f"Rule components: CI entirely above zero = {ci_clears_zero}; observed gain at least 0.02 = {gain_clears_threshold}; HGB directionally higher in every holdout target year = {stable_year_direction}; HGB higher in every development temporal fold = {stable_development_folds}. Overall rule met = {switch_rule_met}.",
        "",
        "## Interpretation",
        "",
        interpretation + " Bootstrap proportions describe the empirical resampling distribution; they are not Bayesian posterior probabilities. The practical-size requirement and preselection discipline remain separate from statistical uncertainty.",
        "",
        "## Limitations",
        "",
        "The bootstrap treats observed MSAs as the resampling population, does not model future regime change, and does not repair complete-case selection or subgroup sparsity. Percentile intervals do not incorporate model-refitting uncertainty because predictions are intentionally frozen. There are only three target years, so temporal stability evidence remains limited.",
        "",
        "## Effect on Primary-Model Decision",
        "",
        f"The prespecified switch rule is {'met' if switch_rule_met else 'not met'}. Logistic remains the primary model pending student review because this remediation quantifies the frozen comparison and does not authorize a post-holdout model switch.",
        "",
        "## Outputs",
        "",
        "- `reports/tables/a6_holdout_ap_cluster_bootstrap.csv`",
        "- `reports/figures/a6_holdout_ap_difference_bootstrap.png`",
    ]
    OUTPUT_REPORT.write_text("\n".join(sections) + "\n", encoding="utf-8")


def run_bootstrap_uncertainty(
    *,
    predictions_path: Path = PREDICTIONS,
    replications: int = REPLICATIONS,
    seed: int = SEED,
) -> dict[str, object]:
    frame = _load_frozen_predictions(predictions_path)
    result = paired_cluster_bootstrap_ap(
        frame,
        cluster_column="cbsa_code",
        label_column="actual_gap",
        prediction_columns=PREDICTION_COLUMNS,
        comparison=COMPARISON,
        replications=replications,
        seed=seed,
        return_replications=True,
    )
    OUTPUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    result.summary.to_csv(OUTPUT_TABLE, index=False, float_format="%.10g")
    by_year = _observed_ap_by_year(frame)
    development_stability = _development_stability()
    _write_figure(result)
    _write_report(frame, result, by_year, development_stability)
    counts = frame.groupby("cbsa_code").size()
    return {
        "rows": len(frame),
        "msas": int(frame.cbsa_code.nunique()),
        "target_years": sorted(int(year) for year in frame.target_year.unique()),
        "prevalence": float(frame.actual_gap.mean()),
        "rows_per_msa": {
            "min": int(counts.min()),
            "median": float(counts.median()),
            "max": int(counts.max()),
            "one_row_msas": int((counts == 1).sum()),
        },
        "summary": result.summary.to_dict(orient="records"),
        "diagnostics": result.diagnostics,
        "by_year": by_year.to_dict(orient="records"),
        "development_stability": development_stability,
        "outputs": [str(OUTPUT_TABLE), str(OUTPUT_FIGURE), str(OUTPUT_REPORT)],
    }


if __name__ == "__main__":
    print(json.dumps(run_bootstrap_uncertainty(), indent=2))
