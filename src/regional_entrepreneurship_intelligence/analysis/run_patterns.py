"""Generate Assignment 5.3 time, sector, MSA, and descriptive quadrant outputs."""

from __future__ import annotations

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

from regional_entrepreneurship_intelligence.analysis.eda import (
    ACS_MSA_YEAR_MEASURES,
    DEFAULT_EDA_DATABASE,
    PATTERN_MEASURES,
    build_descriptive_quadrants,
    collapse_acs_to_msa_year,
    load_analytical_panel,
    summarize_by_msa,
    summarize_by_sector,
    summarize_by_year,
    summarize_msa_coverage,
    summarize_sector_volatility,
)

ROOT = Path(__file__).resolve().parents[3]
TABLES = ROOT / "reports" / "tables"
FIGURES = ROOT / "reports" / "figures"
REPORT = ROOT / "reports" / "assignment5_time_industry_msa_patterns.md"
MIN_ROWS, MIN_SECTORS, MIN_YEARS = 100, 5, 10


def _year_summary(panel: pd.DataFrame) -> pd.DataFrame:
    panel_measures = tuple(v for v in PATTERN_MEASURES if v not in ACS_MSA_YEAR_MEASURES)
    core = summarize_by_year(panel, panel_measures)
    acs = summarize_by_year(collapse_acs_to_msa_year(panel), ACS_MSA_YEAR_MEASURES)
    return pd.concat([core, acs], ignore_index=True).sort_values(["year", "variable"])


def _figures(year: pd.DataFrame, sector: pd.DataFrame, msa: pd.DataFrame,
             quadrants: pd.DataFrame) -> list[str]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    names = []

    axis_labels = {
        "startup_rate": "Startup rate (percent)",
        "employment_growth": "Employment growth (decimal rate)",
        "unemployment_rate": "Unemployment rate (percent)",
        "acs_population_growth": "Population growth (decimal rate)",
    }

    def line(variable: str, title: str, filename: str, statistic: str = "median") -> None:
        data = year[year.variable.eq(variable)].sort_values("year")
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(data.year, data[statistic], marker="o")
        ax.set(title=title, xlabel="Year", ylabel=axis_labels[variable])
        ax.grid(True, alpha=.25)
        fig.tight_layout()
        fig.savefig(FIGURES / filename, dpi=150)
        plt.close(fig)
        names.append(filename)

    line("startup_rate", "Annual median startup rate", "a5_time_startup_rate.png")
    line("employment_growth", "Annual median employment growth", "a5_time_employment_growth.png")
    line("unemployment_rate", "Annual MSA-level median unemployment", "a5_time_unemployment.png")
    line("acs_population_growth", "Annual MSA-level median population growth", "a5_time_population_growth.png")

    for variable, title, filename in (
        ("startup_rate", "Median startup rate by sector", "a5_sector_startup_rate.png"),
        ("employment_growth", "Median employment growth by sector", "a5_sector_employment_growth.png"),
    ):
        data = sector[sector.variable.eq(variable)].sort_values("median")
        fig, ax = plt.subplots(figsize=(9, 6))
        ax.barh(data.sector_code.astype(str), data["median"])
        ax.set(title=title, xlabel=axis_labels[variable], ylabel="NAICS sector")
        ax.grid(True, axis="x", alpha=.25)
        fig.tight_layout()
        fig.savefig(FIGURES / filename, dpi=150)
        plt.close(fig)
        names.append(filename)

    for variable, title, filename in (
        ("employment_growth", "Sector employment-growth dispersion (IQR)", "a5_sector_growth_volatility.png"),
    ):
        data = sector[sector.variable.eq(variable)].sort_values("iqr")
        fig, ax = plt.subplots(figsize=(9, 6))
        ax.barh(data.sector_code.astype(str), data.iqr)
        ax.set(title=title, xlabel="Interquartile range", ylabel="NAICS sector")
        ax.grid(True, axis="x", alpha=.25)
        fig.tight_layout()
        fig.savefig(FIGURES / filename, dpi=150)
        plt.close(fig)
        names.append(filename)

    for variable, title, filename in (
        ("startup_rate", "MSA median startup-rate distribution", "a5_msa_startup_distribution.png"),
        ("employment_growth", "MSA median employment-growth distribution", "a5_msa_growth_distribution.png"),
    ):
        data = msa.loc[msa.variable.eq(variable) & msa.eligible_for_comparison, "median"].dropna()
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.hist(data, bins=30)
        ax.set(title=title, xlabel=axis_labels[variable], ylabel="Number of MSAs")
        ax.grid(True, axis="y", alpha=.25)
        fig.tight_layout()
        fig.savefig(FIGURES / filename, dpi=150)
        plt.close(fig)
        names.append(filename)

    high_low = quadrants[quadrants.quadrant.eq("high_growth_low_startup")]
    prevalence = high_low.groupby("year").observation_count.sum().div(
        quadrants.groupby("year").observation_count.sum()
    ).mul(100)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(prevalence.index, prevalence.values, marker="o")
    ax.set(title="High-growth / low-startup share of classified observations",
           xlabel="Year", ylabel="Percent of classified observations")
    ax.grid(True, alpha=.25)
    fig.tight_layout()
    filename = "a5_descriptive_quadrant_prevalence.png"
    fig.savefig(FIGURES / filename, dpi=150)
    plt.close(fig)
    names.append(filename)
    return names


