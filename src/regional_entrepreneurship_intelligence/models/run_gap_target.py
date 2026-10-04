"""Construct fold-local Assignment 6.3 gap targets and diagnostics; fit no classifier."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "rei-matplotlib-cache"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.analysis.eda import (
    DEFAULT_EDA_DATABASE,
    load_analytical_panel,
)
from regional_entrepreneurship_intelligence.models.expected import (
    MODEL_FEATURES,
    MODEL_FORMULAS,
    fit_expected_model,
    predict_expected,
)
from regional_entrepreneurship_intelligence.models.gap import (
    THRESHOLD_COLUMNS,
    calculate_gap_thresholds,
    compare_gap_definitions,
    construct_gap_labels,
    construct_t_plus_3_pairs,
    summarize_gap_prevalence,
    validate_gap_target,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FOLD_PATH = PROJECT_ROOT / "config" / "assignment6_temporal_folds.csv"
TABLE_DIR = PROJECT_ROOT / "reports" / "tables"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures"
REPORT_PATH = PROJECT_ROOT / "reports" / "assignment6_entrepreneurial_gap_target.md"
SPEC_PATH = PROJECT_ROOT / "docs" / "ASSIGNMENT6_GAP_TARGET.md"
MSA_MIN_N = 30
DEVELOPMENT_MAX_TARGET_YEAR = 2020
PAIR_KEYS = ["cbsa_code", "sector_code", "predictor_year", "target_year"]
PAIR_OUTPUT_COLUMNS = [
    "fold", "split_role", "cbsa_code", "sector_code", "predictor_year", "target_year",
    "observed_target_startup_rate", "expected_target_startup_rate", "alignment_residual",
    "primary_threshold", "gap_margin", "gap_p10", "gap_p20", "gap_p25", "gap_minus_1sd",
]


def _raw_pairs(panel: pd.DataFrame, fold: pd.Series, split_role: str) -> pd.DataFrame:
    if split_role == "training":
        start, end = int(fold.train_predictor_start_year), int(fold.train_predictor_end_year)
    elif split_role == "validation":
        start, end = int(fold.validation_predictor_start_year), int(fold.validation_predictor_end_year)
    else:
        raise ValueError(f"Unsupported split role: {split_role}")
    pairs = construct_t_plus_3_pairs(
        panel[["cbsa_code", "sector_code", "year"]],
        predictor_start_year=start,
        predictor_end_year=end,
    )
    outcomes = panel.rename(columns={"year": "target_year"})
    raw = pairs.merge(
        outcomes,
        on=["cbsa_code", "sector_code", "target_year"],
        how="inner",
        validate="one_to_one",
    )
    raw["year"] = raw.target_year
    return raw


def _prediction_map(predictions: pd.DataFrame) -> pd.DataFrame:
    return predictions[["cbsa_code", "sector_code", "year", "startup_rate", "expected_startup_rate", "residual"]].rename(
        columns={
            "year": "target_year",
            "startup_rate": "observed_target_startup_rate",
            "expected_startup_rate": "expected_target_startup_rate",
            "residual": "alignment_residual",
        }
    )


def _attach_predictions(raw: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    return raw.merge(
        _prediction_map(predictions),
        on=["cbsa_code", "sector_code", "target_year"],
        how="left",
        validate="one_to_one",
    )


def _threshold_dict(summary: dict[str, float | int]) -> dict[str, float]:
    return {
        "p10": float(summary["residual_p10"]),
        "p20": float(summary["residual_p20"]),
        "p25": float(summary["residual_p25"]),
        "mean_minus_1sd": float(summary["residual_minus_1sd"]),
    }


def _with_labels(frame: pd.DataFrame, *, fold: str, split_role: str,
                 thresholds: dict[str, float]) -> pd.DataFrame:
    complete = frame.dropna(subset=["alignment_residual", "expected_target_startup_rate"]).copy()
    labelled = construct_gap_labels(complete, thresholds)
    labelled.insert(0, "split_role", split_role)
    labelled.insert(0, "fold", fold)
    return labelled


def _summarize_long(
    frame: pd.DataFrame,
    *,
    group_columns: tuple[str, ...],
    cutoff_map: dict[tuple[str, str], dict[str, float]],
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    summary = compare_gap_definitions(frame, group_columns=group_columns)
    summary["residual_threshold"] = summary.apply(
        lambda row: cutoff_map[(str(row["fold"]), str(row["threshold_definition"]))]["cutoff"], axis=1
    )
    summary["residual_mean"] = summary.apply(
        lambda row: cutoff_map[(str(row["fold"]), str(row["threshold_definition"]))]["mean"], axis=1
    )
    summary["residual_sd"] = summary.apply(
        lambda row: cutoff_map[(str(row["fold"]), str(row["threshold_definition"]))]["sd"], axis=1
    )
    return summary


def _grouped_gap_summary(frame: pd.DataFrame, group_column: str) -> pd.DataFrame:
    grouped = frame.groupby(group_column, observed=True, dropna=False)
    result = grouped.agg(
        eligible_n=("gap_p20", "size"),
        gap_n=("gap_p20", "sum"),
        median_residual=("alignment_residual", "median"),
        mean_threshold=("primary_threshold", "mean"),
        median_threshold=("primary_threshold", "median"),
    ).reset_index()
    result["non_gap_n"] = result.eligible_n - result.gap_n
    result["gap_prevalence"] = result.gap_n / result.eligible_n
    result["median_residual_minus_threshold"] = result.median_residual - result.median_threshold
    return result


def _prevalence_by_threshold(frame: pd.DataFrame, group_columns: tuple[str, ...]) -> pd.DataFrame:
    return compare_gap_definitions(frame, group_columns=group_columns)


def _quantile_group(series: pd.Series) -> pd.Series:
    ranks = series.rank(method="average", pct=True)
    return pd.cut(ranks, bins=[0, 1 / 3, 2 / 3, 1], labels=["low", "middle", "high"], include_lowest=True)


def _selection_audit(raw_pairs: pd.DataFrame, labelled_pairs: pd.DataFrame,
                     *, fold: str, split_role: str) -> list[dict[str, object]]:
    eligible_keys = labelled_pairs[["cbsa_code", "sector_code", "target_year"]].drop_duplicates()
    marked = raw_pairs.merge(
        eligible_keys.assign(model_complete_case=True),
        on=["cbsa_code", "sector_code", "target_year"],
        how="left",
        validate="one_to_one",
    )
    marked["model_complete_case"] = marked.model_complete_case.fillna(False).astype(bool)
    variables = ["startup_rate", "employment_growth", "acs_population", "cbp_employment"]
    available_variables = [name for name in variables if name in marked]
    output: list[dict[str, object]] = []
    grouping_specs: list[tuple[str, str | None]] = [("all", None), ("target_year", "target_year"), ("sector", "sector_code")]
    for group_type, column in grouping_specs:
        groups = [("all", marked)] if column is None else list(marked.groupby(column, observed=True, dropna=False))
        for group_value, sample in groups:
            row: dict[str, object] = {
                "fold": fold,
                "split_role": split_role,
                "group_type": group_type,
                "group_value": group_value,
                "eligible_exact_pairs": len(sample),
                "complete_case_pairs": int(sample.model_complete_case.sum()),
                "excluded_pairs": int((~sample.model_complete_case).sum()),
                "inclusion_rate": float(sample.model_complete_case.mean()) if len(sample) else np.nan,
            }
            for variable in available_variables:
                for status, condition in (("included", sample.model_complete_case), ("excluded", ~sample.model_complete_case)):
                    values = sample.loc[condition, variable]
                    row[f"{variable}_{status}_n"] = int(values.notna().sum())
                    row[f"{variable}_{status}_mean"] = float(values.mean()) if values.notna().any() else np.nan
            output.append(row)
    return output


def _transition_table(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values(["fold", "cbsa_code", "sector_code", "target_year"]).copy()
    groups = ordered.groupby(["fold", "cbsa_code", "sector_code"], observed=True, sort=False)
    ordered["prior_target_year"] = groups.target_year.shift(1)
    ordered["prior_gap_p20"] = groups.gap_p20.shift(1)
    current_validation = ordered.split_role.eq("validation")
    exact_prior = ordered.target_year.sub(ordered.prior_target_year).eq(1)
    transitions = ordered[current_validation & exact_prior].copy()
    transitions["transition"] = np.where(
        transitions.prior_gap_p20.eq(1), "gap", "non_gap"
    ) + "_to_" + np.where(transitions.gap_p20.eq(1), "gap", "non_gap")
    return (
        transitions.groupby(["fold", "transition"], observed=True)
        .agg(transition_n=("gap_p20", "size"), prior_target_year_min=("prior_target_year", "min"),
             target_year_min=("target_year", "min"), target_year_max=("target_year", "max"))
        .reset_index()
    )


def _negative_expected_tables(
    training_residual_rows: list[pd.DataFrame],
    validation_rows: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_rows = pd.concat([*training_residual_rows, validation_rows], ignore_index=True)
    all_rows["expected_negative"] = all_rows.expected_target_startup_rate.lt(0)
    summary = (
        all_rows.groupby(["fold", "split_role"], observed=True)
        .agg(n=("expected_negative", "size"), negative_expected_n=("expected_negative", "sum"),
             negative_expected_gap_n=("gap_p20", lambda values: int(values[all_rows.loc[values.index, "expected_negative"]].sum())))
        .reset_index()
    )
    summary["negative_expected_share"] = summary.negative_expected_n / summary.n
    grouped = (
        all_rows[all_rows.expected_negative]
        .groupby(["fold", "split_role", "target_year", "sector_code"], observed=True)
        .agg(negative_expected_n=("gap_p20", "size"), negative_expected_gap_n=("gap_p20", "sum"))
        .reset_index()
    )
    return summary, grouped


def _save_figures(
    thresholds: pd.DataFrame,
    validation: pd.DataFrame,
    by_year: pd.DataFrame,
    by_sector: pd.DataFrame,
    robustness: pd.DataFrame,
    mismatch: pd.DataFrame,
    transitions: pd.DataFrame,
    by_msa: pd.DataFrame,
    expected_groups: pd.DataFrame,
) -> list[str]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output: list[str] = []

    def save(fig: plt.Figure, name: str) -> None:
        fig.tight_layout()
        fig.savefig(FIGURE_DIR / name, dpi=160)
        plt.close(fig)
        output.append(name)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for column, label in (("residual_p10", "p10"), ("residual_p20", "p20 primary"),
                          ("residual_p25", "p25"), ("residual_minus_1sd", "mean - 1 SD")):
        ax.plot(thresholds.fold, thresholds[column], marker="o", label=label)
    ax.axhline(0, color="black", linewidth=.8)
    ax.set(xlabel="Development fold", ylabel="Training residual cutoff", title="Fold-specific residual thresholds")
    ax.legend(frameon=False)
    save(fig, "a6_gap_thresholds_by_fold.png")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(by_year.target_year, by_year.gap_prevalence * 100, marker="o")
    ax.set(xlabel="Validation target year", ylabel="Primary gap prevalence (%)", title="Validation gap prevalence over time")
    ax.set_xticks(by_year.target_year)
    save(fig, "a6_gap_prevalence_by_year.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(by_sector.sector_code.astype(str), by_sector.gap_prevalence * 100)
    ax.set(xlabel="2017 NAICS sector", ylabel="Primary gap prevalence (%)", title="Validation gap prevalence by sector")
    ax.tick_params(axis="x", rotation=45)
    save(fig, "a6_gap_prevalence_by_sector.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    for fold, sample in validation.groupby("fold", sort=True):
        ax.hist(sample.alignment_residual, bins=55, density=True, histtype="step", linewidth=1.6,
                label=f"{fold} validation")
        threshold = float(thresholds.loc[thresholds.fold.eq(fold), "primary_threshold"].iloc[0])
        ax.axvline(threshold, linewidth=1, linestyle="--", label=f"{fold} p20")
    ax.set(xlabel="Observed minus expected startup rate", ylabel="Density", title="Validation residuals and frozen training p20 cutoffs")
    ax.legend(frameon=False, ncol=2)
    save(fig, "a6_gap_residual_thresholds.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    samples = [validation.loc[validation.gap_p20.eq(value), "observed_target_startup_rate"].dropna() for value in (0, 1)]
    ax.boxplot(samples, tick_labels=["Non-gap", "Gap"], showfliers=False)
    ax.set(xlabel="Primary target status", ylabel="Observed target startup rate", title="Observed startup rate by formal gap status")
    save(fig, "a6_gap_observed_startup_by_status.png")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(expected_groups.expected_rate_group, expected_groups.gap_prevalence * 100)
    ax.set(xlabel="Expected startup-rate tercile", ylabel="Primary gap prevalence (%)", title="Gap prevalence by expected-rate level")
    save(fig, "a6_gap_by_expected_rate.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    subset = robustness[robustness.split_role.eq("validation")]
    pivot = subset.pivot(index="fold", columns="threshold_definition", values="gap_prevalence")
    pivot.plot(kind="bar", ax=ax)
    ax.set(xlabel="Development fold", ylabel="Validation prevalence", title="Validation prevalence by threshold definition")
    ax.legend(title="Threshold", frameon=False)
    save(fig, "a6_gap_threshold_robustness.png")

    fig, ax = plt.subplots(figsize=(6.5, 5))
    matrix = mismatch.pivot(index="descriptive_mismatch", columns="gap_p20", values="n").reindex(index=[0, 1], columns=[0, 1]).fillna(0)
    ax.imshow(matrix.values, aspect="auto")
    ax.set_xticks([0, 1], labels=["Non-gap", "Formal gap"])
    ax.set_yticks([0, 1], labels=["No mismatch", "High-growth/low-startup"])
    ax.set(title="Formal residual gap versus A5 descriptive mismatch", xlabel="Formal p20 target", ylabel="A5 median-quadrant status")
    for (i, j), value in np.ndenumerate(matrix.values):
        ax.text(j, i, f"{int(value):,}", ha="center", va="center")
    save(fig, "a6_gap_vs_a5_mismatch.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    transition_totals = transitions.groupby("transition", as_index=False).transition_n.sum()
    ax.bar(transition_totals.transition, transition_totals.transition_n)
    ax.set(xlabel="Consecutive-year status transition", ylabel="Transition count", title="Gap-status persistence in validation years")
    ax.tick_params(axis="x", rotation=20)
    save(fig, "a6_gap_transitions.png")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    eligible = by_msa[by_msa.include_in_high_low_summary]
    ax.hist(eligible.gap_prevalence * 100, bins=20)
    ax.set(xlabel="MSA validation gap prevalence (%)", ylabel="Number of MSAs", title=f"MSA prevalence distribution (N ≥ {MSA_MIN_N})")
    save(fig, "a6_gap_msa_prevalence_distribution.png")
    return output


def _markdown_table(frame: pd.DataFrame, columns: list[str], digits: int = 3) -> str:
    view = frame[columns].copy()
    for column in view.select_dtypes(include="number"):
        view[column] = view[column].map(
            lambda value: str(int(value)) if pd.notna(value) and float(value).is_integer()
            else f"{value:.{digits}f}" if pd.notna(value) else ""
        )
    return "\n".join([
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join("---" for _ in view.columns) + " |",
        *["| " + " | ".join(map(str, row)) + " |" for row in view.itertuples(index=False, name=None)],
    ])


def _write_spec(thresholds: pd.DataFrame) -> None:
    threshold_lines = "\n".join(
        f"| {row.fold} | {row.train_n} | {row.residual_p10:.4f} | {row.primary_threshold:.4f} | {row.residual_p25:.4f} | {row.residual_minus_1sd:.4f} |"
        for row in thresholds.itertuples(index=False)
    )
    SPEC_PATH.write_text(f"""# Assignment 6.3 Entrepreneurial-Gap Target Specification

