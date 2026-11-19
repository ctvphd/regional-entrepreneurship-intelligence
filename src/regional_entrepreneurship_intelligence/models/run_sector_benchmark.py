"""Generate the leakage-safe A6.8C sector-only benchmark artifacts."""

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

from regional_entrepreneurship_intelligence.models.bootstrap import (
    paired_cluster_bootstrap_ap,
)
from regional_entrepreneurship_intelligence.models.sector_benchmark import (
    benchmark_performance,
    fit_sector_prevalence,
    score_sector_prevalence,
    within_sector_logistic_performance,
)


ROOT = Path(__file__).resolve().parents[3]
DEVELOPMENT = ROOT / "reports" / "tables" / "a6_baseline_oof_predictions.csv"
HOLDOUT = ROOT / "reports" / "tables" / "a6_final_holdout_predictions.csv"
FINAL_PERFORMANCE = ROOT / "reports" / "tables" / "a6_final_model_performance.csv"
COMPARISON_TABLE = ROOT / "reports" / "tables" / "a6_sector_only_model_comparison.csv"
PREVALENCE_TABLE = ROOT / "reports" / "tables" / "a6_sector_prevalence_development_holdout.csv"
WITHIN_SECTOR_TABLE = ROOT / "reports" / "tables" / "a6_sector_within_logistic_ranking.csv"
FIGURE = ROOT / "reports" / "figures" / "a6_sector_only_ap_comparison.png"
REPORT = ROOT / "reports" / "assignment6_sector_only_benchmark.md"
SEED = 755
REPLICATIONS = 5_000


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    development = pd.read_csv(DEVELOPMENT, dtype={"cbsa_code": str, "sector_code": str})
    holdout = pd.read_csv(HOLDOUT, dtype={"cbsa_code": str, "sector_code": str})
    canonical = pd.read_csv(FINAL_PERFORMANCE)
    development_keys = ["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"]
    holdout_keys = ["cbsa_code", "sector_code", "predictor_year", "target_year"]
    required_development = {*development_keys, "actual_gap"}
    required_holdout = {
        *holdout_keys,
        "actual_gap",
        "sector_title",
        "predicted_probability_logistic",
        "predicted_probability_hgb",
    }
    if missing := sorted(required_development - set(development.columns)):
        raise ValueError(f"Development fields are missing: {missing}")
    if missing := sorted(required_holdout - set(holdout.columns)):
        raise ValueError(f"Holdout fields are missing: {missing}")
    if development.duplicated(development_keys).any():
        raise ValueError("Development OOF predictions contain duplicate evaluation keys")
    if holdout.duplicated(holdout_keys).any():
        raise ValueError("Final holdout predictions contain duplicate evaluation keys")
    if int(development.target_year.max()) > 2020 or not holdout.target_year.isin([2021, 2022, 2023]).all():
        raise ValueError("Development and holdout periods are not separated as documented")
    return development, holdout, canonical


def _difference_summary(
    replications: pd.DataFrame,
    *,
    higher: str,
    lower: str,
    observed: float,
) -> dict[str, float | str]:
    values = (replications[higher] - replications[lower]).to_numpy(dtype=float)
    return {
        "estimand": f"{higher}_minus_{lower}",
        "observed": observed,
        "bootstrap_mean": float(values.mean()),
        "bootstrap_median": float(np.median(values)),
        "bootstrap_se": float(values.std(ddof=1)),
        "ci_low": float(np.quantile(values, 0.025)),
        "ci_high": float(np.quantile(values, 0.975)),
        "proportion_above_zero": float((values > 0).mean()),
    }


