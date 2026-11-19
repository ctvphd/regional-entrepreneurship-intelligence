"""Generate A6.8E holdout drift and complete-case coverage diagnostics."""

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

from regional_entrepreneurship_intelligence.models.baseline import EXTENDED_REQUIRED
from regional_entrepreneurship_intelligence.models.drift_coverage import (
    classify_eligibility,
    exclusion_reason_table,
    standardized_mean_difference,
    standardized_prevalence,
)
from regional_entrepreneurship_intelligence.models.final_holdout import EXPECTED_FEATURES


ROOT = Path(__file__).resolve().parents[3]
TABLES = ROOT / "reports" / "tables"
FIGURES = ROOT / "reports" / "figures"
PANEL = ROOT / "data" / "dashboard" / "dashboard_msa_industry_year.parquet"
HOLDOUT = TABLES / "a6_final_holdout_predictions.csv"
DEVELOPMENT = TABLES / "a6_baseline_oof_predictions.csv"
DEVELOPMENT_EXPECTED = TABLES / "a6_expected_validation_predictions.csv"
YEAR_PERFORMANCE = TABLES / "a6_final_holdout_by_year.csv"
SAMPLE_AUDIT = TABLES / "a6_final_sample_audit.csv"
SIZE_CUTPOINTS = TABLES / "a6_final_msa_size_cutpoints.csv"
TARGET_THRESHOLD = TABLES / "a6_final_target_threshold.csv"

DRIFT_TABLE = TABLES / "a6_holdout_drift_summary.csv"
YEAR_TABLE = TABLES / "a6_holdout_drift_by_year.csv"
COMPARISON_TABLE = TABLES / "a6_holdout_eligible_excluded_comparison.csv"
REASONS_TABLE = TABLES / "a6_holdout_exclusion_reasons.csv"
SIZE_TABLE = TABLES / "a6_holdout_exclusion_by_msa_size.csv"
SECTOR_TABLE = TABLES / "a6_holdout_exclusion_by_sector.csv"
ALIGNMENT_FIGURE = FIGURES / "a6_holdout_alignment_evidence.png"
SIZE_FIGURE = FIGURES / "a6_holdout_exclusion_by_msa_size.png"
REPORT = ROOT / "reports" / "assignment6_holdout_drift_and_coverage.md"

TARGET_REQUIRED = tuple(
    ["target_startup_rate"]
    + [f"target_{name}" for name in EXPECTED_FEATURES if name not in {"sector_code", "year"}]
)
PREDICTOR_REQUIRED = tuple(
    name for name in EXTENDED_REQUIRED if name not in {"sector_code", "year"}
)
COMPARISON_VARIABLES = (
    "startup_rate",
    "target_startup_rate",
    "startup_rate_lag1",
    "employment_growth",
    "establishment_growth",
    "payroll_growth",
    "wage_growth",
    "acs_population",
    "acs_population_growth",
    "median_household_income",
    "educational_attainment_pct",
    "labor_force_participation_pct",
    "unemployment_rate",
)


def _load_panel() -> pd.DataFrame:
    panel = pd.read_parquet(PANEL).rename(
        columns={"msa_name": "cbsa_name", "sector_name": "sector_title"}
    )
    panel["cbsa_code"] = panel.cbsa_code.astype(str)
    panel["sector_code"] = panel.sector_code.astype(str)
    panel["year"] = pd.to_numeric(panel.year, errors="raise").astype(int)
    if panel.duplicated(["cbsa_code", "sector_code", "year"]).any():
        raise ValueError("Frozen panel contains duplicate MSA-sector-year rows")
    return panel