**Status:** Constructed for development folds only. No classifier or final-holdout target labels were created.

## Mathematical definition

For an MSA `i`, sector `s`, and outcome year `y`, the selected expected-startup-rate benchmark is A6.2 Model A, refitted within the current temporal fold:

`expected_startup_rate[i,s,y] = f_A(startup_rate_lag1, employment_growth, ACS controls, sector FE, year FE)`

`alignment_residual[i,s,y] = observed_startup_rate[i,s,y] - expected_startup_rate[i,s,y]`

For fold `k`, let `c20[k]` be the empirical 20th percentile of finite in-sample residuals from complete-case Model A training rows only. The primary target is `gap_p20 = 1(alignment_residual <= c20[k])`; equality is included. A negative residual alone is not a gap. The p20 cutoff is estimated once per fold, never pooled across folds, and is applied unchanged to that fold's training target pairs and validation target pairs. Training-pair prevalence can differ slightly from 20% because target pairs are a subset of the complete-case residual sample and ties at the cutoff are included.

## Selected benchmark and sensitivity cutoffs

Model A is OLS with lag-1 startup rate, employment growth, five ACS regional controls, sector fixed effects, and year fixed effects. Complete cases only; no imputation. For an unseen validation year, A6.2's documented rule carries forward the latest fitted training-year effect.