def _write_report(panel: pd.DataFrame, year: pd.DataFrame, sector: pd.DataFrame,
                  msa: pd.DataFrame, coverage: pd.DataFrame, quadrants: pd.DataFrame,
                  figures: list[str]) -> None:
    def ranked(variable: str, field: str = "median", ascending: bool = False) -> tuple[str, str]:
        data = sector[sector.variable.eq(variable)].sort_values(field, ascending=ascending)
        return (f"{data.iloc[0].sector_code} ({data.iloc[0][field]:.4g})",
                f"{data.iloc[-1].sector_code} ({data.iloc[-1][field]:.4g})")

    startup_high, startup_low = ranked("startup_rate")
    growth_high, growth_low = ranked("employment_growth")
    startup_vol_high, startup_vol_low = ranked("startup_rate", "iqr")
    growth_vol_high, growth_vol_low = ranked("employment_growth", "iqr")
    growth_tail_high = ranked("employment_growth", "p95")
    growth_tail_low = ranked("employment_growth", "p05", True)
    eligible = int(coverage.eligible_for_comparison.sum())
    high_low_count = int(quadrants.loc[quadrants.quadrant.eq("high_growth_low_startup"), "observation_count"].sum())
    classified_count = int(quadrants.observation_count.sum())
    year_stats = year.set_index(["year", "variable"])
    period_lines = []
    for variable in ("startup_rate", "employment_growth", "establishment_growth", "payroll_growth",
                     "unemployment_rate", "acs_population_growth"):
        values = [year_stats.loc[(yr, variable), "median"] for yr in (2019, 2020, 2021, 2022)]
        period_lines.append(f"- `{variable}` annual medians, 2019–2022: " + ", ".join(
            f"{yr} {val:.4g}" if pd.notna(val) else f"{yr} NA" for yr, val in zip((2019, 2020, 2021, 2022), values)))

    context_lines = []
    for variable in ACS_MSA_YEAR_MEASURES:
        data = year[year.variable.eq(variable)].sort_values("year")
        observed = data.dropna(subset=["median"])
        if len(observed):
            low = observed.loc[observed["median"].idxmin()]
            high = observed.loc[observed["median"].idxmax()]
            context_lines.append(f"- `{variable}`: lowest annual MSA median {low['median']:.4g} ({int(low.year)}); "
                                 f"highest {high['median']:.4g} ({int(high.year)}); counts and missingness are in the year table.")

    endpoints = []
    for variable in ("startup_rate", "employment_growth", "establishment_growth", "payroll_growth"):
        data = year[year.variable.eq(variable)].set_index("year")
        start = data.loc[2010, "median"]
        end = data.loc[2023, "median"]
        start_text = f"{start:.4g}" if pd.notna(start) else "unavailable (no prior-year growth baseline)"
        end_text = f"{end:.4g}" if pd.notna(end) else "unavailable"
        endpoints.append(f"- `{variable}` median: {start_text} in 2010 to {end_text} in 2023.")

    eligible_msa = msa[msa.eligible_for_comparison & msa.variable.eq("startup_rate")]
    msa_startup_high = eligible_msa.sort_values("median").iloc[-1]
    msa_startup_low = eligible_msa.sort_values("median").iloc[0]
    eligible_growth = msa[msa.eligible_for_comparison & msa.variable.eq("employment_growth")]
    msa_growth_high = eligible_growth.sort_values("median").iloc[-1]
    msa_growth_low = eligible_growth.sort_values("median").iloc[0]
    msa_startup_volatile = eligible_msa.sort_values("iqr").iloc[-1]
    msa_startup_stable = eligible_msa.sort_values("iqr").iloc[0]
    msa_zero_high = eligible_msa.sort_values("zero_pct").iloc[-1]
    eligible_growth_volatile = msa[msa.eligible_for_comparison & msa.variable.eq("employment_growth")]
    msa_growth_volatile = eligible_growth_volatile.sort_values("iqr").iloc[-1]
    mquad = pd.read_csv(TABLES / "a5_msa_descriptive_quadrants.csv")
    high_low = quadrants[quadrants.quadrant.eq("high_growth_low_startup")]
    frequent_msa = mquad[mquad.quadrant.eq("high_growth_low_startup")].sort_values(
        "observation_count", ascending=False).head(5)
    frequent_sector = quadrants[quadrants.quadrant.eq("high_growth_low_startup")].groupby(
        "sector_code").observation_count.sum().sort_values(ascending=False).head(5)
    year_prevalence = (high_low.groupby("year").observation_count.sum() /
                       quadrants.groupby("year").observation_count.sum()).sort_values(ascending=False)
    sections = [
        "# Assignment 5.3: Time, Industry & MSA Pattern Analysis", "",
        "## Executive Summary", "",
        f"The analysis covers {len(panel):,} MSA-sector-year rows, {panel.cbsa_code.nunique()} MSAs, "
        f"{panel.sector_code.nunique()} sectors, and 2010–2023. It is descriptive: no causal, predictive, or A5.4 relationship analysis is performed.", "",
        f"Sector medians span {startup_low} to {startup_high} for startup rate and {growth_low} to {growth_high} for employment growth. "
        f"{eligible} of {len(coverage)} MSAs meet the documented coverage rule for comparative summaries.", "",
        "## Time Patterns", "",
        "Annual panel growth/startup summaries use available observations and report count, missingness, mean, median, standard deviation, and quartiles. "
        "ACS controls are summarized using one MSA-year row, not repeated industry rows. Growth rates are decimal changes; startup rates/profile percentages use percent units.", "",
        *endpoints, "",
        "Employment growth is heavy-tailed, so the median is emphasized alongside the mean. Year tables report available counts and missing rates; ACS measures use MSA-year counts.", "",
        "## 2020–2021 Descriptive Review", "", *period_lines, "",
        "These adjacent-year comparisons are descriptive only. No event-study, causal COVID attribution, or structural-break test was conducted.", "",
        "## Industry Patterns", "",
        f"By sector median startup rate, the highest is {startup_high} and lowest is {startup_low}; the highest and lowest median employment growth are {growth_high} and {growth_low}.", "",
        f"The largest/smallest startup-rate IQRs are {startup_vol_high} and {startup_vol_low}; for employment growth they are {growth_vol_high} and {growth_vol_low}. "
        f"Employment-growth sector 95th percentiles are highest/lowest in {growth_tail_high[0]} / {growth_tail_high[1]}; 5th percentiles are highest/lowest in {growth_tail_low[0]} / {growth_tail_low[1]}. "
        "IQR is the stated robust dispersion measure; standard deviation and MAD are also retained in tables. Dispersion is not performance.", "",
        "Sector summaries include row/MSA/year counts, observed N, missingness, zero shares, quartiles, and tail-sensitive mean/standard deviation.", "",
        "## Industry Volatility", "",
        "Annual sector summaries are available by sector-year in `a5_sector_year_summary.csv`; volatility tables use IQR, standard deviation, and MAD.", "",
        "## MSA Coverage", "",
        f"All {len(coverage)} MSAs remain in the full summary. A comparison-eligible MSA must have at least {MIN_ROWS} panel rows, {MIN_SECTORS} sectors, and {MIN_YEARS} years; {eligible} qualify. "
        "The rule is an explicit coverage screen, not a quality judgment or statistical guarantee.", "",
        "## MSA Entrepreneurship Patterns", "",
        f"Among eligible MSAs, the highest/lowest median startup rate is {msa_startup_high.cbsa_name} ({msa_startup_high['median']:.4g}) / {msa_startup_low.cbsa_name} ({msa_startup_low['median']:.4g}). "
        f"The highest/lowest median employment growth is {msa_growth_high.cbsa_name} ({msa_growth_high['median']:.4g}) / {msa_growth_low.cbsa_name} ({msa_growth_low['median']:.4g}). "
        f"Startup-rate IQR is largest in {msa_startup_volatile.cbsa_name} ({msa_startup_volatile.iqr:.4g}) and smallest in {msa_startup_stable.cbsa_name} ({msa_startup_stable.iqr:.4g}); "
        f"the greatest startup zero share is {msa_zero_high.cbsa_name} ({msa_zero_high.zero_pct:.1f}%). Employment-growth IQR is greatest in {msa_growth_volatile.cbsa_name} ({msa_growth_volatile.iqr:.4g}). "
        "These are descriptive orderings only.", "",
        "## MSA Industry-Growth Patterns", "",
        "Employment-growth medians and dispersion are summarized for every MSA. Means may be unstable under sparse support and heavy tails; eligibility limits, but does not eliminate, this concern. No observations are removed or winsorized.", "",
        "## Regional Context", "", *context_lines, "",
        "ACS controls are MSA-year measures repeated across industry rows in the integrated panel. Every ACS-only annual and MSA summary first validates within-MSA-year agreement and collapses to one row per MSA-year, preventing industry replication weighting. Income is not deflated to common-year dollars.", "",
        "## Descriptive High-Growth / Low-Startup Patterns", "",
        f"Rows are classified against contemporaneous year-by-sector medians (ties count as high); {high_low_count:,} of {classified_count:,} classified observations "
        f"({high_low_count / classified_count * 100:.2f}%) are high-growth/low-startup. The most frequent sectors are {', '.join(frequent_sector.index.astype(str))}; "
        f"the years with the largest shares are {', '.join(str(int(y)) for y in year_prevalence.head(3).index)}. "
        f"Among eligible MSAs, most frequent by count include {', '.join(f'{r.cbsa_name} ({int(r.observation_count)})' for r in frequent_msa.itertuples())}. "
        "`a5_descriptive_quadrants.csv` reports counts/percentages within sector-year; `a5_msa_descriptive_quadrants.csv` reports eligible-MSA frequencies and within-MSA shares. "
        "This exploratory grouping uses no future values and is NOT the final entrepreneurial-gap target, expected entrepreneurship, or a model label.", "",
        "## Data Limitations", "",
        "Growth missingness includes initial-year/prior-source availability constraints. Startup rate is a percentage; growth is decimal. ACS years and income definitions follow source release conventions. This panel is repeated across MSA-sector units; pooled summary counts are not independent samples.", "",
        "## Questions Raised for Relationship Analysis", "",
        "- Do sectors with higher employment growth also show different startup rates?",
        "- Does startup-rate persistence vary by sector or MSA?",
        "- How do population growth, unemployment, income, and education co-vary with the descriptive patterns?",
        "- Are high-growth/low-startup observations more prevalent in particular sectors or years?",
        "These questions are not tested here; they belong to A5.4.", "",
        "## Figures", "", *[f"- `reports/figures/{name}`" for name in figures], "",
    ]
    REPORT.write_text("\n".join(sections), encoding="utf-8")