def _write_figure(comparison: pd.DataFrame) -> None:
    colors = ["#8A8F98", "#D9892B", "#3F7CAC", "#4C8C6A"]
    x = np.arange(len(comparison))
    values = comparison.AP.to_numpy(dtype=float)
    lower = values - comparison.AP_ci_low.fillna(comparison.AP).to_numpy(dtype=float)
    upper = comparison.AP_ci_high.fillna(comparison.AP).to_numpy(dtype=float) - values
    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    ax.bar(x, values, color=colors, width=0.68)
    ax.errorbar(x, values, yerr=np.vstack([lower, upper]), fmt="none", ecolor="#20242A", capsize=4)
    ax.set_xticks(x, comparison.model)
    ax.set_ylabel("Average Precision")
    ax.set_title("Final holdout ranking: sector context explains part, not all, of model signal")
    ax.set_ylim(0, max(comparison.AP_ci_high.fillna(comparison.AP)) * 1.2)
    ax.grid(axis="y", alpha=0.22)
    for index, value in enumerate(values):
        ax.text(index, value + 0.012, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    plt.close(fig)


def _write_report(
    development: pd.DataFrame,
    holdout: pd.DataFrame,
    comparison: pd.DataFrame,
    prevalence: pd.DataFrame,
    within_sector: pd.DataFrame,
    differences: list[dict[str, float | str]],
    diagnostics: dict[str, float | int],
) -> None:
    models = comparison.set_index("model")
    logistic_difference = next(row for row in differences if row["estimand"] == "Logistic_minus_Sector-only")
    hgb_difference = next(row for row in differences if row["estimand"] == "HGB_minus_Sector-only")
    eligible = within_sector[within_sector.eligible]
    drift = prevalence.sort_values("prevalence_change", ascending=False)
    rank_correlation = float(
        prevalence.development_gap_prevalence.rank().corr(prevalence.holdout_gap_prevalence.rank())
    )
    top_rises = ", ".join(
        f"{row.sector_code} ({row.prevalence_change:+.3f})" for row in drift.head(3).itertuples()
    )
    smallest_changes = ", ".join(
        f"{row.sector_code} ({row.prevalence_change:+.3f})" for row in drift.tail(3).itertuples()
    )
    lines = [
        "# Assignment 6.8C: Sector-Only Benchmark",
        "",
        "## Purpose and design",
        "",
        "This post-assignment benchmark asks how much frozen final-holdout ranking performance can be obtained from sector identity alone. Each sector receives its pooled development out-of-fold gap prevalence from `a6_baseline_oof_predictions.csv`. The mapping is then frozen and applied to the 2021-2023 holdout without reading holdout labels. No classifier was refit and no label, probability, row, or threshold was changed.",
        "",
        f"The development artifact contains {len(development):,} unique OOF evaluation rows through 2020. It is the committed leakage-safe development label population available for this benchmark; it is not a reconstruction of the final full-development fit. All {holdout.sector_code.nunique()} holdout sectors were observed in development, so no unseen-sector fallback was used.",
        "",
        "## Final holdout comparison",
        "",
        "| benchmark | AP | AP / prevalence | ROC-AUC | Brier | top-10% lift | 95% MSA-cluster AP CI |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in comparison.itertuples():
        interval = "not estimated" if pd.isna(row.AP_ci_low) else f"{row.AP_ci_low:.3f}-{row.AP_ci_high:.3f}"
        lines.append(
            f"| {row.model} | {row.AP:.3f} | {row.AP_prevalence_ratio:.2f} | "
            f"{row.ROC_AUC:.3f} | {row.Brier:.3f} | {row.top10_lift:.2f} | {interval} |"
        )
    lines.extend(
        [
            "",
            f"Sector-only AP is {models.loc['Sector-only', 'AP']:.3f}, compared with the no-information prevalence benchmark of {models.loc['Prevalence', 'AP']:.3f}. Logistic adds {float(logistic_difference['observed']):.3f} AP over sector-only ({float(logistic_difference['observed']) / models.loc['Sector-only', 'AP']:.1%} relative), while HGB adds {float(hgb_difference['observed']):.3f}. Sector composition is therefore a meaningful benchmark, but the frozen models retain ranking information beyond sector identity.",
            "",
            "Sector-only scores have only 19 distinct values. Top-decile lift is computed with the existing tie-aware boundary rule and should not be interpreted as precise within-sector prioritization.",
            "",
            "## Paired MSA-cluster uncertainty",
            "",
            f"Seed `{SEED}` requested {REPLICATIONS:,} paired replications over {holdout.cbsa_code.nunique()} whole MSA clusters; {int(diagnostics['valid_replications']):,} were valid and {int(diagnostics['invalid_replications']):,} were excluded for containing one target class. Sector-only AP has a 95% percentile CI of {models.loc['Sector-only', 'AP_ci_low']:.3f}-{models.loc['Sector-only', 'AP_ci_high']:.3f}.",
            "",
            f"The paired Logistic-minus-sector difference is {float(logistic_difference['observed']):.3f}, with CI [{float(logistic_difference['ci_low']):.3f}, {float(logistic_difference['ci_high']):.3f}] and {float(logistic_difference['proportion_above_zero']):.1%} of valid replications above zero. The HGB-minus-sector difference is {float(hgb_difference['observed']):.3f}, with CI [{float(hgb_difference['ci_low']):.3f}, {float(hgb_difference['ci_high']):.3f}] and {float(hgb_difference['proportion_above_zero']):.1%} above zero. Predictions remain frozen, so these intervals do not include refitting uncertainty.",
            "",
            "## Within-sector Logistic ranking",
            "",
            f"Sector-only cannot rank two rows in the same sector. Logistic is therefore evaluated separately within sectors, using the existing minimum of 30 positive holdout labels. {len(eligible)} of {len(within_sector)} sectors are eligible; {int((~within_sector.eligible).sum())} are suppressed. Among eligible sectors, median Logistic AP is {eligible.logistic_AP.median():.3f}, median natural prevalence is {eligible.prevalence.median():.3f}, median AP/prevalence is {eligible.AP_prevalence_ratio.median():.2f}, and AP exceeds prevalence in {int((eligible.logistic_AP > eligible.prevalence).sum())} sectors. These subgroup estimates are descriptive and not separately bootstrapped.",
            "",
            "## Sector prevalence drift",
            "",
            f"The rank correlation between development and holdout sector prevalence is {rank_correlation:.3f}. The largest increases are {top_rises}; the smallest changes are {smallest_changes}. This drift table is contextual evidence, not a recalibration step: holdout prevalence was never used to create sector scores.",
            "",
            "## Relationship to Assignment 5",
            "",
            "Assignment 5 R-squared describes how much variation the expected-startup regression explains in a continuous startup-rate outcome. Assignment 6 Average Precision evaluates ranking of a binary, fold-defined entrepreneurial-response gap. They answer different questions and should not be compared as if they shared a scale.",
            "",
            "## Interpretation and limitations",
            "",
            "Sector identity captures broad structural differences in gap prevalence, while the positive incremental AP results show that the frozen models rank risk beyond those broad sector rates. This is predictive association, not a causal sector effect. The comparison inherits complete-case selection, label-model dependence, 2-digit sector aggregation, only three holdout target years, and possible temporal regime change. Pooled development OOF labels are appropriate for a committed leakage-safe benchmark, but they are not identical to labels from a hypothetical single full-development refit.",
            "",
            "## Outputs",
            "",
            "- `reports/tables/a6_sector_only_model_comparison.csv`",
            "- `reports/tables/a6_sector_prevalence_development_holdout.csv`",
            "- `reports/tables/a6_sector_within_logistic_ranking.csv`",
            "- `reports/figures/a6_sector_only_ap_comparison.png`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_sector_benchmark() -> dict[str, object]:
    development, holdout, canonical = _load_inputs()
    rates = fit_sector_prevalence(development)
    scored = score_sector_prevalence(holdout, rates)

    title_map = holdout[["sector_code", "sector_title"]].drop_duplicates()
    if title_map.sector_code.duplicated().any():
        raise ValueError("Holdout sector codes do not map to unique titles")
    holdout_rates = holdout.groupby("sector_code", as_index=False).agg(
        holdout_n=("actual_gap", "size"),
        holdout_gap_n=("actual_gap", "sum"),
        holdout_gap_prevalence=("actual_gap", "mean"),
    )
    prevalence = rates.merge(holdout_rates, on="sector_code", how="outer", validate="one_to_one")
    prevalence = prevalence.merge(title_map, on="sector_code", how="left", validate="one_to_one")
    if prevalence[["development_gap_prevalence", "holdout_gap_prevalence"]].isna().any().any():
        raise ValueError("Development and holdout sector coverage must match exactly")
    prevalence["prevalence_change"] = (
        prevalence.holdout_gap_prevalence - prevalence.development_gap_prevalence
    )

    holdout_canonical = canonical[canonical.dataset.eq("holdout")].set_index("model")
    baseline_score = float(holdout_canonical.loc["prevalence_benchmark", "classification_threshold"])
    score_columns = {
        "Prevalence": np.full(len(scored), baseline_score),
        "Sector-only": scored.sector_only_probability.to_numpy(),
        "Logistic": scored.predicted_probability_logistic.to_numpy(),
        "HGB": scored.predicted_probability_hgb.to_numpy(),
    }
    rows = []
    for model, scores in score_columns.items():
        row = {"model": model, **benchmark_performance(scored.actual_gap, scores)}
        row["score_source"] = {
            "Prevalence": "frozen final-development prevalence",
            "Sector-only": "pooled development OOF sector prevalence",
            "Logistic": "frozen final-holdout probabilities",
            "HGB": "frozen final-holdout probabilities",
        }[model]
        rows.append(row)
    comparison = pd.DataFrame(rows)

    for model, canonical_name in (("Prevalence", "prevalence_benchmark"), ("Logistic", "logistic"), ("HGB", "hist_gradient_boosting")):
        expected = float(holdout_canonical.loc[canonical_name, "AP"])
        observed = float(comparison.loc[comparison.model.eq(model), "AP"].iloc[0])
        if not np.isclose(expected, observed, atol=1e-12):
            raise ValueError(f"{model} AP no longer matches the canonical holdout artifact")

    bootstrap = paired_cluster_bootstrap_ap(
        scored,
        cluster_column="cbsa_code",
        label_column="actual_gap",
        prediction_columns={
            "Sector-only": "sector_only_probability",
            "Logistic": "predicted_probability_logistic",
            "HGB": "predicted_probability_hgb",
        },
        comparison=("Logistic", "Sector-only"),
        replications=REPLICATIONS,
        seed=SEED,
        return_replications=True,
    )
    bootstrap_summary = bootstrap.summary.set_index("estimand")
    comparison["AP_ci_low"] = comparison.model.map(bootstrap_summary.ci_low)
    comparison["AP_ci_high"] = comparison.model.map(bootstrap_summary.ci_high)
    logistic_difference = _difference_summary(
        bootstrap.replications,
        higher="Logistic",
        lower="Sector-only",
        observed=float(models_ap(comparison, "Logistic") - models_ap(comparison, "Sector-only")),
    )
    hgb_difference = _difference_summary(
        bootstrap.replications,
        higher="HGB",
        lower="Sector-only",
        observed=float(models_ap(comparison, "HGB") - models_ap(comparison, "Sector-only")),
    )

    within_sector = within_sector_logistic_performance(scored, minimum_positives=30)
    within_sector = within_sector.merge(title_map, on="sector_code", how="left", validate="one_to_one")
    output_columns = [
        "model", "n", "prevalence", "AP", "AP_prevalence_ratio", "ROC_AUC", "Brier",
        "top10_lift", "AP_ci_low", "AP_ci_high", "score_source",
    ]
    COMPARISON_TABLE.parent.mkdir(parents=True, exist_ok=True)
    comparison[output_columns].to_csv(COMPARISON_TABLE, index=False, float_format="%.10g")
    prevalence.to_csv(PREVALENCE_TABLE, index=False, float_format="%.10g")
    within_sector.to_csv(WITHIN_SECTOR_TABLE, index=False, float_format="%.10g")
    _write_figure(comparison)
    _write_report(
        development,
        scored,
        comparison,
        prevalence,
        within_sector,
        [logistic_difference, hgb_difference],
        bootstrap.diagnostics,
    )
    return {
        "development_rows": len(development),
        "holdout_rows": len(scored),
        "sectors": int(scored.sector_code.nunique()),
        "msas": int(scored.cbsa_code.nunique()),
        "comparison": comparison[output_columns].to_dict(orient="records"),
        "differences": [logistic_difference, hgb_difference],
        "bootstrap_diagnostics": bootstrap.diagnostics,
        "outputs": [str(COMPARISON_TABLE), str(PREVALENCE_TABLE), str(WITHIN_SECTOR_TABLE), str(FIGURE), str(REPORT)],
    }


def models_ap(comparison: pd.DataFrame, model: str) -> float:
    return float(comparison.loc[comparison.model.eq(model), "AP"].iloc[0])


if __name__ == "__main__":
    print(json.dumps(run_sector_benchmark(), indent=2))