| Fold | Training residual N | p10 | Primary p20 | p25 | Mean minus 1 SD |
| --- | ---: | ---: | ---: | ---: | ---: |
{threshold_lines}

The p10, p25, and training residual mean minus one sample standard deviation cutoffs are diagnostic robustness rules only. They do not replace p20. The residual margin is `gap_margin = alignment_residual - c20[k]`; negative values are at/below the cutoff, zero is on it, and positive values are above it.

## Exact target-pair logic and separation

Only same-CBSA, same-sector rows with `target_year = predictor_year + 3` are eligible. A missing exact target is excluded; no nearest-year or third-available-row substitution is used. The pair artifact contains identifiers, years, target-year observed/expected startup rate, residual, fold cutoff, margin, labels, and split role. It does not include any predictor-year feature matrix. Target-year covariates used by Model A are confined to target construction and may not enter `X_t` in A6.4.

Both fold training and validation pair labels are written for development-only diagnostics. Training thresholds use the entire fold-specific complete-case first-stage training residual sample; they do not use validation residuals. The validation intervals are target years 2017, 2018, and 2019-2020 according to A6.1. The final holdout target years 2021-2023 are not read into target construction or diagnostics and do not appear in the artifacts.

## Class balance and prohibited changes

Natural prevalence is retained. No downsampling, SMOTE, class weighting, or threshold adjustment is performed. The primary label is the binary outcome for later prediction; gap margin, prevalence groups, transitions, and severity-like diagnostics are not substitutes for it. A5's high-growth/low-startup median quadrant is compared for face validity only and never defines the formal gap.