def run_patterns(database_path: Path = DEFAULT_EDA_DATABASE) -> dict[str, object]:
    panel = load_analytical_panel(database_path)
    TABLES.mkdir(parents=True, exist_ok=True)
    year = _year_summary(panel)
    sector = summarize_by_sector(panel)
    sector_year = panel.groupby(["year", "sector_code"], as_index=False).agg(
        observation_count=("geography_id", "size"), msa_count=("geography_id", "nunique"),
        startup_rate_median=("startup_rate", "median"), employment_growth_median=("employment_growth", "median"),
    )
    coverage = summarize_msa_coverage(panel, min_rows=MIN_ROWS, min_sectors=MIN_SECTORS, min_years=MIN_YEARS)
    msa = summarize_by_msa(panel, min_rows=MIN_ROWS, min_sectors=MIN_SECTORS, min_years=MIN_YEARS)
    volatility = summarize_sector_volatility(panel)
    quadrants = build_descriptive_quadrants(panel)
    msa_quadrants = build_descriptive_quadrants(panel, group_by=("geography_id", "cbsa_code", "cbsa_name"))
    msa_quadrants = msa_quadrants.merge(coverage[["geography_id", "eligible_for_comparison"]],
                                        on="geography_id", validate="many_to_one")
    outputs = {
        "a5_year_summary.csv": year,
        "a5_sector_summary.csv": sector,
        "a5_sector_year_summary.csv": sector_year,
        "a5_sector_volatility.csv": volatility,
        "a5_msa_summary.csv": msa,
        "a5_msa_coverage.csv": coverage,
        "a5_descriptive_quadrants.csv": quadrants,
        "a5_msa_descriptive_quadrants.csv": msa_quadrants,
    }
    for filename, data in outputs.items():
        data.to_csv(TABLES / filename, index=False, float_format="%.8g")
    figures = _figures(year, sector, msa, quadrants)
    _write_report(panel, year, sector, msa, coverage, quadrants, figures)
    return {"rows": len(panel), "msas": len(coverage), "eligible_msas": int(coverage.eligible_for_comparison.sum()),
            "sectors": panel.sector_code.nunique(), "tables": list(outputs), "figures": figures,
            "report": str(REPORT)}


if __name__ == "__main__":
    print(run_patterns())
