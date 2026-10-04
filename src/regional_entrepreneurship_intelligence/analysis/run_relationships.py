"""Generate Assignment 5.4 exploratory relationship and hypothesis outputs."""

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
    build_correlation_matrix,
    calculate_pairwise_relationship,
    collapse_acs_to_msa_year,
    fit_exploratory_regression,
    load_analytical_panel,
    run_covid_sensitivity,
    run_outlier_sensitivity,
    summarize_lag_relationships,
    summarize_quadrant_context,
    summarize_sector_relationships,
)

ROOT = Path(__file__).resolve().parents[3]
TABLES = ROOT / "reports" / "tables"
FIGURES = ROOT / "reports" / "figures"
REPORT = ROOT / "reports" / "assignment5_relationship_hypothesis_analysis.md"
CORE_VARIABLES = (
    "startup_rate", "employment_growth", "establishment_growth", "payroll_growth", "wage_growth",
    "acs_population_growth", "median_household_income", "educational_attainment_pct",
    "labor_force_participation_pct", "unemployment_rate",
)
GROWTH_VARIABLES = ("employment_growth", "establishment_growth", "payroll_growth", "wage_growth")
REGIONAL_CONTROLS = (
    "acs_population_growth", "median_household_income", "educational_attainment_pct",
    "labor_force_participation_pct", "unemployment_rate",
)