def _build_holdout_candidates(panel: pd.DataFrame) -> pd.DataFrame:
    predictor = panel[panel.year.isin([2018, 2019, 2020])].copy().rename(
        columns={"year": "predictor_year"}
    )
    target = panel[panel.year.isin([2021, 2022, 2023])].copy().rename(
        columns={"year": "target_year"}
    )
    target["predictor_year"] = target.target_year - 3
    target_names = ["startup_rate", *[name for name in EXPECTED_FEATURES if name not in {"sector_code", "year"}]]
    target = target[
        ["cbsa_code", "sector_code", "predictor_year", "target_year", *target_names]
    ].rename(columns={name: f"target_{name}" for name in target_names})
    candidates = predictor.merge(
        target,
        on=["cbsa_code", "sector_code", "predictor_year"],
        how="inner",
        validate="one_to_one",
    )
    candidates = classify_eligibility(
        candidates,
        target_required=TARGET_REQUIRED,
        predictor_required=PREDICTOR_REQUIRED,
    )
    holdout = pd.read_csv(HOLDOUT, dtype={"cbsa_code": str, "sector_code": str})
    keys = ["cbsa_code", "sector_code", "predictor_year", "target_year"]
    candidates = candidates.merge(
        holdout[keys + ["actual_gap", "predicted_probability_logistic"]],
        on=keys,
        how="left",
        validate="one_to_one",
    )
    if len(candidates) != 12_091:
        raise ValueError("Reconstructed holdout candidate count changed")
    if candidates.actual_gap.notna().sum() != 10_304:
        raise ValueError("Frozen holdout predictions do not match reconstructed eligibility")
    if not candidates.eligible.eq(candidates.actual_gap.notna()).all():
        raise ValueError("Reconstructed complete-case eligibility disagrees with frozen scores")
    audit = pd.read_csv(SAMPLE_AUDIT).set_index("sample").loc["holdout"]
    observed_counts = (
        len(candidates),
        int(candidates.target_label_eligible.sum()),
        int(candidates.eligible.sum()),
        int((~candidates.eligible).sum()),
    )
    expected_counts = (
        int(audit.candidate_pairs),
        int(audit.target_label_eligible_pairs),
        int(audit.complete_case_eligible_pairs),
        int(audit.excluded_pairs),
    )
    if observed_counts != expected_counts:
        raise ValueError("Reconstructed eligibility counts disagree with the committed audit")
    return candidates


def _load_development(panel: pd.DataFrame) -> pd.DataFrame:
    oof = pd.read_csv(DEVELOPMENT, dtype={"cbsa_code": str, "sector_code": str})
    expected = pd.read_csv(
        DEVELOPMENT_EXPECTED, dtype={"cbsa_code": str, "sector_code": str}
    )
    expected = expected[expected.model.eq("A")]
    keys = ["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"]
    development = oof.merge(
        expected[
            keys + ["observed_startup_rate", "expected_startup_rate", "residual"]
        ],
        on=keys,
        how="left",
        validate="one_to_one",
    )
    if development[["observed_startup_rate", "expected_startup_rate", "residual"]].isna().any().any():
        raise ValueError("Development OOF rows lack expected-model diagnostics")
    population = panel[["cbsa_code", "sector_code", "year", "acs_population"]]
    development = development.merge(
        population,
        left_on=["cbsa_code", "sector_code", "predictor_year"],
        right_on=["cbsa_code", "sector_code", "year"],
        how="left",
        validate="many_to_one",
    )
    return development


def _assign_size(frame: pd.DataFrame) -> pd.DataFrame:
    cutpoints = pd.read_csv(SIZE_CUTPOINTS).iloc[0]
    lower = float(cutpoints.msa_population_lower_tercile_cutpoint)
    upper = float(cutpoints.msa_population_upper_tercile_cutpoint)
    result = frame.copy()
    result["msa_size_group"] = pd.cut(
        result.acs_population,
        [-np.inf, lower, upper, np.inf],
        labels=["small", "middle", "large"],
        include_lowest=True,
    ).astype("string")
    result["msa_size_group"] = result.msa_size_group.fillna(
        "unclassified_missing_population"
    )
    return result