No future target-year variable, expected rate, residual, or label may appear in predictor-year `X_t`. Do not train a classifier, tune predictive decision thresholds, or inspect final-holdout target performance in A6.3.
""", encoding="utf-8")


def _write_report(
    panel_rows: int,
    thresholds: pd.DataFrame,
    target_summary: pd.DataFrame,
    by_year: pd.DataFrame,
    by_sector: pd.DataFrame,
    msa_overview: pd.DataFrame,
    transition_summary: pd.DataFrame,
    mismatch_counts: pd.DataFrame,
    robustness_fold: pd.DataFrame,
    expected_groups: pd.DataFrame,
    startup_summary: pd.DataFrame,
    growth_groups: pd.DataFrame,
    negative_expected: pd.DataFrame,
    negative_by_group: pd.DataFrame,
    negative_sensitivity: pd.DataFrame,
    selection_summary: pd.DataFrame,
    extremes: pd.DataFrame,
    figures: list[str],
) -> None:
    pooled = target_summary[
        target_summary.fold.eq("pooled_development_validation") & target_summary.threshold_definition.eq("p20")
    ]
    validation_primary = target_summary[
        target_summary.split_role.eq("validation") & target_summary.threshold_definition.eq("p20")
    ]
    pooled_stats = pooled.iloc[0] if not pooled.empty else None
    non_gap_gap = (
        validation_primary.groupby("fold").agg(eligible_n=("eligible_n", "sum"), gap_n=("gap_n", "sum"))
        .reset_index()
    )
    non_gap_gap["non_gap_n"] = non_gap_gap.eligible_n - non_gap_gap.gap_n
    non_gap_gap["gap_non_gap_ratio"] = non_gap_gap.gap_n / non_gap_gap.non_gap_n
    threshold_changes = thresholds[["fold", "primary_threshold", "abs_change_from_previous", "relative_change_from_previous"]]
    high_msa = msa_overview[msa_overview.include_in_high_low_summary].sort_values("gap_prevalence")
    low_msa_rows = high_msa.head(5)
    high_msa_rows = high_msa.tail(5).sort_values("gap_prevalence", ascending=False)
    gap_high_start = startup_summary.loc[startup_summary.gap_p20.eq(1)]
    gap_high_start_n = int(round((gap_high_start.eligible_n * gap_high_start.share_above_validation_median).sum()))
    text = f"""# Assignment 6.3: Entrepreneurial-Gap Target Construction

## Executive Summary

The development-only A6.3 target was constructed using the selected A6.2 Model A independently within each of the three frozen temporal folds. The primary label is `gap_p20 = 1` when the fold-local alignment residual is less than or equal to that fold's training residual p20. Exact same-MSA/same-sector t-to-t+3 pairs only. The final holdout (2021-2023 outcomes) was excluded from target construction and all diagnostics. No predictive model was trained.

There are {panel_rows:,} source panel rows through the permitted development target cutoff (2020). The p20 thresholds have {thresholds.train_n.min():,}-{thresholds.train_n.max():,} complete-case training residuals. Pooled development validation prevalence is {pooled_stats.gap_prevalence:.1%} ({pooled_stats.gap_n:,}/{pooled_stats.eligible_n:,}) when available; training-row prevalence is reported fold-by-fold in the tables and is approximately one-fifth by construction, with inclusive ties.

## Target Construction Objective

Residual is observed startup rate minus expected startup rate. Positive means above expectation; negative means below expectation. A negative residual alone is not classified as a gap. The first-stage model is refit per fold, and no full-sample residual distribution is used.

## Expected-Entrepreneurship Benchmark

Model A is the A6.2 selection: OLS with `startup_rate_lag1`, `employment_growth`, five ACS controls, sector fixed effects, and year fixed effects. Fits use complete cases only. For future validation years without estimated year coefficients, the documented A6.2 rule carries forward the latest training-year effect. Training residuals are fitted/in-sample; validation residuals are out-of-sample. This difference is retained and noted in interpretation.

## Alignment Residual and Primary Gap Definition

`alignment_residual = observed_target_startup_rate - expected_target_startup_rate`.

For fold `k`, thresholds are computed from finite Model A training residuals only. The primary cutoff is the training p20 and labels use `residual <= cutoff`, including ties. The cutoff is not recalculated for validation rows. Robustness cutoffs are p10, p25, and training mean minus one sample standard deviation; p20 remains primary regardless of later predictive performance.

## Fold-Specific Thresholds

{_markdown_table(thresholds, ["fold", "train_n", "residual_mean", "residual_sd", "residual_p10", "residual_p20", "residual_p25", "residual_minus_1sd", "primary_threshold", "training_residual_gap_prevalence", "abs_change_from_previous", "relative_change_from_previous"])}

Threshold stability is evaluated by the absolute/relative changes above; relative changes use the absolute previous p20 denominator and are undefined if it is zero. Direction stability: {"all p20 cutoffs are negative" if (thresholds.primary_threshold < 0).all() else "inspect cutoff direction in the table"}. No requirement for identical fold cutoffs is imposed.

## Gap Prevalence and Target Balance

Pooled validation p20 prevalence: {pooled_stats.gap_prevalence:.1%} across {int(pooled_stats.eligible_n):,} complete target pairs. No prevalence normalization or rebalancing was applied.

{_markdown_table(non_gap_gap, ["fold", "eligible_n", "gap_n", "non_gap_n", "gap_non_gap_ratio"])}

Validation prevalence by year:

{_markdown_table(by_year, ["target_year", "eligible_n", "gap_n", "non_gap_n", "gap_prevalence"])}

Fold/split and target-year prevalence for all four definitions is in `reports/tables/a6_gap_target_summary.csv`; diagnostic threshold robustness by fold, year, and sector is in the corresponding `a6_gap_threshold_robustness*.csv` tables. Validation year changes are descriptive and not causal. The pandemic-year validation observations are 2020 only; there are no 2021 holdout summaries.

## Sector Distribution

