"""Generate Assignment 5.2 descriptive, missingness, and diagnostic outputs."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
import os
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
    VARIABLE_GROUPS,
    load_analytical_panel,
    summarize_distribution_shape,
    summarize_economic_plausibility,
    summarize_missingness,
    summarize_missingness_by_year,
    summarize_numeric_variables,
    summarize_structural_missingness,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TABLE_DIR = PROJECT_ROOT / "reports" / "tables"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures"
REPORT_PATH = PROJECT_ROOT / "reports" / "assignment5_descriptive_missingness.md"

TIER1_MEASURES = (
    "startup_rate", "employment_growth", "acs_population_growth", "unemployment_rate",
    "educational_attainment_pct", "median_household_income",
)
TIER2_GROUPS = ("entrepreneurship", "industry_growth", "regional_control", "business_structure")
TIER2_MEASURES = tuple(
    sorted(set().union(*(VARIABLE_GROUPS[name] for name in TIER2_GROUPS)) - set(TIER1_MEASURES))
)
SUMMARY_VARIABLES = TIER1_MEASURES + TIER2_MEASURES
CORE_SHAPE_VARIABLES = (
    "startup_rate", "employment_growth", "establishment_growth", "payroll_growth",
    "wage_growth", "acs_population_growth", "median_household_income",
    "unemployment_rate", "educational_attainment_pct", "labor_force_participation_pct",
)
YEAR_MISSINGNESS_VARIABLES = (
    "startup_rate", "startup_rate_lag1", "startup_rate_lag2", "startup_rate_lag3",
    "employment_growth", "employment_growth_lag1", "employment_growth_lag2",
    "employment_growth_lag3", "establishment_growth", "establishment_growth_lag1",
    "establishment_growth_lag2", "establishment_growth_lag3", "payroll_growth",
    "payroll_growth_lag1", "wage_growth", "average_pay_growth_lag1",
    "acs_population_growth", "median_household_income", "educational_attainment_pct",
    "labor_force_participation_pct", "unemployment_rate", "cbp_employment",
    "cbp_establishments", "cbp_annual_payroll", "cbp_first_quarter_payroll",
)
CONCENTRATION_VARIABLES = (
    "startup_rate_lag1", "employment_growth", "acs_population_growth",
    "median_household_income", "cbp_employment", "cbp_establishments",
)
GROWTH_DENOMINATORS = {
    "employment_growth": "prior_year_employment",
    "establishment_growth": "prior_year_establishments",
    "payroll_growth": "prior_year_payroll",
    "wage_growth": "prior_year_average_wage",
}


def _load_denominator_context(database_path: Path, panel: pd.DataFrame) -> pd.DataFrame:
    query = """SELECT a.geography_id, a.industry_id, a.year,
                      p.employment AS prior_year_employment,
                      p.establishments AS prior_year_establishments,
                      p.payroll AS prior_year_payroll,
                      p.average_wage AS prior_year_average_wage
               FROM analytics_msa_industry_year AS a
               LEFT JOIN int_industry_growth AS p
                 ON p.geography_id = a.geography_id
                AND p.industry_id = a.industry_id
                AND p.year = a.year - 1"""
    with closing(sqlite3.connect(f"file:{database_path.resolve().as_posix()}?mode=ro", uri=True)) as con:
        history = pd.read_sql_query(query, con)
    return panel[["geography_id", "industry_id", "year", *GROWTH_DENOMINATORS]].merge(
        history, on=["geography_id", "industry_id", "year"], how="left", validate="one_to_one"
    )


def _denominator_diagnostics(context: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for growth_variable, denominator_column in GROWTH_DENOMINATORS.items():
        values = context[growth_variable]
        denominators = context[denominator_column]
        valid = values.notna() & np.isfinite(values.astype(float))
        missing_growth = values.isna()
        observed = context.loc[valid, [growth_variable, denominator_column]].copy()
        if observed.empty:
            continue
        cutoff = observed[growth_variable].abs().quantile(0.99)
        extreme = observed.loc[observed[growth_variable].abs() >= cutoff]
        positive_denominators = observed.loc[observed[denominator_column] > 0, denominator_column]
        decile = positive_denominators.quantile(0.10) if len(positive_denominators) else np.nan
        rows.append(
            {
                "growth_variable": growth_variable,
                "finite_observation_count": len(observed),
                "absolute_growth_p99": float(cutoff),
                "top_one_pct_count": len(extreme),
                "top_one_pct_missing_prior_denominator": int(extreme[denominator_column].isna().sum()),
                "prior_denominator_p10_all_positive": float(decile) if np.isfinite(decile) else np.nan,
                "top_one_pct_prior_denominator_median": float(extreme[denominator_column].median()),
                "top_one_pct_share_bottom_decile_denominator": (
                    float((extreme[denominator_column] <= decile).mean())
                    if np.isfinite(decile) and extreme[denominator_column].notna().any()
                    else np.nan
                ),
                "top_one_pct_nonpositive_prior_denominator": int((extreme[denominator_column] <= 0).sum()),
                "missing_growth_count": int(missing_growth.sum()),
                "missing_growth_prior_denominator_zero": int((missing_growth & denominators.eq(0)).sum()),
                "missing_growth_prior_denominator_negative": int((missing_growth & denominators.lt(0)).sum()),
                "missing_growth_prior_denominator_unavailable": int((missing_growth & denominators.isna()).sum()),
            }
        )
    return pd.DataFrame(rows)


def _missingness_concentration(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variable in CONCENTRATION_VARIABLES:
        for group_column, label in (("sector_code", "sector"), ("cbsa_code", "msa")):
            if group_column == "sector_code":
                groups = panel.groupby("sector_code", dropna=False)
            else:
                groups = panel.groupby(["cbsa_code", "cbsa_name"], dropna=False)
            rates = []
            for key, group in groups:
                if len(group) < 50:
                    continue
                name = key[1] if isinstance(key, tuple) else key
                missing = int(group[variable].isna().sum())
                rates.append((name, len(group), missing, missing / len(group) * 100))
            for group_value, n, missing, rate in sorted(rates, key=lambda item: item[3], reverse=True)[:5]:
                rows.append(
                    {
                        "variable": variable,
                        "grouping": label,
                        "group_value": group_value,
                        "group_n": n,
                        "missing_count": missing,
                        "missing_pct": rate,
                        "median_group_missing_pct": float(np.median([item[3] for item in rates])) if rates else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def _msa_size_missingness(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variable in CONCENTRATION_VARIABLES:
        msa = panel.groupby(["cbsa_code", "cbsa_name"], dropna=False).agg(
            mean_population=("acs_population", "mean"),
            missing_rate=(variable, lambda values: values.isna().mean()),
            panel_rows=(variable, "size"),
        )
        msa = msa.loc[msa.mean_population.notna() & (msa.panel_rows >= 50)].copy()
        if len(msa) < 6:
            continue
        msa["population_tercile"] = pd.qcut(
            msa.mean_population.rank(method="first"), q=3, labels=["lower", "middle", "upper"]
        )
        grouped = msa.groupby("population_tercile", observed=False).missing_rate.mean() * 100
        rows.append(
            {
                "variable": variable,
                "msa_count": len(msa),
                "spearman_population_missingness": msa.mean_population.corr(msa.missing_rate, method="spearman"),
                "lower_population_tercile_missing_pct": float(grouped.get("lower", np.nan)),
                "middle_population_tercile_missing_pct": float(grouped.get("middle", np.nan)),
                "upper_population_tercile_missing_pct": float(grouped.get("upper", np.nan)),
                "notes": "MSA-level descriptive check; only MSAs with observed ACS population and at least 50 panel rows",
            }
        )
    return pd.DataFrame(rows)


def _extreme_observations(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variable in CORE_SHAPE_VARIABLES:
        finite = panel.loc[panel[variable].notna() & np.isfinite(panel[variable].astype(float))]
        for tail, selected in (("lowest", finite.nsmallest(3, variable)), ("highest", finite.nlargest(3, variable))):
            for _, row in selected.iterrows():
                rows.append(
                    {
                        "variable": variable,
                        "tail": tail,
                        "value": row[variable],
                        "cbsa_code": row["cbsa_code"],
                        "cbsa_name": row["cbsa_name"],
                        "sector_code": row["sector_code"],
                        "sector_title": row["sector_title"],
                        "year": int(row["year"]),
                    }
                )
    return pd.DataFrame(rows)


def _save_figures(panel: pd.DataFrame, missingness: pd.DataFrame) -> list[str]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    saved = []
    for variable, filename, title, xlabel in (
        ("startup_rate", "a5_startup_rate_histogram.png", "Startup Rate Distribution (P01-P99 View)", "Startup rate (percent)"),
        ("employment_growth", "a5_employment_growth_histogram.png", "Employment Growth Distribution (P01-P99 View)", "Annual growth rate"),
    ):
        values = panel[variable].dropna()
        fig, ax = plt.subplots()
        ax.hist(values, bins=50)
        ax.set_xlim(values.quantile(0.01), values.quantile(0.99))
        ax.set(title=title, xlabel=xlabel, ylabel="MSA-sector-year observations")
        fig.tight_layout()
        fig.savefig(FIGURE_DIR / filename, dpi=150)
        plt.close(fig)
        saved.append(filename)

    growths = ["employment_growth", "establishment_growth", "payroll_growth", "wage_growth"]
    fig, ax = plt.subplots()
    ax.boxplot([panel[name].dropna().to_numpy() for name in growths], tick_labels=growths, showfliers=False)
    ax.set(title="Annual Growth Distributions (Fliers Hidden for Scale)", ylabel="Annual growth rate")
    ax.tick_params(axis="x", labelrotation=25)
    fig.tight_layout()
    filename = "a5_growth_boxplot.png"
    fig.savefig(FIGURE_DIR / filename, dpi=150)
    plt.close(fig)
    saved.append(filename)

    selected = missingness.loc[missingness["variable"].isin(YEAR_MISSINGNESS_VARIABLES)]
    selected = selected.sort_values("missing_pct", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.barh(selected["variable"], selected["missing_pct"])
    ax.set(title="Missingness in Core and Supporting Measures", xlabel="Missing observations (%)", ylabel="")
    fig.tight_layout()
    filename = "a5_missingness_summary.png"
    fig.savefig(FIGURE_DIR / filename, dpi=150)
    plt.close(fig)
    saved.append(filename)
    return saved


def _fmt(value: object, digits: int = 3) -> str:
    return "NA" if pd.isna(value) else f"{float(value):,.{digits}f}"


def _summary_markdown(stats: pd.DataFrame, variables: tuple[str, ...]) -> str:
    selected = stats.loc[stats["variable"].isin(variables)]
    if selected.empty:
        return "No available summary rows."
    lines = ["| Variable | N | Missing % | Mean | Median | P05 | P95 | Min | Max |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for _, row in selected.iterrows():
        lines.append(
            f"| `{row.variable}` | {int(row['count']):,} | {_fmt(row.missing_pct, 2)} | "
            f"{_fmt(row['mean'])} | {_fmt(row['median'])} | {_fmt(row.p05)} | "
            f"{_fmt(row.p95)} | {_fmt(row['min'])} | {_fmt(row['max'])} |"
        )
    return "\n".join(lines)


def _write_report(
    panel: pd.DataFrame,
    stats: pd.DataFrame,
    missing: pd.DataFrame,
    causes: pd.DataFrame,
    shapes: pd.DataFrame,
    plausibility: pd.DataFrame,
    denominators: pd.DataFrame,
    concentration: pd.DataFrame,
    msa_size: pd.DataFrame,
    extremes: pd.DataFrame,
    figure_names: list[str],
) -> None:
    def cause_total(category: str) -> int:
        return int(causes.loc[causes["cause_category"] == category, "missing_count"].sum())

    startup_shape = shapes.set_index("variable").loc["startup_rate"]
    employment_shape = shapes.set_index("variable").loc["employment_growth"]
    qcew_growth_missing = missing.loc[missing["variable"].isin(GROWTH_DENOMINATORS)].copy()
    cbp_missing = missing.loc[missing["variable"] == "cbp_employment", "missing_pct"].iloc[0]
    acs_missing = missing.loc[missing["variable"] == "median_household_income", "missing_pct"].iloc[0]
    flags = plausibility.loc[plausibility["flagged_count"] > 0]
    rate_flags = int(
        plausibility.loc[plausibility.rule == "outside_0_100", "flagged_count"].sum()
    )
    findings = "\n".join(
        f"- `{row.variable}` / `{row.rule}`: {int(row.flagged_count):,} flagged. {row.notes}."
        for _, row in flags.iterrows()
    ) or "- No values met the explicit plausibility rules in this pass."
    denominator_lines = []
    for _, row in denominators.iterrows():
        denominator_lines.append(
            f"- `{row.growth_variable}`: top 1% absolute-growth observations have median prior denominator "
            f"{_fmt(row.top_one_pct_prior_denominator_median)}; "
            f"{_fmt(row.top_one_pct_share_bottom_decile_denominator * 100, 1)}% fall at or below the full-sample "
            f"positive-denominator 10th percentile. Of {int(row.missing_growth_count):,} missing-growth rows, "
            f"{int(row.missing_growth_prior_denominator_zero):,} have a zero prior denominator, "
            f"{int(row.missing_growth_prior_denominator_negative):,} a negative denominator, and "
            f"{int(row.missing_growth_prior_denominator_unavailable):,} no matched prior denominator."
        )
    concentration_lines = []
    if not concentration.empty:
        for variable in CONCENTRATION_VARIABLES:
            rows = concentration.loc[(concentration.variable == variable) & (concentration.grouping == "sector")]
            if not rows.empty:
                top = rows.iloc[0]
                concentration_lines.append(
                    f"- `{variable}`: highest sector missingness was {top.missing_pct:.1f}% "
                    f"(sector {top.group_value}); median sector rate was {top.median_group_missing_pct:.1f}%."
                )
            msa_rows = concentration.loc[(concentration.variable == variable) & (concentration.grouping == "msa")]
            if not msa_rows.empty:
                top_msa = msa_rows.iloc[0]
                concentration_lines.append(
                    f"  Across MSAs with at least 50 panel rows, the highest observed rate was "
                    f"{top_msa.missing_pct:.1f}% (median MSA rate {top_msa.median_group_missing_pct:.1f}%)."
                )
    growth_missing_text = ", ".join(
        f"`{row.variable}` {row.missing_pct:.1f}%" for _, row in qcew_growth_missing.iterrows()
    )
    msa_size_lines = [
        f"- `{row.variable}`: Spearman rho between MSA mean population and missing share = "
        f"{_fmt(row.spearman_population_missingness)}; lower/middle/upper population-tercile missingness "
        f"was {row.lower_population_tercile_missing_pct:.1f}% / {row.middle_population_tercile_missing_pct:.1f}% / "
        f"{row.upper_population_tercile_missing_pct:.1f}% (n={int(row.msa_count)} MSAs)."
        for _, row in msa_size.iterrows()
    ]
    outlier_leaders = shapes.nlargest(1, "iqr_outlier_count").iloc[0]
    sd_leaders = shapes.nlargest(1, "three_sd_count").iloc[0]
    extreme_lines = []
    for variable in CORE_SHAPE_VARIABLES:
        rows = extremes.loc[
            (extremes.variable == variable) & extremes["tail"].isin(("lowest", "highest"))
        ]
        for tail in ("lowest", "highest"):
            selected = rows.loc[rows["tail"] == tail]
            if selected.empty:
                continue
            row = selected.iloc[0]
            extreme_lines.append(
                f"- `{variable}` {tail}: {_fmt(row.value)} in {row.cbsa_name}, sector "
                f"{row.sector_code}, {int(row.year)}."
            )
    shape_lines = [
        "| Variable | Skewness | Excess kurtosis | Zero N | Negative N | Shape notes |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for _, row in shapes.iterrows():
        shape_lines.append(
            f"| `{row.variable}` | {_fmt(row.skewness)} | {_fmt(row.excess_kurtosis)} | "
            f"{int(row.zero_count):,} | {int(row.negative_count):,} | {row.notes} |"
        )

    sections = [
        "# Assignment 5.2: Descriptive Statistics & Missingness",
        "",
        "## Scope and Data",
        "",
        f"The A5.1 read-only loader returned **{len(panel):,}** MSA-sector-year observations across "
        f"**{panel.cbsa_code.nunique():,} MSAs**, **{panel.sector_code.nunique()} sectors**, and "
        f"**{panel.year.min()}–{panel.year.max()}**. There are no duplicate panel keys. The active view has "
        f"{len(panel.columns)} fields; all remain within the documented Assignment 4 scope.",
        "",
        "This report covers overall distributions, completeness, concentration checks, and initial outlier/plausibility diagnostics. It does not analyze trends, sector-specific relationships, causal effects, predictive performance, expected entrepreneurship, or entrepreneurial-gap status.",
        "",
        "Stored growth measures are decimal rates (for example, 0.015 is 1.5%); startup rate and ACS profile percentages are expressed in percent units. Income is retained in ACS release-adjusted dollars and is not deflated to a common year.",
        "",
        "## What the Data Show",
        "",
        "### Entrepreneurship",
        "",
        _summary_markdown(stats, ("startup_rate", "firm_startups", "establishment_entry", "establishment_entry_rate", "startup_job_creation", "startup_rate_lag1", "startup_rate_lag2", "startup_rate_lag3")),
        "",
        f"Startup rate has skewness {_fmt(startup_shape.skewness)} and excess kurtosis {_fmt(startup_shape.excess_kurtosis)}; "
        f"{int(startup_shape.zero_count):,} observed values are zero ({startup_shape.zero_count / max(startup_shape['count'], 1) * 100:.1f}%). "
        "This is a descriptive distribution summary, not a decision to transform the variable.",
        "",
        "### Industry Growth",
        "",
        _summary_markdown(stats, ("employment_growth", "establishment_growth", "payroll_growth", "wage_growth", "employment_growth_lag1", "employment_growth_lag2", "employment_growth_lag3", "establishment_growth_lag1", "establishment_growth_lag2", "establishment_growth_lag3", "payroll_growth_lag1", "average_pay_growth_lag1")),
        "",
        f"Employment growth skewness is {_fmt(employment_shape.skewness)} with excess kurtosis {_fmt(employment_shape.excess_kurtosis)}. "
        f"The distribution includes {int(employment_shape.negative_count):,} negative observations and "
        f"{int(employment_shape.zero_count):,} exact zeros. Negative growth is economically possible.",
        "",
        "### Regional Context",
        "",
        _summary_markdown(stats, ("acs_population_growth", "median_household_income", "educational_attainment_pct", "labor_force_participation_pct", "unemployment_rate")),
        "",
        "ACS control gaps are distinct from panel lags: income, education, participation, and unemployment each have "
        f"{acs_missing:.2f}% missingness, corresponding to unmatched ACS support rows in the integration flags. "
        "Income is not common-year deflated. ACS values repeat across sector rows at MSA-year grain and are not independent regional observations.",
        "",
        "### Business Structure",
        "",
        _summary_markdown(stats, ("cbp_establishments", "cbp_employment", "cbp_annual_payroll", "cbp_first_quarter_payroll")),
        "",
        f"CBP employment is missing in {cbp_missing:.2f}% of core panel rows. The source flags distinguish unmatched/incomplete aggregates from rows marked as suppressed; native CBP payroll units remain $1,000. CBP support missingness does not remove a BDS-QCEW core row.",
        "",
        "## Missingness",
        "",
        "Overall rates are in `reports/tables/a5_missingness.csv`; selected year-level rates are in `a5_missingness_by_year.csv`. The cause table is an auditable partition, not an imputation model.",
        "",
        f"- **Expected structural/unavailable:** {cause_total('expected_structural_missing'):,} missing cells classified as outside the study-window predecessor or lacking a prior calendar-year panel key for a lag.",
        f"- **Source/data-quality flagged:** {cause_total('source_data_quality_missing'):,} missing cells associated with source suppression, ACS missing-control, or CBP completeness flags.",
        f"- **Support source unmatched:** {cause_total('support_source_missing'):,} missing cells with an ACS or CBP source-match flag set to unavailable.",
        f"- **Unexplained by available flags:** {cause_total('unexplained_missing'):,} cells remain unexplained; no cause is imputed from the pattern alone.",
        "",
        "Growth variables are missing for all 2010 panel rows because the prior year is outside the locked study panel; later missingness can also reflect gaps in valid prior source observations or denominators. Explicit lags require actual prior calendar years and otherwise remain null. ACS source matching is separate from lag availability. CBP is a left-joined support source; unmatched, suppressed, or incomplete CBP does not invalidate the core BDS-QCEW observation. Suppression is not zero.",
        "",
        f"The annual missingness table shows QCEW growth missingness at {growth_missing_text}. Highest missingness is concentrated at the initial study boundary for growth and lag families. The concentration table checks only leading missingness rates for selected fields (minimum group size 50); it is not a sector/MSA performance ranking.",
        "",
        *concentration_lines,
        "",
        "MSA-size context is a limited missingness check using MSA mean ACS population among MSAs with observed population and at least 50 panel rows; it does not rank regional performance:",
        *msa_size_lines,
        "",
        "## Distribution and Outlier Diagnostics",
        "",
        "The distribution table reports skewness, excess kurtosis, percentile tails, exact zeros, negatives, IQR flags, and 3-SD flags. IQR flags are screening counts, not errors. The two histograms zoom the x-axis to P01-P99 and therefore omit tail observations from the visible window; full-range values remain in the tables and extreme-observation output. The growth boxplot hides fliers only for readability; source values remain unchanged.",
        "",
        "| Variable | Skewness | Excess kurtosis | Zero N | Negative N | Shape notes |",
        "|---|---:|---:|---:|---:|---|",
        *shape_lines[2:],
        "",
        f"Among the selected core measures, `{outlier_leaders.variable}` has the most IQR flags "
        f"({int(outlier_leaders.iqr_outlier_count):,}); `{sd_leaders.variable}` has the most 3-SD flags "
        f"({int(sd_leaders.three_sd_count):,}). These thresholds are descriptive screens, not deletion rules.",
        *extreme_lines,
        "",
        "### Plausibility Flags",
        "",
        findings,
        "",
        f"Negative growth is valid. The range checks produced {rate_flags} rate/percentage flags; these are review prompts, not proof of invalid data and not cleaning rules. Nonnegative count/level measures also receive sign checks. No extreme finite growth observation is treated as impossible solely because it is large.",
        "",
        "### Prior-Denominator Review",
        "",
        *denominator_lines,
        "",
        "The comparison uses prior-year QCEW intermediate levels and the top 1% of absolute finite growth observations. Low denominators can make percentage changes volatile; this is a review signal, not proof of an error. No value is altered.",
        "",
        "## Limited Figures",
        "",
        *[f"- `reports/figures/{name}`" for name in figure_names],
        "",
        "## Implications for Later Analysis",
        "",
        "Revisit transformations for skewed positive level variables, robust summaries for heavy-tailed growth, whether controls with limited support availability belong in each later sample, and denominator sensitivity for extreme growth. Lag availability may constrain complete-history specifications and temporal validation. No transformation, deletion, capping, winsorization, imputation, or feature selection was performed here.",
        "",
        "## What Cannot Yet Be Concluded",
        "",
        "These summaries do not establish causality, predictive importance, hypothesis support, an entrepreneurial gap, expected entrepreneurship, or model performance. The panel is repeated over MSA-industry units; pooled observations are not independent. Time, sector, MSA pattern analysis and relationship analysis are reserved for A5.3/A5.4.",
    ]
    REPORT_PATH.write_text("\n".join(sections) + "\n", encoding="utf-8")


def run_descriptive(database_path: Path = DEFAULT_EDA_DATABASE) -> dict[str, object]:
    panel = load_analytical_panel(database_path)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    stats = summarize_numeric_variables(panel, SUMMARY_VARIABLES)
    missing = summarize_missingness(panel)
    missing_by_year = summarize_missingness_by_year(panel, YEAR_MISSINGNESS_VARIABLES)
    causes = summarize_structural_missingness(panel, SUMMARY_VARIABLES)
    shapes = summarize_distribution_shape(panel, CORE_SHAPE_VARIABLES)
    plausibility = summarize_economic_plausibility(panel)
    denominator_context = _load_denominator_context(database_path, panel)
    denominators = _denominator_diagnostics(denominator_context)
    concentration = _missingness_concentration(panel)
    msa_size = _msa_size_missingness(panel)
    extremes = _extreme_observations(panel)

    outputs = {
        "a5_descriptive_statistics.csv": stats,
        "a5_missingness.csv": missing,
        "a5_missingness_by_year.csv": missing_by_year,
        "a5_missingness_causes.csv": causes,
        "a5_distribution_diagnostics.csv": shapes,
        "a5_economic_plausibility.csv": plausibility,
        "a5_growth_denominator_review.csv": denominators,
        "a5_missingness_concentration.csv": concentration,
        "a5_missingness_msa_size_context.csv": msa_size,
        "a5_extreme_observations.csv": extremes,
    }
    for filename, table in outputs.items():
        table.to_csv(TABLE_DIR / filename, index=False, float_format="%.8g")
    figure_names = _save_figures(panel, missing)
    _write_report(
        panel, stats, missing, causes, shapes, plausibility, denominators,
        concentration, msa_size, extremes, figure_names
    )
    return {
        "rows": len(panel),
        "fields": len(panel.columns),
        "summary_variables": len(stats),
        "missingness_variables": len(missing),
        "figures": figure_names,
        "tables": list(outputs),
        "report": str(REPORT_PATH),
    }


if __name__ == "__main__":
    print(run_descriptive())