def _pair_table(panel: pd.DataFrame, msa_year: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for x in (*GROWTH_VARIABLES, *REGIONAL_CONTROLS):
        for method in ("pearson", "spearman"):
            result = calculate_pairwise_relationship(panel, x, "startup_rate", method)
            result["sample_grain"] = "msa_sector_year_pooled"
            rows.append(result)
    for x in REGIONAL_CONTROLS:
        for y in ("startup_rate", "employment_growth"):
            for method in ("pearson", "spearman"):
                result = calculate_pairwise_relationship(msa_year, x, y, method)
                result["sample_grain"] = "msa_year_means_across_sectors"
                rows.append(result)
    for x in REGIONAL_CONTROLS:
        for method in ("pearson", "spearman"):
            result = calculate_pairwise_relationship(panel, x, "employment_growth", method)
            result["sample_grain"] = "msa_sector_year_pooled"
            rows.append(result)
    return pd.DataFrame(rows)


def _msa_year_frame(panel: pd.DataFrame) -> pd.DataFrame:
    acs = collapse_acs_to_msa_year(panel)
    industry_means = panel.groupby(["geography_id", "year"], as_index=False).agg(
        startup_rate=("startup_rate", "mean"), employment_growth=("employment_growth", "mean"),
    )
    return acs.merge(industry_means, on=["geography_id", "year"], validate="one_to_one")


def _regressions(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    specifications = (
        ("bivariate", ("employment_growth",), ()),
        ("year_controls", ("employment_growth",), ("year",)),
        ("sector_controls", ("employment_growth",), ("sector_code",)),
        ("year_sector_controls", ("employment_growth",), ("year", "sector_code")),
        ("regional_controls_year_sector", (
            "employment_growth", *REGIONAL_CONTROLS,
        ), ("year", "sector_code")),
    )
    outputs = []
    for name, predictors, categorical in specifications:
        outputs.append(fit_exploratory_regression(
            panel, "startup_rate", predictors, categorical=categorical,
            model_name=name,
        ))
    coefficients = pd.concat(outputs, ignore_index=True)
    model_summary = coefficients.groupby("model", as_index=False).agg(
        n=("n", "first"), r_squared=("r_squared", "first"), covariance=("covariance", "first"),
    )
    return coefficients, model_summary


def _within_panel_persistence(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    work = panel[["geography_id", "industry_id", "startup_rate", "startup_rate_lag1"]].copy()
    for variable in ("startup_rate", "startup_rate_lag1"):
        work[f"{variable}_within"] = work[variable] - work.groupby(
            ["geography_id", "industry_id"]
        )[variable].transform("mean")
    for x, y, label in (("startup_rate_lag1", "startup_rate", "pooled_levels"),
                        ("startup_rate_lag1_within", "startup_rate_within", "within_panel_deviations")):
        result = calculate_pairwise_relationship(work, x, y, "pearson")
        result["sample_grain"] = label
        rows.append(result)
    return pd.DataFrame(rows)


def _quadrant_composition(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = panel[["year", "sector_code", "startup_rate", "employment_growth"]].copy()
    work["startup_cutoff"] = work.groupby(["year", "sector_code"]).startup_rate.transform("median")
    work["growth_cutoff"] = work.groupby(["year", "sector_code"]).employment_growth.transform("median")
    work = work.dropna(subset=["startup_rate", "employment_growth"])
    work["quadrant"] = np.where(work.employment_growth.ge(work.growth_cutoff), "high_growth_", "low_growth_") + np.where(
        work.startup_rate.ge(work.startup_cutoff), "high_startup", "low_startup")
    sector = work.groupby(["quadrant", "sector_code"]).size().rename("observation_count").reset_index()
    sector["percent_within_quadrant"] = sector.observation_count / sector.groupby("quadrant").observation_count.transform("sum") * 100
    year = work.groupby(["quadrant", "year"]).size().rename("observation_count").reset_index()
    year["percent_within_quadrant"] = year.observation_count / year.groupby("quadrant").observation_count.transform("sum") * 100
    return sector, year


def _quadrant_panel_context(panel: pd.DataFrame) -> pd.DataFrame:
    """Summarize classified MSA-sector-year rows separately from MSA-year context."""
    work = panel[["geography_id", "year", "sector_code", "startup_rate", "employment_growth"]].copy()
    work["startup_cutoff"] = work.groupby(["year", "sector_code"]).startup_rate.transform("median")
    work["growth_cutoff"] = work.groupby(["year", "sector_code"]).employment_growth.transform("median")
    work = work.dropna(subset=["startup_rate", "employment_growth"])
    work["quadrant"] = np.where(work.employment_growth.ge(work.growth_cutoff), "high_growth_", "low_growth_") + np.where(
        work.startup_rate.ge(work.startup_cutoff), "high_startup", "low_startup"
    )
    return work.groupby("quadrant", as_index=False).agg(
        observation_count=("geography_id", "size"),
        msa_count=("geography_id", "nunique"),
        sector_count=("sector_code", "nunique"),
        startup_rate_mean=("startup_rate", "mean"),
        startup_rate_median=("startup_rate", "median"),
        employment_growth_mean=("employment_growth", "mean"),
        employment_growth_median=("employment_growth", "median"),
    )


def _figures(panel: pd.DataFrame, pearson: pd.DataFrame, sectors: pd.DataFrame,
             covid: pd.DataFrame) -> list[str]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    names = []

    def save(fig: plt.Figure, filename: str) -> None:
        fig.tight_layout()
        fig.savefig(FIGURES / filename, dpi=150)
        plt.close(fig)
        names.append(filename)

    rng = np.random.default_rng(751)
    display = panel[["employment_growth", "startup_rate"]].dropna()
    if len(display) > 12000:
        display = display.iloc[np.sort(rng.choice(len(display), 12000, replace=False))]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(display.employment_growth, display.startup_rate, alpha=.18, s=10)
    ax.set(title="Startup rate and employment growth", xlabel="Employment growth (decimal)", ylabel="Startup rate (%)")
    ax.grid(True, alpha=.2)
    save(fig, "a5_relationship_growth_startup_scatter.png")

    full = panel[["employment_growth", "startup_rate"]].dropna().copy()
    full["growth_bin"] = pd.qcut(full.employment_growth, 20, duplicates="drop")
    binned = full.groupby("growth_bin", observed=True).agg(
        growth_median=("employment_growth", "median"), startup_median=("startup_rate", "median"),
    ).reset_index()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(binned.growth_median, binned.startup_median, marker="o")
    ax.set(title="Binned median growth-startup pattern", xlabel="Median employment growth (decimal)", ylabel="Median startup rate (%)")
    ax.grid(True, alpha=.25)
    save(fig, "a5_relationship_growth_startup_binned.png")

    lag = panel[["startup_rate_lag1", "startup_rate"]].dropna()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(lag.startup_rate_lag1, lag.startup_rate, alpha=.15, s=10)
    ax.set(title="Current and prior-year startup rate", xlabel="Prior-year startup rate (%)", ylabel="Current startup rate (%)")
    ax.grid(True, alpha=.2)
    save(fig, "a5_relationship_startup_lag1.png")

    sector_plot = sectors.sort_values("pearson")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(sector_plot.sector_code.astype(str), sector_plot.pearson)
    ax.axvline(0, linewidth=.8)
    ax.set(title="Growth-startup Pearson correlation by sector", xlabel="Pearson correlation", ylabel="NAICS sector")
    ax.grid(True, axis="x", alpha=.2)
    save(fig, "a5_relationship_sector_correlations.png")

    matrix = build_correlation_matrix(panel, CORE_VARIABLES, "pearson")
    fig, ax = plt.subplots(figsize=(9, 8))
    image = ax.imshow(matrix.to_numpy(), vmin=-1, vmax=1, cmap="coolwarm", aspect="auto")
    ax.set_xticks(range(len(matrix.columns)), matrix.columns, rotation=70, ha="right")
    ax.set_yticks(range(len(matrix.index)), matrix.index)
    ax.set_title("Pairwise Pearson correlation matrix (pooled panel)")
    fig.colorbar(image, ax=ax, label="Pearson correlation")
    save(fig, "a5_relationship_correlation_matrix.png")

    for variable, filename, title in (
        ("unemployment_rate", "a5_relationship_startup_unemployment.png", "Startup rate and unemployment"),
        ("acs_population_growth", "a5_relationship_startup_population_growth.png", "Startup rate and population growth"),
    ):
        sample = panel[[variable, "startup_rate"]].dropna()
        if len(sample) > 12000:
            sample = sample.iloc[np.sort(rng.choice(len(sample), 12000, replace=False))]
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(sample[variable], sample.startup_rate, alpha=.18, s=10)
        xlabel = "Unemployment rate (percent)" if variable == "unemployment_rate" else "Population growth (decimal rate)"
        ax.set(title=title, xlabel=xlabel, ylabel="Startup rate (percent)")
        ax.grid(True, alpha=.2)
        save(fig, filename)

    selected = covid[covid.method.eq("pearson")]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(selected.sensitivity, selected.coefficient)
    ax.axhline(0, linewidth=.8)
    ax.set(title="Primary correlation under year-exclusion sensitivities", ylabel="Pearson correlation", xlabel="Sensitivity sample")
    ax.tick_params(axis="x", rotation=15)
    ax.grid(True, axis="y", alpha=.2)
    save(fig, "a5_relationship_covid_sensitivity.png")
    return names


def _write_report(panel: pd.DataFrame, correlations: pd.DataFrame, regressions: pd.DataFrame,
                  model_summary: pd.DataFrame, sectors: pd.DataFrame, lags: pd.DataFrame,
                  covid: pd.DataFrame, outliers: pd.DataFrame, within: pd.DataFrame,
                  quadrant: pd.DataFrame, quadrant_sectors: pd.DataFrame,
                  quadrant_years: pd.DataFrame, figures: list[str]) -> None:
    def corr_text(x: str, y: str, method: str = "pearson", grain: str = "msa_sector_year_pooled") -> str:
        row = correlations[(correlations.x == x) & (correlations.y == y) &
                           (correlations.method == method) & (correlations.sample_grain == grain)].iloc[0]
        return f"r={row.coefficient:.3f}, N={int(row.n):,}"

    def model_line(name: str) -> str:
        metric = model_summary[model_summary.model.eq(name)].iloc[0]
        coef = regressions[(regressions.model.eq(name)) & (regressions.term.eq("employment_growth"))]
        term = ""
        if len(coef):
            row = coef.iloc[0]
            p_value = "<0.001" if row.p_value < .001 else f"{row.p_value:.3g}"
            term = (f", growth coefficient={row.coefficient:.4g} (SE {row.std_error:.3g}; "
                    f"95% CI {row.ci_lower:.4g} to {row.ci_upper:.4g}; p {p_value})")
        return f"`{name}`: N={int(metric.n):,}, R²={metric.r_squared:.4f}{term}."

    pearson_sector = sectors.sort_values("pearson")
    sector_slope_high = sectors.sort_values("slope").iloc[-1]
    sector_slope_low = sectors.sort_values("slope").iloc[0]
    lag_rows = lags.sort_values(["lag", "method"])
    covid_p = covid[covid.method.eq("pearson")].set_index("sensitivity")
    outlier_idx = outliers.set_index("sensitivity")
    positive_n = int((sectors.pearson > 0).sum())
    negative_n = int((sectors.pearson < 0).sum())
    quadrant.sort_values("msa_year_count", ascending=False, inplace=True)
    qtext = "; ".join(f"{r.quadrant}: {int(r.msa_year_count):,} MSA-year-quadrants ({r.startup_rate_mean:.2f}% mean startup rate)" for r in quadrant.itertuples())
    q_highlow = quadrant[quadrant.quadrant.eq("high_growth_low_startup")].iloc[0]
    q_highhigh = quadrant[quadrant.quadrant.eq("high_growth_high_startup")].iloc[0]
    high_low_sector = quadrant_sectors[quadrant_sectors.quadrant.eq("high_growth_low_startup")].nlargest(3, "percent_within_quadrant")
    high_low_year = quadrant_years[quadrant_years.quadrant.eq("high_growth_low_startup")].nlargest(3, "percent_within_quadrant")
    year_pair = calculate_pairwise_relationship(panel, "employment_growth", "startup_rate", "pearson")
    sections = [
        "# Assignment 5.4: Relationship & Hypothesis-Oriented Analysis", "",
        "## Executive Summary", "",
        f"The primary pooled available-case association is {corr_text('employment_growth', 'startup_rate')}; Spearman is {corr_text('employment_growth', 'startup_rate', 'spearman')}. "
        f"Sector correlations are positive in {positive_n} and negative in {negative_n} of {len(sectors)} sectors, indicating pooled summaries may conceal heterogeneous patterns.", "",
        "This is exploratory evidence, not causal inference, a final panel specification, prediction evaluation, or a formal test of the future-gap hypotheses. Pooled p-values assume independent observations and are not treated as inferential evidence here.", "",
        "## H2 — Industry Growth and Entrepreneurship", "",
        f"Primary employment growth vs startup rate: Pearson {corr_text('employment_growth', 'startup_rate')}; Spearman {corr_text('employment_growth', 'startup_rate', 'spearman')}. "
        f"Supporting Pearson correlations: establishment growth {corr_text('establishment_growth', 'startup_rate')}, payroll growth {corr_text('payroll_growth', 'startup_rate')}, wage growth {corr_text('wage_growth', 'startup_rate')}.", "",
        "Regional controls in the correlation table use pairwise available observations. Pooled MSA-sector-year correlations repeat MSA-year ACS values across industries; the separately labeled MSA-year table instead correlates annual means across sectors with a single ACS record per MSA-year.", "",
        "## H3 — Entrepreneurship Persistence", "",
        *[f"- Lag {int(r.lag)} {r.method}: r={r.coefficient:.3f}, N={int(r.n):,}." for r in lag_rows.itertuples()],
        f"Within-panel demeaned lag-1 correlation: {within.loc[within.sample_grain.eq('within_panel_deviations'), 'coefficient'].iloc[0]:.3f} "
        f"(N={int(within.loc[within.sample_grain.eq('within_panel_deviations'), 'n'].iloc[0]):,}); pooled-level result is {within.loc[within.sample_grain.eq('pooled_levels'), 'coefficient'].iloc[0]:.3f}.", "",
        "These summarize persistence in observed startup rates only. They do NOT test whether prior entrepreneurship reduces future entrepreneurial-gap probability; no future gap outcome exists here.", "",
        "## H4 — Sector Heterogeneity", "",
        f"Sector Pearson coefficients range from {pearson_sector.iloc[0].sector_code} ({pearson_sector.iloc[0].pearson:.3f}, near zero) to {pearson_sector.iloc[-1].sector_code} ({pearson_sector.iloc[-1].pearson:.3f}); "
        f"all 19 are positive, with {int((sectors.pearson.abs() < .05).sum())} near-zero (|r|<.05). The strongest coefficients are in sectors {', '.join(sectors.nlargest(3, 'pearson').sector_code.astype(str))}. "
        f"Sector simple slopes range from {sector_slope_low.sector_code} ({sector_slope_low.slope:.3g}) to {sector_slope_high.sector_code} ({sector_slope_high.slope:.3g}) startup-rate points per unit growth rate. "
        "This variation is preliminary descriptive evidence of heterogeneity, not a confirmatory interaction test.", "",
        "## Regional Context", "",
        f"Pooled startup-rate Pearson associations: population growth {corr_text('acs_population_growth', 'startup_rate')}; income {corr_text('median_household_income', 'startup_rate')}; "
        f"education {corr_text('educational_attainment_pct', 'startup_rate')}; labor-force participation {corr_text('labor_force_participation_pct', 'startup_rate')}; unemployment {corr_text('unemployment_rate', 'startup_rate')}.", "",
        "MSA-year-grain correlations, with industry-average startup/growth measures matched to one ACS record per geography-year:",
        *[f"- `{v}` vs MSA-year mean startup rate: Pearson {corr_text(v, 'startup_rate', 'pearson', 'msa_year_means_across_sectors')}; Spearman {corr_text(v, 'startup_rate', 'spearman', 'msa_year_means_across_sectors')}; "
           f"vs MSA-year mean employment growth: Pearson {corr_text(v, 'employment_growth', 'pearson', 'msa_year_means_across_sectors')}; Spearman {corr_text(v, 'employment_growth', 'spearman', 'msa_year_means_across_sectors')}." for v in REGIONAL_CONTROLS], "",
        "Pairwise candidate correlations are a redundancy screen, not an automatic variable-removal rule. Pooled Pearson employment-growth/payroll-growth is 0.714; payroll/wage growth is 0.621; income/education is 0.613; income/unemployment is -0.520. These are potentially overlapping signals, not proof that a predictor must be removed. No variable was dropped based on correlations or p-values.", "",
        "## Exploratory Regression Results", "",
        *[f"- {model_line(name)}" for name in model_summary.model], "",
        "Growth is stored as a decimal rate and startup rate as percentage points: the bivariate slope is per 1.0 (100 percentage point) growth-rate change; a 0.01 change corresponds to about 0.042 startup-rate points. The coefficient stays positive and declines from 4.207 pooled to 3.502 with year and sector controls; R² rises from 0.0098 to 0.342, largely reflecting sector/year level differences rather than a predictive-performance test. OLS covariance is clustered by MSA-industry panel. Even clustered standard errors do not address shared year shocks or all dependence structures. The year + sector model controls additive differences only; no interaction/final panel model is fit. The modest regional-controls specification is complete-case and its N may differ substantially.", "",
        "## COVID-19 Context and Sensitivity", "",
        "2020–2021 occurred during the COVID-19 pandemic and associated economic disruption and reopening. Excluding these years is sensitivity analysis, not a recommendation to delete them and not an estimate of a COVID effect.", "",
        *[f"- {label}: Pearson r={covid_p.loc[label, 'coefficient']:.3f} (N={int(covid_p.loc[label, 'n']):,}); Spearman r={covid[(covid.sensitivity == label) & (covid.method == 'spearman')].coefficient.iloc[0]:.3f}." for label in ("full", "exclude_2020", "exclude_2020_2021")],
        "The direction remains weakly positive in all samples; excluding 2020 alone changes magnitude more than excluding both years. This is sensitivity analysis only.", "",
        "## Outlier Sensitivity", "",
        *[f"- {label}: r={row.coefficient:.3f}, N={int(row.n):,}." for label, row in outlier_idx.iterrows()],
        "The P01/P99 specification excludes observations outside those employment-growth quantiles for this calculation only; production values are unchanged. The positive direction persists while Pearson magnitude increases after trimming (0.099 to 0.155), indicating tail observations affect magnitude but not sign. Spearman is a rank-based comparison, not an outlier deletion rule.", "",
        "## Descriptive Quadrant Context", "",
        f"A5.3 sector-year median quadrant context, collapsed to one row per MSA-year within each quadrant: {qtext}. "
        f"High-growth/low-startup versus high-growth/high-startup mean income is {q_highlow.median_household_income_mean:,.0f} vs {q_highhigh.median_household_income_mean:,.0f}, "
        f"education {q_highlow.educational_attainment_pct_mean:.1f}% vs {q_highhigh.educational_attainment_pct_mean:.1f}%, and unemployment {q_highlow.unemployment_rate_mean:.2f}% vs {q_highhigh.unemployment_rate_mean:.2f}%. "
        "Selected ACS context means by quadrant are retained in `a5_quadrant_msa_year_context.csv`; each MSA-year contributes at most once to each quadrant. "
        f"Among high-growth/low-startup observations, largest sector shares are {', '.join(high_low_sector.sector_code.astype(str))} and largest year shares are {', '.join(high_low_year.year.astype(str))}. "
        "Full sector/year composition counts are in `a5_quadrant_sector_composition.csv` and `a5_quadrant_year_composition.csv`.", "",
        "`a5_quadrant_context.csv` summarizes classified MSA-sector-year rows; `a5_quadrant_msa_year_context.csv` collapses each MSA-year once within quadrant for regional context. These are descriptive group summaries, NOT the entrepreneurial-gap target and not regression outcomes.", "",
        "## Multicollinearity / Predictor Redundancy", "",
        "Pairwise matrix coefficients identify potentially redundant candidates but do not establish harmful multicollinearity in a final specification. Growth measures share economic content; income and education may co-vary; unemployment and labor-force participation may overlap. No VIF-based pruning or p-value selection was performed.", "",
        "## Limitations", "",
        f"The primary pairwise available-case sample has N={year_pair['n']:,}. The panel repeats MSA-industry observations over time, while ACS measures repeat across industries within MSA-year. Pooled observations and p-values are not independent/causal evidence. Extreme growth is heavy-tailed; all sensitivity filters are non-destructive. These analyses assess association and persistence, not predictive improvement or future outcomes.", "",
        "## Implications for Assignment 6", "",
        "Consider year and sector controls; compare candidate growth measures without collapsing them into an unvalidated index; assess panel-aware uncertainty; retain sensitivity checks for heavy tails; inspect lag availability/persistence; and handle ACS at its MSA-year origin grain. Correlated candidates merit specification diagnostics rather than automatic exclusion. No Assignment 6 code or target was created.", "",
        "## Figures", "", *[f"- `reports/figures/{name}`" for name in figures], "",
    ]
    REPORT.write_text("\n".join(sections), encoding="utf-8")


def run_relationships(database_path: Path = DEFAULT_EDA_DATABASE) -> dict[str, object]:
    panel = load_analytical_panel(database_path)
    TABLES.mkdir(parents=True, exist_ok=True)
    msa_year = _msa_year_frame(panel)
    pairs = _pair_table(panel, msa_year)
    pearson = build_correlation_matrix(panel, CORE_VARIABLES, "pearson")
    spearman = build_correlation_matrix(panel, CORE_VARIABLES, "spearman")
    sectors = summarize_sector_relationships(panel)
    lags = summarize_lag_relationships(panel)
    regressions, models = _regressions(panel)
    covid = run_covid_sensitivity(panel)
    outliers = run_outlier_sensitivity(panel)
    within = _within_panel_persistence(panel)
    quadrant = summarize_quadrant_context(panel)
    quadrant_panel = _quadrant_panel_context(panel)
    quadrant_sectors, quadrant_years = _quadrant_composition(panel)
    outputs = {
        "a5_pairwise_relationships.csv": pairs,
        "a5_correlation_pearson.csv": pearson.reset_index(names="variable"),
        "a5_correlation_spearman.csv": spearman.reset_index(names="variable"),
        "a5_correlation_pairs_pearson.csv": pairs.loc[(pairs.method == "pearson") & (pairs.sample_grain == "msa_sector_year_pooled")],
        "a5_correlation_pairs_spearman.csv": pairs.loc[(pairs.method == "spearman") & (pairs.sample_grain == "msa_sector_year_pooled")],
        "a5_sector_relationships.csv": sectors,
        "a5_lag_relationships.csv": lags,
        "a5_regression_coefficients.csv": regressions,
        "a5_regression_summary.csv": models,
        "a5_sensitivity_summary.csv": pd.concat([covid, outliers], ignore_index=True, sort=False),
        "a5_within_panel_persistence.csv": within,
        "a5_quadrant_context.csv": quadrant_panel,
        "a5_quadrant_msa_year_context.csv": quadrant,
        "a5_quadrant_sector_composition.csv": quadrant_sectors,
        "a5_quadrant_year_composition.csv": quadrant_years,
        "a5_regional_msa_year_relationships.csv": pairs.loc[pairs.sample_grain == "msa_year_means_across_sectors"],
    }
    for filename, table in outputs.items():
        table.to_csv(TABLES / filename, index=False, float_format="%.8g")
    figures = _figures(panel, pearson, sectors, covid)
    _write_report(panel, pairs, regressions, models, sectors, lags, covid, outliers,
                  within, quadrant, quadrant_sectors, quadrant_years, figures)
    return {"rows": len(panel), "pairwise_relationships": len(pairs), "sectors": len(sectors),
            "models": models.model.tolist(), "tables": list(outputs), "figures": figures,
            "report": str(REPORT)}


if __name__ == "__main__":
    print(run_relationships())