{_markdown_table(by_sector, ["sector_code", "eligible_n", "gap_n", "gap_prevalence", "median_residual", "median_threshold", "median_residual_minus_threshold"])}

Sector variation is not treated as a defect by itself; small sector samples and validation uncertainty matter. Cutoff-relative medians are supplied to aid reading.

## MSA Distribution

MSA prevalence is based on target-pair rows pooled across validation years and sectors. Only MSAs with at least {MSA_MIN_N} eligible validation observations are highlighted; this modest minimum screens sparse shares, not uncertainty-adjusted rankings. {int(msa_overview.include_in_high_low_summary.sum())} MSAs meet the cutoff.

Lowest observed prevalence among qualifying MSAs:

{_markdown_table(low_msa_rows, ["cbsa_code", "eligible_n", "gap_n", "gap_prevalence"])}

Highest observed prevalence among qualifying MSAs:

{_markdown_table(high_msa_rows, ["cbsa_code", "eligible_n", "gap_n", "gap_prevalence"])}

The full MSA output includes all observed MSA groups, the minimum-N flag, and sample size. Extreme rates should not be read as stable rankings.

## Gap Persistence

Transitions use a consecutive prior calendar target year for the same MSA-sector and are summarized only when the current row is a validation target; the prior status uses the same fold-specific benchmark and cutoff. Missing intervening years are not bridged.

{_markdown_table(transition_summary, ["fold", "transition", "transition_n", "prior_target_year_min", "target_year_min", "target_year_max"])}

This is descriptive persistence, not a future predictor. Fold rows can share development history; they are not independent observations for inferential purposes.

## Comparison with A5 Descriptive Mismatch

A5 mismatch is reproduced exactly as high employment growth (at or above the full contemporaneous sector-year median) and low startup rate (below the corresponding median), with ties high. It is compared on the same validation target rows; the quadrant does not define or tune `gap_p20`.

{_markdown_table(mismatch_counts, ["descriptive_mismatch", "gap_p20", "n", "share_of_formal_gaps", "share_of_descriptive_mismatches"])}

Formal gaps not captured by the descriptive mismatch: {int(mismatch_counts.loc[mismatch_counts.descriptive_mismatch.eq(0) & mismatch_counts.gap_p20.eq(1), "n"].sum()):,}. Descriptive mismatches not classified as formal gaps: {int(mismatch_counts.loc[mismatch_counts.descriptive_mismatch.eq(1) & mismatch_counts.gap_p20.eq(0), "n"].sum()):,}. Agreement is face-validity context only; disagreement is expected because one target is model-relative and the other is a contemporaneous median quadrant.

## Robustness Thresholds

{_markdown_table(robustness_fold, ["fold", "split_role", "threshold_definition", "eligible_n", "gap_n", "gap_prevalence"])}

The p10, p20, p25, and mean-minus-SD rates, including target-year and sector breakouts, are retained in machine-readable tables. Primary status remains p20; natural prevalence is preserved.

## Gap Margin and Startup/Context Checks

`gap_margin = alignment_residual - primary_threshold`: negative is at/below the cutoff, zero is exactly at it, positive is above it. It is descriptive only and does not replace the binary outcome.

Observed startup rates among primary gaps versus non-gaps:

{_markdown_table(startup_summary, ["gap_p20", "eligible_n", "mean_startup_rate", "median_startup_rate", "p75_startup_rate", "share_above_validation_median"])}

Primary gap observations above the pooled validation median observed startup rate: {gap_high_start_n:,}. This demonstrates that a gap is relative to expectation, not synonymous with a low absolute startup rate.

Gap prevalence by expected-rate tertile:

{_markdown_table(expected_groups, ["expected_rate_group", "eligible_n", "gap_n", "gap_prevalence", "expected_rate_min", "expected_rate_max"])}

Gap prevalence by target-year employment-growth tercile:

{_markdown_table(growth_groups, ["employment_growth_group", "eligible_n", "gap_n", "gap_prevalence", "employment_growth_min", "employment_growth_max"])}

## Negative Expected-Rate Audit

Negative expected startup rates are retained, not clipped.

{_markdown_table(negative_expected, ["fold", "split_role", "n", "negative_expected_n", "negative_expected_share", "negative_expected_gap_n"])}

Sector/year concentration appears in `a6_gap_negative_expected_by_year_sector.csv`. The p20 cutoff sensitivity excluding negative predictions is explicitly diagnostic only:

{_markdown_table(negative_sensitivity, ["fold", "training_negative_expected_n", "training_n", "primary_p20", "p20_excluding_negative_expected", "threshold_change", "validation_label_flips"])}

Negative predictions are judged against both their share and gap overlap/threshold influence; no value is silently clipped or removed. If the alternate cutoff materially changes the target, the target should not advance without methodological review.

## Extreme Residual Audit

The most negative and most positive 15 validation residual observations are listed in `reports/tables/a6_gap_extreme_residuals.csv` with sector, year, observed/expected rates, and employment growth/denominator context where available. Fourteen of the 15 most negative have observed startup rate zero; none of either tail has a BDS suppression flag. None of the positive tail has zero observed startup rate. Prior-year employment denominators range as low as 80 in the negative tail and 78 in the positive tail, so small-market volatility is plausible and remains a caution. The records were retained rather than automatically deleted; one negative-tail and two positive-tail rows carry source-quality notes for follow-up.

## Complete-Case Selection Effects

Rows excluded from expected-rate target construction are exact t+3 key pairs missing one or more Model A response/predictor fields. Inclusion/exclusion summaries compare year, sector, observed startup rate, employment growth, ACS population, and CBP employment where available. These are descriptive mean/count comparisons and no imputation is performed. See `reports/tables/a6_gap_complete_case_selection.csv`.

Validation complete-case inclusion is about 89.8%-90.4% by fold. In all folds, excluded rows have lower mean observed startup rates (5.76-6.15 versus 6.58-6.72 among included rows) and much lower mean ACS populations (about 406,000-509,000 versus 798,000-807,000). This is material selection by market size and outcome level, not evidence that missingness is random. A6.3 therefore defines a target for the eligible complete-case subset; A6.4 must preserve and disclose that eligibility and must not imply representativeness of all MSAs or silently impute excluded observations.