def _period_summary(
    development: pd.DataFrame,
    eligible: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cutoff = float(pd.read_csv(TARGET_THRESHOLD).iloc[0].p20_residual_cutoff)
    year_performance = pd.read_csv(YEAR_PERFORMANCE)
    year_performance = year_performance[year_performance.model.eq("logistic")].set_index("target_year")

    def row(name: str, frame: pd.DataFrame, *, development_row: bool, ap: float) -> dict:
        observed = frame.observed_startup_rate if development_row else frame.target_startup_rate
        result = {
            "period": name,
            "n": len(frame),
            "gap_prevalence": float(frame.actual_gap.mean()),
            "observed_startup_mean": float(observed.mean()),
            "observed_startup_median": float(observed.median()),
            "logistic_AP": ap,
            "expected_startup_mean": np.nan,
            "expected_startup_median": np.nan,
            "residual_mean": np.nan,
            "residual_median": np.nan,
            "residual_sd": np.nan,
            "residual_p10": np.nan,
            "residual_p20": np.nan,
            "residual_p25": np.nan,
            "share_below_frozen_final_cutoff": np.nan,
            "residual_availability": "not committed; no refit performed",
        }
        if development_row:
            residual = frame.residual
            result.update(
                expected_startup_mean=float(frame.expected_startup_rate.mean()),
                expected_startup_median=float(frame.expected_startup_rate.median()),
                residual_mean=float(residual.mean()),
                residual_median=float(residual.median()),
                residual_sd=float(residual.std(ddof=1)),
                residual_p10=float(residual.quantile(0.10)),
                residual_p20=float(residual.quantile(0.20)),
                residual_p25=float(residual.quantile(0.25)),
                share_below_frozen_final_cutoff=float(residual.le(cutoff).mean()),
                residual_availability="committed fold-validation Model A predictions",
            )
        return result

    development_ap = float(
        pd.read_csv(TABLES / "a6_baseline_model_performance.csv")
        .query("model == 'baseline_1_simple' and fold == 'pooled_oof'")
        .iloc[0]
        .pr_auc
    )
    pooled = pd.DataFrame(
        [
            row("development_oof", development, development_row=True, ap=development_ap),
            row("holdout_pooled", eligible, development_row=False, ap=0.40422477786600497),
        ]
    )
    year_rows = []
    for target_year, group in eligible.groupby("target_year", sort=True):
        year_rows.append(
            row(
                str(int(target_year)),
                group,
                development_row=False,
                ap=float(year_performance.loc[target_year, "AP"]),
            )
        )
    return pooled, pd.DataFrame(year_rows)


def _composition_summary(
    development: pd.DataFrame,
    eligible: pd.DataFrame,
) -> pd.DataFrame:
    development = development.rename(columns={"actual_gap": "actual_gap"})
    raw_development = float(development.actual_gap.mean())
    raw_holdout = float(eligible.actual_gap.mean())
    rows = []
    for label, strata in (
        ("sector", ("sector_code",)),
        ("msa_size", ("msa_size_group",)),
        ("sector_x_msa_size", ("sector_code", "msa_size_group")),
    ):
        result = standardized_prevalence(
            development, eligible, strata=strata, label_column="actual_gap"
        )
        standardized = float(result["standardized_prevalence"])
        rows.append(
            {
                "standardization": label,
                "raw_development_prevalence": raw_development,
                "raw_holdout_prevalence": raw_holdout,
                "holdout_prevalence_at_development_composition": standardized,
                "raw_difference_percentage_points": 100 * (raw_holdout - raw_development),
                "adjusted_difference_percentage_points": 100 * (standardized - raw_development),
                "composition_contribution_percentage_points": 100 * (raw_holdout - standardized),
                "strata_n": result["strata_n"],
            }
        )
    return pd.DataFrame(rows)


def _eligible_excluded_comparison(candidates: pd.DataFrame) -> pd.DataFrame:
    included = candidates[candidates.eligible]
    excluded = candidates[~candidates.eligible]
    rows = []
    for variable in COMPARISON_VARIABLES:
        left = pd.to_numeric(included[variable], errors="coerce")
        right = pd.to_numeric(excluded[variable], errors="coerce")
        rows.append(
            {
                "variable": variable,
                "eligible_available_n": int(left.notna().sum()),
                "excluded_available_n": int(right.notna().sum()),
                "eligible_mean": float(left.mean()),
                "excluded_mean": float(right.mean()),
                "eligible_median": float(left.median()),
                "excluded_median": float(right.median()),
                "standardized_difference_eligible_minus_excluded": standardized_mean_difference(left, right),
            }
        )
    return pd.DataFrame(rows)


def _coverage_tables(candidates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    size = candidates.groupby("msa_size_group", as_index=False, dropna=False).agg(
        candidate_n=("eligible", "size"), eligible_n=("eligible", "sum")
    )
    size["excluded_n"] = size.candidate_n - size.eligible_n
    size["exclusion_rate"] = size.excluded_n / size.candidate_n
    size["candidate_share"] = size.candidate_n / len(candidates)
    size["eligible_share"] = size.eligible_n / int(candidates.eligible.sum())

    sector = candidates.groupby(["sector_code", "sector_title"], as_index=False).agg(
        candidate_n=("eligible", "size"), eligible_n=("eligible", "sum")
    )
    sector["excluded_n"] = sector.candidate_n - sector.eligible_n
    sector["exclusion_rate"] = sector.excluded_n / sector.candidate_n
    sector = sector.sort_values(["exclusion_rate", "sector_code"], ascending=[False, True])
    return size, sector


def _write_figures(
    development: pd.DataFrame,
    pooled: pd.DataFrame,
    by_year: pd.DataFrame,
    by_size: pd.DataFrame,
) -> None:
    cutoff = float(pd.read_csv(TARGET_THRESHOLD).iloc[0].p20_residual_cutoff)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    axes[0].hist(development.residual, bins=50, color="#4C78A8", edgecolor="white", linewidth=0.3)
    axes[0].axvline(cutoff, color="#B65C45", linestyle="--", linewidth=1.5, label="Frozen final cutoff")
    axes[0].set(title="Available development OOF residuals", xlabel="Observed minus expected startup rate", ylabel="Rows")
    axes[0].legend(frameon=False)
    prevalence = pd.concat(
        [pooled[pooled.period.eq("development_oof")], by_year], ignore_index=True
    )
    axes[1].bar(prevalence.period, prevalence.gap_prevalence * 100, color=["#777F8C", "#D9892B", "#D9892B", "#D9892B"])
    axes[1].set(title="Gap prevalence by evaluation period", xlabel="Period", ylabel="Gap prevalence (%)")
    axes[1].set_ylim(0, max(prevalence.gap_prevalence * 100) * 1.25)
    for index, value in enumerate(prevalence.gap_prevalence * 100):
        axes[1].text(index, value + 0.6, f"{value:.1f}%", ha="center", fontsize=9)
    for ax in axes:
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("Alignment evidence without reconstructing uncommitted holdout residuals")
    fig.tight_layout()
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(ALIGNMENT_FIGURE, dpi=180)
    plt.close(fig)

    order = ["small", "middle", "large", "unclassified_missing_population"]
    view = by_size.set_index("msa_size_group").reindex(order).dropna(subset=["candidate_n"])
    display_labels = [
        "Missing population" if label == "unclassified_missing_population" else label
        for label in view.index
    ]
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    bars = ax.bar(display_labels, view.exclusion_rate * 100, color=["#D9892B", "#4C78A8", "#4C8C6A", "#8A8F98"][: len(view)])
    ax.set(title="Complete-case abstention is highest for smaller and unclassified cells", xlabel="Training-cutpoint MSA-size group", ylabel="Excluded candidates (%)")
    ax.tick_params(axis="x", rotation=8)
    ax.grid(axis="y", alpha=0.2)
    for bar, value in zip(bars, view.exclusion_rate * 100):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 1, f"{value:.1f}%", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(SIZE_FIGURE, dpi=180)
    plt.close(fig)


def _write_report(
    pooled: pd.DataFrame,
    by_year: pd.DataFrame,
    composition: pd.DataFrame,
    comparison: pd.DataFrame,
    reasons: pd.DataFrame,
    by_size: pd.DataFrame,
    by_sector: pd.DataFrame,
    candidates: pd.DataFrame,
) -> None:
    dev = pooled.set_index("period").loc["development_oof"]
    hold = pooled.set_index("period").loc["holdout_pooled"]
    audit = pd.read_csv(SAMPLE_AUDIT).set_index("sample").loc["holdout"]
    comp = composition.set_index("standardization")
    compare = comparison.set_index("variable")
    reason = reasons.set_index("reason")
    size = by_size.set_index("msa_size_group")
    high_sector = by_sector.head(3)
    low_sector = by_sector.tail(3).sort_values("exclusion_rate")
    label_capable_excluded = int((~candidates.eligible & candidates.target_label_eligible).sum())
    excluded = candidates[~candidates.eligible]
    simple_benchmark_feasible = int(
        (
            excluded.target_startup_rate.notna()
            & excluded.sector_code.notna()
            & excluded.target_year.notna()
        ).sum()
    )
    year_lines = [
        f"- {row.period}: prevalence {row.gap_prevalence:.1%}, observed startup mean/median {row.observed_startup_mean:.3f}/{row.observed_startup_median:.3f}, Logistic AP {row.logistic_AP:.3f}."
        for row in by_year.itertuples()
    ]
    size_lines = [
        f"- {group}: {int(row.excluded_n):,} of {int(row.candidate_n):,} excluded ({row.exclusion_rate:.1%})."
        for group, row in size.iterrows()
    ]
    high_text = ", ".join(
        f"{row.sector_code} ({row.exclusion_rate:.1%})" for row in high_sector.itertuples()
    )
    low_text = ", ".join(
        f"{row.sector_code} ({row.exclusion_rate:.1%})" for row in low_sector.itertuples()
    )
    lines = [
        "# Assignment 6.8E: Holdout Prevalence Drift and Complete-Case Scope",
        "",
        "## Purpose",
        "",
        "This diagnostic explains the development-to-holdout prevalence increase and pairs predictive performance with the population that can actually be scored. It uses committed labels, probabilities, expected-model validation predictions, sample audits, and the frozen descriptive panel. No model was refit, no excluded value was imputed, and no production rule changed.",
        "",
        "## Development vs Holdout Prevalence",
        "",
        f"Pooled development OOF prevalence is {dev.gap_prevalence:.3%}; final holdout prevalence is {hold.gap_prevalence:.3%}, an increase of {(hold.gap_prevalence - dev.gap_prevalence) * 100:.3f} percentage points. The development OOF labels use fold-local expected models and thresholds; the final holdout uses the frozen full-development expected model and cutoff, so the comparison combines temporal outcome change with benchmark-transfer differences.",
        "",
        "## Observed vs Expected Startup Activity",
        "",
        f"Mean observed startup activity rises from {dev.observed_startup_mean:.3f} in development OOF rows to {hold.observed_startup_mean:.3f} in eligible holdout rows; medians rise from {dev.observed_startup_median:.3f} to {hold.observed_startup_median:.3f}. A simple decline in raw observed startup activity therefore does not explain the higher gap prevalence.",
        "",
        f"Development OOF expected activity averages {dev.expected_startup_mean:.3f}, with mean residual {dev.residual_mean:.3f}. Row-level final-holdout expected values and continuous residuals were not committed. Recreating them would require refitting the production expected model, which this diagnostic explicitly forbids. Accordingly, the analysis does not claim whether expected activity moved upward or quantify a continuous holdout residual shift.",
        "",
        "## Residual Distribution Shift",
        "",
        f"Available development OOF residuals have mean {dev.residual_mean:.3f}, median {dev.residual_median:.3f}, SD {dev.residual_sd:.3f}, p10 {dev.residual_p10:.3f}, p20 {dev.residual_p20:.3f}, and p25 {dev.residual_p25:.3f}. {dev.share_below_frozen_final_cutoff:.1%} fall below the frozen final cutoff of {float(pd.read_csv(TARGET_THRESHOLD).iloc[0].p20_residual_cutoff):.6f}. These fold-validation residuals are not interchangeable with final-model in-sample residuals. Holdout residual quantiles are reported as unavailable, not reconstructed.",
        "",
        "## Holdout Years",
        "",
        *year_lines,
        "",
        "The low 2022 prevalence followed by the high 2023 prevalence supports temporal heterogeneity rather than a uniform one-direction shift.",
        "",
        "## Composition Standardization",
        "",
        f"Reweighting holdout sector rates to development sector shares gives {comp.loc['sector', 'holdout_prevalence_at_development_composition']:.3%}, versus raw holdout prevalence {hold.gap_prevalence:.3%}. Sector mix accounts for only {comp.loc['sector', 'composition_contribution_percentage_points']:.3f} percentage points of the raw increase. MSA-size standardization gives {comp.loc['msa_size', 'holdout_prevalence_at_development_composition']:.3%}; its composition contribution is {comp.loc['msa_size', 'composition_contribution_percentage_points']:.3f} points. Joint sector-by-size standardization gives {comp.loc['sector_x_msa_size', 'holdout_prevalence_at_development_composition']:.3%}, leaving an adjusted increase of {comp.loc['sector_x_msa_size', 'adjusted_difference_percentage_points']:.3f} points. Composition therefore does not explain the 4.123-point shift.",
        "",
        "## Complete-Case Eligibility",
        "",
        f"The exact holdout universe has {int(audit.candidate_pairs):,} t-to-t+3 candidate pairs. {int(audit.target_label_eligible_pairs):,} have complete expected-model target inputs, {int(audit.complete_case_eligible_pairs):,} satisfy both target and predictor completeness, and {int(audit.excluded_pairs):,} are excluded ({audit.exclusion_share:.3%}). Scoreable coverage is {1 - audit.exclusion_share:.3%}.",
        "",
        "## Who Is Excluded?",
        "",
        f"Eligible predictor-year population averages {compare.loc['acs_population', 'eligible_mean']:,.0f}, versus {compare.loc['acs_population', 'excluded_mean']:,.0f} among available excluded rows. Predictor-year startup rate averages {compare.loc['startup_rate', 'eligible_mean']:.3f} versus {compare.loc['startup_rate', 'excluded_mean']:.3f}. Target-year observed startup rate is available for all candidates and averages {compare.loc['target_startup_rate', 'eligible_mean']:.3f} versus {compare.loc['target_startup_rate', 'excluded_mean']:.3f}. Standardized differences and available Ns are retained in the comparison CSV so structural missingness is never converted to zero.",
        "",
        *size_lines,
        "",
        f"Highest sector exclusion rates are {high_text}; lowest are {low_text}. Exclusion describes scoreability, not predictive performance.",
        "",
        "## Exclusion Reasons",
        "",
        f"Target benchmark inputs are incomplete for {int(reason.loc['target benchmark inputs incomplete', 'excluded_n']):,} candidates; predictor complete-case inputs are incomplete for {int(reason.loc['predictor complete-case inputs incomplete', 'excluded_n']):,}; {int(reason.loc['both target and predictor inputs incomplete', 'excluded_n']):,} have both problems. Counts overlap by design. Field-level reasons are reported separately, with no imputation.",
        "",
        "## Interpretation of Drift",
        "",
        "The evidence supports a mixed benchmark-relative temporal shift, not a raw startup decline or composition-only explanation. Raw observed startup activity is higher in the holdout, sector/size standardization leaves nearly the full prevalence increase, and annual prevalence varies sharply. Because final holdout expected values and residual magnitudes were not persisted, the analysis cannot distinguish real residual deterioration from expected-model benchmark transfer as finely as a frozen residual artifact would permit.",
        "",
        "## Interpretation of AP",
        "",
        f"AP = 0.404 describes ranking performance among the {int(audit.complete_case_eligible_pairs):,} MSA-industry-year observations that satisfy exact temporal pairing, expected-label availability, and the locked complete-case predictor rules. It does not describe the {int(audit.excluded_pairs):,} abstained candidate cells, all theoretical MSA-industry combinations, non-metropolitan areas, or cells without sufficient historical and regional data. Performance should therefore be presented together with {1 - audit.exclusion_share:.1%} candidate coverage.",
        "",
        "## Abstention Framework",
        "",
        f"Excluded cells should be called insufficient-data model abstentions, not negative predictions. Of the excluded cells, {label_capable_excluded:,} retain the production gap-label inputs but lack predictor completeness; no classifier probability is generated. All {simple_benchmark_feasible:,} excluded rows retain observed startup activity plus sector and year, so a simpler sector-year benchmark is technically feasible for diagnostic research. It would define a different estimand and must not be substituted into production without a separately locked design and validation.",
        "",
        "## Presentation Language",
        "",
        f'“Gap prevalence rose from {dev.gap_prevalence:.1%} in development to {hold.gap_prevalence:.1%} in the holdout; diagnostics show that sector and MSA-size composition explain little of the increase and that raw observed startup activity did not decline, leaving a mixed benchmark-relative temporal shift.”',
        "",
        f'“The model’s AP of 0.404 applies to the {1 - audit.exclusion_share:.1%} of exact holdout candidate cells with sufficient target and predictor data; smaller, lower-startup, and population-unclassified cells are more likely to be insufficient-data abstentions.”',
        "",
        "## Limitations and Implications",
        "",
        "Development OOF and final holdout labels use related but not identical expected-model fits and threshold construction. Continuous holdout residual drift cannot be audited from committed artifacts without prohibited refitting. Complete-case contrasts are descriptive and may reflect overlapping missingness mechanisms. These limits should be stated in the final presentation and motivate, but do not implement, future dissertation work on abstention-aware or reduced-data models.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_drift_coverage() -> dict[str, object]:
    panel = _load_panel()
    candidates = _assign_size(_build_holdout_candidates(panel))
    development = _assign_size(_load_development(panel))
    eligible = candidates[candidates.eligible].copy()
    eligible["actual_gap"] = eligible.actual_gap.astype(int)
    development["actual_gap"] = development.actual_gap.astype(int)

    pooled, by_year = _period_summary(development, eligible)
    composition = _composition_summary(development, eligible)
    drift = pooled.merge(
        pd.DataFrame(
            {
                "period": ["development_oof", "holdout_pooled"],
                "raw_prevalence_difference_percentage_points": [
                    0.0,
                    100 * (eligible.actual_gap.mean() - development.actual_gap.mean()),
                ],
            }
        ),
        on="period",
        validate="one_to_one",
    )
    comparison = _eligible_excluded_comparison(candidates)
    reasons = exclusion_reason_table(
        candidates,
        target_required=TARGET_REQUIRED,
        predictor_required=PREDICTOR_REQUIRED,
    )
    by_size, by_sector = _coverage_tables(candidates)

    TABLES.mkdir(parents=True, exist_ok=True)
    drift.to_csv(DRIFT_TABLE, index=False, float_format="%.10g")
    by_year.to_csv(YEAR_TABLE, index=False, float_format="%.10g")
    comparison.to_csv(COMPARISON_TABLE, index=False, float_format="%.10g")
    reasons.to_csv(REASONS_TABLE, index=False, float_format="%.10g")
    by_size.to_csv(SIZE_TABLE, index=False, float_format="%.10g")
    by_sector.to_csv(SECTOR_TABLE, index=False, float_format="%.10g")
    composition.to_csv(TABLES / "a6_holdout_composition_standardization.csv", index=False, float_format="%.10g")
    _write_figures(development, pooled, by_year, by_size)
    _write_report(
        pooled, by_year, composition, comparison, reasons, by_size, by_sector, candidates
    )
    audit = pd.read_csv(SAMPLE_AUDIT).set_index("sample").loc["holdout"]
    return {
        "development_prevalence": float(development.actual_gap.mean()),
        "holdout_prevalence": float(eligible.actual_gap.mean()),
        "candidate_n": len(candidates),
        "eligible_n": int(candidates.eligible.sum()),
        "excluded_n": int((~candidates.eligible).sum()),
        "coverage": 1 - float(audit.exclusion_share),
        "composition": composition.to_dict(orient="records"),
        "outputs": [
            str(DRIFT_TABLE), str(YEAR_TABLE), str(COMPARISON_TABLE), str(REASONS_TABLE),
            str(SIZE_TABLE), str(SECTOR_TABLE),
            str(TABLES / "a6_holdout_composition_standardization.csv"),
            str(ALIGNMENT_FIGURE), str(SIZE_FIGURE), str(REPORT),
        ],
    }


if __name__ == "__main__":
    print(json.dumps(run_drift_coverage(), indent=2))