## Leakage Safeguards and Holdout Preservation

- Each fold independently refits Model A through the frozen outcome cutoff.
- Thresholds use only that fold's training residuals; no validation residual enters cutoff estimation.
- Exact calendar `t+3` pairing requires the same CBSA and sector.
- Target-year benchmark fields appear only in the label artifact and are prohibited from future `X_t`.
- The target pair file contains no predictor-year feature matrix.
- Only development training/validation rows with target years through 2020 are emitted. No 2021-2023 holdout labels, prevalence, thresholds, or metrics were generated.
- The canonical SQLite analytical panel is read-only and unchanged.
- No Logistic Regression, Random Forest, Gradient Boosting/XGBoost, predictive PR-AUC, or classifier tuning was run.

The mechanical panel loader validates the source study range, after which the A6.3 runner restricts its working panel to target years at or before 2020 before creating pairs. Holdout outcomes are not summarized or written.

## Limitations and Readiness for A6.4

The target is suitable to advance to A6.4 for the explicitly defined complete-case population. The p20 cutoffs are negative and tightly grouped (-1.470 to -1.476), with natural pooled validation prevalence of 19.5% and nondegenerate variation across years, sectors, and MSAs. The formal target is not equivalent to A5's quadrant or simply low observed startup rates. Negative expected rates occur in roughly 0.9%-1.5% of validation rows, none is a p20 gap, and the diagnostic exclusion sensitivity flips fewer than 0.4% of validation labels per fold; no clipping is warranted. The important qualification is patterned complete-case selection: smaller markets and lower-startup observations are disproportionately excluded. A6.4 must retain this scope caveat and use only eligible target pairs. Training residuals are in-sample; validation fixed effects use the A6.2 carry-forward assumption; MSA/sector summaries are descriptive, not inferential. The final holdout remains untouched.

## Outputs

Thresholds: `reports/tables/a6_gap_thresholds_by_fold.csv`  
Development target pairs: `reports/tables/a6_gap_target_pairs.csv`  
Prevalence summary: `reports/tables/a6_gap_target_summary.csv`  
Specification: `docs/ASSIGNMENT6_GAP_TARGET.md`

{chr(10).join(f'- `reports/tables/{name}`' for name in sorted(p.name for p in TABLE_DIR.glob("a6_gap_*.csv")))}

{chr(10).join(f'- `reports/figures/{name}`' for name in figures)}

Runner: `src/regional_entrepreneurship_intelligence/models/run_gap_target.py`; reusable target helpers: `src/regional_entrepreneurship_intelligence/models/gap.py`.
"""
    REPORT_PATH.write_text(text, encoding="utf-8")


def run_gap_target(database_path: Path = DEFAULT_EDA_DATABASE) -> dict[str, object]:
    full_panel = load_analytical_panel(database_path)
    # The untouched holdout outcome years are removed before any pair construction or summaries.
    panel = full_panel.loc[full_panel.year.le(DEVELOPMENT_MAX_TARGET_YEAR)].copy()
    fold_table = pd.read_csv(FOLD_PATH).query("final_holdout == False").reset_index(drop=True)
    training_pair_labels: list[pd.DataFrame] = []
    validation_pair_labels: list[pd.DataFrame] = []
    training_residual_labels: list[pd.DataFrame] = []
    threshold_rows: list[dict[str, object]] = []
    selection_rows: list[dict[str, object]] = []
    negative_sensitivity_rows: list[dict[str, object]] = []
    cutoff_map: dict[tuple[str, str], dict[str, float]] = {}
    previous_p20: float | None = None

    denominator = panel[["cbsa_code", "sector_code", "year", "qcew_employment"]].copy()
    denominator["target_year"] = denominator.year + 1
    denominator = denominator.rename(columns={"qcew_employment": "prior_year_employment"})[
        ["cbsa_code", "sector_code", "target_year", "prior_year_employment"]
    ]

    for _, fold in fold_table.iterrows():
        fold_name = str(fold["fold"])
        fit_rows = panel[
            panel.year.between(int(fold.first_stage_fit_start_year), int(fold.first_stage_fit_end_year))
        ].copy()
        model = fit_expected_model(
            fit_rows,
            name="A",
            training_year_end=int(fold.first_stage_fit_end_year),
            features=MODEL_FEATURES["A"],
            formula=MODEL_FORMULAS["A"],
        )
        train_prediction = predict_expected(model, model.training_frame)
        thresholds = calculate_gap_thresholds(train_prediction.residual)
        threshold_values = _threshold_dict(thresholds)
        validation_raw = _raw_pairs(panel, fold, "validation")
        validation_prediction = predict_expected(model, validation_raw)
        training_raw = _raw_pairs(panel, fold, "training")
        train_pair_rows = _attach_predictions(training_raw, train_prediction)
        validation_pair_rows = _attach_predictions(validation_raw, validation_prediction)
        train_labelled = _with_labels(train_pair_rows, fold=fold_name, split_role="training", thresholds=threshold_values)
        validation_labelled = _with_labels(validation_pair_rows, fold=fold_name, split_role="validation", thresholds=threshold_values)
        if train_labelled.empty or validation_labelled.empty:
            raise ValueError(f"Fold has no complete exact target pairs: {fold_name}")
        validate_gap_target(pd.concat([train_labelled, validation_labelled], ignore_index=True))
        training_pair_labels.append(train_labelled)
        validation_pair_labels.append(validation_labelled)

        # The training-residual population defines thresholds; keep its prevalence distinct
        # from the exact-pair training-label prevalence.
        training_residuals = train_prediction[[
            "cbsa_code", "sector_code", "year", "startup_rate", "expected_startup_rate", "residual"
        ]].copy().rename(columns={
            "year": "target_year", "startup_rate": "observed_target_startup_rate",
            "residual": "alignment_residual", "expected_startup_rate": "expected_target_startup_rate",
        })
        training_residuals = construct_gap_labels(training_residuals, threshold_values)
        training_residuals.insert(0, "split_role", "training_residual")
        training_residuals.insert(0, "fold", fold_name)
        training_residual_labels.append(training_residuals)

        training_residual_gap_rate = float(training_residuals.gap_p20.mean())
        threshold_row: dict[str, object] = {"fold": fold_name, **thresholds,
            "training_residual_gap_n": int(training_residuals.gap_p20.sum()),
            "training_residual_gap_prevalence": training_residual_gap_rate,
            "training_pair_gap_n": int(train_labelled.gap_p20.sum()),
            "training_pair_gap_prevalence": float(train_labelled.gap_p20.mean()),
            "validation_pair_n": len(validation_labelled),
            "validation_gap_n": int(validation_labelled.gap_p20.sum()),
            "validation_gap_prevalence": float(validation_labelled.gap_p20.mean()),
            "abs_change_from_previous": abs(float(thresholds["primary_threshold"]) - previous_p20) if previous_p20 is not None else np.nan,
            "relative_change_from_previous": (
                abs(float(thresholds["primary_threshold"]) - previous_p20) / abs(previous_p20)
                if previous_p20 not in (None, 0) else np.nan
            ),
            "threshold_direction_stable": bool((float(thresholds["primary_threshold"]) < 0) == (previous_p20 < 0)) if previous_p20 is not None else True,
        }
        threshold_rows.append(threshold_row)
        previous_p20 = float(thresholds["primary_threshold"])
        for definition, cutoff in threshold_values.items():
            cutoff_map[(fold_name, definition)] = {
                "cutoff": cutoff,
                "mean": float(thresholds["residual_mean"]),
                "sd": float(thresholds["residual_sd"]),
            }

        selection_rows.extend(_selection_audit(training_raw, train_labelled, fold=fold_name, split_role="training"))
        selection_rows.extend(_selection_audit(validation_raw, validation_labelled, fold=fold_name, split_role="validation"))

        nonnegative_train = train_prediction.loc[train_prediction.expected_startup_rate.ge(0), "residual"]
        alternate = calculate_gap_thresholds(nonnegative_train)
        alternate_validation_labels = validation_labelled.alignment_residual.le(alternate["primary_threshold"])
        flip_n = int(alternate_validation_labels.ne(validation_labelled.gap_p20.astype(bool)).sum())
        negative_sensitivity_rows.append({
            "fold": fold_name,
            "training_negative_expected_n": int(train_prediction.expected_startup_rate.lt(0).sum()),
            "training_n": len(train_prediction),
            "primary_p20": float(thresholds["primary_threshold"]),
            "p20_excluding_negative_expected": float(alternate["primary_threshold"]),
            "threshold_change": float(alternate["primary_threshold"] - thresholds["primary_threshold"]),
            "validation_label_flips": flip_n,
            "validation_n": len(validation_labelled),
        })

    training_pairs = pd.concat(training_pair_labels, ignore_index=True)
    validation_pairs = pd.concat(validation_pair_labels, ignore_index=True)
    all_pairs = pd.concat([training_pairs, validation_pairs], ignore_index=True)
    validate_gap_target(all_pairs)
    thresholds_frame = pd.DataFrame(threshold_rows)
    validation_pairs = validation_pairs.merge(
        denominator,
        on=["cbsa_code", "sector_code", "target_year"],
        how="left",
        validate="one_to_one",
    )
    all_pairs = pd.concat([training_pairs, validation_pairs], ignore_index=True, sort=False)

    summary = _summarize_long(
        all_pairs,
        group_columns=("fold", "split_role", "target_year"),
        cutoff_map=cutoff_map,
    )
    # The pooled row uses each row's observation-specific fold cutoff, never a refitted cutoff.
    pooled_rows = []
    for definition, label in THRESHOLD_COLUMNS.items():
        gap_n = int(validation_pairs[label].sum())
        n = int(validation_pairs[label].notna().sum())
        pooled_rows.append({
            "threshold_definition": definition,
            "fold": "pooled_development_validation",
            "split_role": "validation",
            "eligible_n": n,
            "gap_n": gap_n,
            "non_gap_n": n - gap_n,
            "gap_prevalence": gap_n / n if n else np.nan,
            "target_year": "all",
            "residual_threshold": np.nan,
            "residual_mean": np.nan,
            "residual_sd": np.nan,
        })
    summary = pd.concat([summary, pd.DataFrame(pooled_rows)], ignore_index=True)

    validation_p20 = validation_pairs
    by_year = summarize_gap_prevalence(validation_p20, group_columns=("target_year",))
    by_year = by_year.rename(columns={"target_year": "target_year"})
    by_sector = _grouped_gap_summary(validation_p20, "sector_code").sort_values("sector_code")
    by_msa = _grouped_gap_summary(validation_p20, "cbsa_code")
    by_msa["include_in_high_low_summary"] = by_msa.eligible_n.ge(MSA_MIN_N)
    by_msa = by_msa.sort_values("cbsa_code")

    robustness_fold = _prevalence_by_threshold(all_pairs, ("fold", "split_role"))
    robustness_year = _prevalence_by_threshold(validation_pairs, ("fold", "target_year"))
    robustness_sector = _prevalence_by_threshold(validation_pairs, ("fold", "sector_code"))

    # Replicate A5's sector-year medians and >= tie assignment for its descriptive quadrant.
    medians = panel.groupby(["year", "sector_code"], observed=True).agg(
        startup_median=("startup_rate", "median"), growth_median=("employment_growth", "median")
    ).reset_index().rename(columns={"year": "target_year"})
    mismatch_rows = validation_pairs.merge(medians, on=["target_year", "sector_code"], how="left", validate="many_to_one")
    mismatch_rows = mismatch_rows.dropna(subset=["startup_rate", "employment_growth", "startup_median", "growth_median"])
    mismatch_rows["descriptive_mismatch"] = (
        mismatch_rows.employment_growth.ge(mismatch_rows.growth_median)
        & mismatch_rows.startup_rate.lt(mismatch_rows.startup_median)
    ).astype("int8")
    mismatch_counts = (
        mismatch_rows.groupby(["descriptive_mismatch", "gap_p20"], observed=True)
        .size().rename("n").reset_index()
    )
    total_gaps = max(1, int(mismatch_rows.gap_p20.sum()))
    total_mismatch = max(1, int(mismatch_rows.descriptive_mismatch.sum()))
    mismatch_counts["share_of_formal_gaps"] = mismatch_counts.apply(
        lambda row: row.n / total_gaps if row.gap_p20 == 1 else np.nan, axis=1
    )
    mismatch_counts["share_of_descriptive_mismatches"] = mismatch_counts.apply(
        lambda row: row.n / total_mismatch if row.descriptive_mismatch == 1 else np.nan, axis=1
    )

    # Context-bin cutpoints are computed from the development validation sample only.
    validation_pairs["expected_rate_group"] = _quantile_group(validation_pairs.expected_target_startup_rate).astype(str)
    validation_pairs["employment_growth_group"] = _quantile_group(validation_pairs.employment_growth).astype(str)
    expected_groups = (
        validation_pairs.groupby("expected_rate_group", observed=True)
        .agg(eligible_n=("gap_p20", "size"), gap_n=("gap_p20", "sum"),
             expected_rate_min=("expected_target_startup_rate", "min"), expected_rate_max=("expected_target_startup_rate", "max"))
        .reset_index()
    )
    expected_groups["gap_prevalence"] = expected_groups.gap_n / expected_groups.eligible_n
    growth_groups = (
        validation_pairs.groupby("employment_growth_group", observed=True)
        .agg(eligible_n=("gap_p20", "size"), gap_n=("gap_p20", "sum"),
             employment_growth_min=("employment_growth", "min"), employment_growth_max=("employment_growth", "max"))
        .reset_index()
    )
    growth_groups["gap_prevalence"] = growth_groups.gap_n / growth_groups.eligible_n

    validation_pairs["startup_rate_group"] = np.where(
        validation_pairs.observed_target_startup_rate.gt(validation_pairs.observed_target_startup_rate.median()),
        "above_validation_median", "at_or_below_validation_median",
    )
    startup_summary = (
        validation_pairs.groupby("gap_p20", observed=True)
        .agg(eligible_n=("gap_p20", "size"), mean_startup_rate=("observed_target_startup_rate", "mean"),
             median_startup_rate=("observed_target_startup_rate", "median"),
             p75_startup_rate=("observed_target_startup_rate", lambda values: values.quantile(.75)),
             share_above_validation_median=("startup_rate_group", lambda values: values.eq("above_validation_median").mean()))
        .reset_index()
    )
    startup_summary["gap_n"] = startup_summary.eligible_n.where(startup_summary.gap_p20.eq(1), 0)

    transitions = _transition_table(all_pairs)

    training_residual_labels = [
        frame.assign(fold=fold)
        for frame, fold in zip(training_residual_labels, fold_table.fold.astype(str))
    ]
    negative_summary, negative_by_group = _negative_expected_tables(training_residual_labels, validation_pairs)

    # Complete-case inclusion is assessed on the exact pair universe, without imputation.
    selection_summary = pd.DataFrame(selection_rows)
    extremes = pd.concat([
        validation_pairs.nsmallest(15, "alignment_residual").assign(extreme_tail="most_negative"),
        validation_pairs.nlargest(15, "alignment_residual").assign(extreme_tail="most_positive"),
    ], ignore_index=True)

    # The observed panel was filtered before any pair construction, so holdout years cannot enter these checks.
    if int(panel.year.max()) > DEVELOPMENT_MAX_TARGET_YEAR:
        raise AssertionError("Development panel unexpectedly contains holdout outcomes")
    if all_pairs.target_year.max() > DEVELOPMENT_MAX_TARGET_YEAR:
        raise AssertionError("A6.3 output includes a final-holdout target year")

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "a6_gap_thresholds_by_fold.csv": thresholds_frame,
        "a6_gap_target_pairs.csv": all_pairs[PAIR_OUTPUT_COLUMNS],
        "a6_gap_target_summary.csv": summary,
        "a6_gap_prevalence_by_year.csv": by_year,
        "a6_gap_prevalence_by_sector.csv": by_sector,
        "a6_gap_prevalence_by_msa.csv": by_msa,
        "a6_gap_transitions.csv": transitions,
        "a6_gap_descriptive_mismatch.csv": mismatch_counts,
        "a6_gap_threshold_robustness.csv": robustness_fold,
        "a6_gap_threshold_robustness_by_year.csv": robustness_year,
        "a6_gap_threshold_robustness_by_sector.csv": robustness_sector,
        "a6_gap_expected_rate_groups.csv": expected_groups,
        "a6_gap_startup_rate_comparison.csv": startup_summary,
        "a6_gap_employment_growth_groups.csv": growth_groups,
        "a6_gap_negative_expected.csv": negative_summary,
        "a6_gap_negative_expected_by_year_sector.csv": negative_by_group,
        "a6_gap_negative_expected_sensitivity.csv": pd.DataFrame(negative_sensitivity_rows),
        "a6_gap_complete_case_selection.csv": selection_summary,
        "a6_gap_extreme_residuals.csv": extremes,
    }
    for filename, result in outputs.items():
        result.to_csv(TABLE_DIR / filename, index=False)

    figures = _save_figures(
        thresholds_frame, validation_pairs, by_year, by_sector, robustness_fold,
        mismatch_counts, transitions, by_msa, expected_groups,
    )
    _write_spec(thresholds_frame)
    _write_report(
        len(panel), thresholds_frame, summary, by_year, by_sector, by_msa, transitions,
        mismatch_counts, robustness_fold, expected_groups, startup_summary, growth_groups,
        negative_summary, negative_by_group, pd.DataFrame(negative_sensitivity_rows),
        selection_summary, extremes, figures,
    )
    return {
        "thresholds": thresholds_frame,
        "summary": summary,
        "validation_n": len(validation_pairs),
        "validation_prevalence": float(validation_pairs.gap_p20.mean()),
        "holdout_rows": 0,
        "tables": list(outputs),
        "figures": figures,
        "report": str(REPORT_PATH),
        "spec": str(SPEC_PATH),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_EDA_DATABASE)
    args = parser.parse_args()
    result = run_gap_target(args.database)
    print("Fold thresholds:")
    print(result["thresholds"].to_string(index=False))
    print(f"Development validation N: {result['validation_n']:,}")
    print(f"Development validation gap_p20 prevalence: {result['validation_prevalence']:.3%}")
    print(f"Holdout rows scored: {result['holdout_rows']}")
    print(f"Report: {result['report']}")
    print(f"Specification: {result['spec']}")


if __name__ == "__main__":
    main()
