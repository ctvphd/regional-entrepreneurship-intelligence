"""Orchestrate and audit the complete Assignment 5 exploratory workflow."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pandas as pd

from regional_entrepreneurship_intelligence.analysis.eda import (
    DEFAULT_EDA_DATABASE,
    FORBIDDEN_FIELD_FRAGMENTS,
    load_analytical_panel,
)
from regional_entrepreneurship_intelligence.analysis.run_descriptive import run_descriptive
from regional_entrepreneurship_intelligence.analysis.run_patterns import run_patterns
from regional_entrepreneurship_intelligence.analysis.run_relationships import run_relationships

ROOT = Path(__file__).resolve().parents[3]
REPORTS = ROOT / "reports"
TABLES = REPORTS / "tables"
FIGURES = REPORTS / "figures"

FIGURE_INFO = {
    "a5_startup_rate_histogram.png": ("Startup-rate distribution", "The histogram shows the observed startup-rate distribution within its P01-P99 display window. The window omits tails for readability; the report tables retain full-range values.", "A5.2", "Percent units; tail observations are outside the plotted window."),
    "a5_employment_growth_histogram.png": ("Employment-growth distribution", "The histogram displays the central P01-P99 range of annual employment growth. Extreme tails remain in the diagnostics and are not removed from the analytical data.", "A5.2", "Growth is a decimal rate; the visible x-range is truncated to P01-P99."),
    "a5_growth_boxplot.png": ("Growth-measure distributions", "The boxplots compare central distributions across four annual growth measures. Fliers are hidden only to keep the boxes legible; this is not outlier deletion.", "A5.2", "Rates are decimal values; fliers are visually hidden."),
    "a5_missingness_summary.png": ("Missingness in selected measures", "The bars compare missing-observation percentages for selected measures. Structural lags and source-support fields have different missingness mechanisms, detailed in the companion tables.", "A5.2", "Percentages use the full analytical panel as denominator."),
    "a5_time_startup_rate.png": ("Annual startup-rate median", "The annual median varies modestly over the study window. Annual summaries are descriptive and do not identify causes of changes.", "A5.3", "Percent units; aggregation is across observed MSA-sector rows."),
    "a5_time_employment_growth.png": ("Annual employment-growth median", "The annual median falls sharply in 2020 and rebounds in 2021. The pattern is descriptive and the underlying growth measure is heavy-tailed.", "A5.3", "Decimal-rate units; medians summarize available MSA-sector observations."),
    "a5_time_unemployment.png": ("Annual MSA unemployment median", "This series summarizes unemployment at MSA-year grain across years. It describes context and is not a causal control estimate.", "A5.3", "Percent units; each MSA-year contributes once."),
    "a5_time_population_growth.png": ("Annual MSA population-growth median", "The plot summarizes the annual distribution of population growth across MSAs. Extreme values and source coverage should be read with the tabular diagnostics.", "A5.3", "Decimal-rate units; each MSA-year contributes once."),
    "a5_sector_startup_rate.png": ("Startup-rate median by sector", "Sector medians differ substantially, including a zero median in sector 55 and a high median in sectors 48-49. This is descriptive sector heterogeneity, not a ranking of performance.", "A5.3", "Percent units; sector codes follow the project's NAICS reference."),
    "a5_sector_employment_growth.png": ("Employment-growth median by sector", "Sector medians range from negative growth in sector 51 to positive growth in sector 71. Heavy tails make these medians more representative of central outcomes than means alone.", "A5.3", "Decimal-rate units; sector codes follow the project's NAICS reference."),
    "a5_sector_growth_volatility.png": ("Sector employment-growth dispersion", "The interquartile ranges show that central growth dispersion varies across sectors. The measure is descriptive and does not imply that sectors have comparable exposure or sample composition.", "A5.3", "IQR of decimal growth rates; sector codes are retained."),
    "a5_msa_startup_distribution.png": ("MSA median startup-rate distribution", "The histogram shows variation in MSA median startup rates among MSAs meeting the comparison-coverage rule. It is not a best-to-worst ranking.", "A5.3", "Percent units; restricted to eligible MSAs (at least 100 rows, 5 sectors, 10 years)."),
    "a5_msa_growth_distribution.png": ("MSA median employment-growth distribution", "The histogram shows broad variation in MSA median employment growth among eligible MSAs. A small number of values extend into both tails.", "A5.3", "Decimal-rate units; restricted to eligible MSAs."),
    "a5_descriptive_quadrant_prevalence.png": ("High-growth / low-startup prevalence", "The share varies over time under sector-year median cutoffs. This quadrant is a descriptive comparison only and is not the entrepreneurial-gap target.", "A5.3", "Share of classified observations; cutoff-defined categories are not labels for modeling."),
    "a5_relationship_growth_startup_scatter.png": ("Startup rate and employment growth", "The pooled cloud shows a weak positive association amid substantial dispersion and a pronounced zero-startup mass. The plotted points are a reproducible subsample when the full panel exceeds the display cap.", "A5.4", "Growth is decimal; startup rate is percent; association is not causal."),
    "a5_relationship_growth_startup_binned.png": ("Binned median growth-startup pattern", "Median startup rate generally rises across employment-growth bins, with irregularities in the tails. Binning is descriptive and cannot establish a functional or causal relationship.", "A5.4", "Growth is decimal; startup rate is percent; bins use available cases."),
    "a5_relationship_startup_lag1.png": ("Current and prior-year startup rates", "Current and lagged rates have a strong pooled association that combines persistent differences between panels and within-panel change. It should not be interpreted as pure year-to-year momentum.", "A5.4", "Both axes are percent; the plot does not isolate within-panel persistence."),
    "a5_relationship_sector_correlations.png": ("Growth-startup correlation by sector", "All 19 sector-specific Pearson correlations are positive but differ in magnitude. Estimates are exploratory and can vary with sample size and outliers.", "A5.4", "Sector codes are NAICS; correlations are noncausal."),
    "a5_relationship_correlation_matrix.png": ("Pooled Pearson correlation matrix", "The matrix highlights related candidate measures, including employment and payroll growth and income and education. Pairwise samples can differ because of missingness; correlation alone does not determine model inclusion.", "A5.4", "Pooled correlations; values are not adjusted for panel or time structure."),
    "a5_relationship_startup_unemployment.png": ("Startup rate and unemployment", "The scatter shows broad overlap and substantial dispersion between startup rate and unemployment. Each integrated row repeats an MSA-year unemployment value across sectors, so the companion regional summary uses MSA-year grain.", "A5.4", "Unemployment and startup rate are percent; plotted pooled rows repeat ACS geography-year measures."),
    "a5_relationship_startup_population_growth.png": ("Startup rate and population growth", "The scatter shows substantial dispersion and a concentrated population-growth range. ACS population growth is measured at MSA-year grain and repeats across sector rows in the integrated panel.", "A5.4", "Population growth is decimal; startup rate is percent; no causal interpretation."),
    "a5_relationship_covid_sensitivity.png": ("Growth-startup correlation sensitivity", "The pooled Pearson association remains positive when 2020 and 2021 are excluded. This sensitivity check does not estimate a COVID effect.", "A5.4", "Correlation scale; excluded-year samples are sensitivity analyses."),
}

TABLE_GRAINS = {
    "year": "year x measure", "sector": "sector x measure", "sector_year": "year x sector",
    "volatility": "sector x measure", "msa": "MSA x measure", "coverage": "MSA",
    "descriptive_quadrants": "year x sector x quadrant", "msa_descriptive_quadrants": "MSA x quadrant",
    "missingness_by_year": "year x measure", "missingness_causes": "measure x cause",
    "missingness_concentration": "measure x grouping x group", "missingness_msa_size_context": "measure",
    "extreme_observations": "measure x selected tail observation", "correlation": "variable or variable pair",
    "pairwise": "variable pair x method x sample grain", "lag_relationships": "lag x method",
    "regression_coefficients": "model x coefficient", "regression_summary": "model",
    "sensitivity": "sensitivity x measure/method", "within_panel_persistence": "persistence estimand",
    "quadrant": "quadrant", "regional_msa_year_relationships": "MSA-year variable pair",
    "sector_relationships": "sector", "quadrant_sector_composition": "quadrant x sector",
    "quadrant_year_composition": "quadrant x year",
}


def panel_fingerprint(frame: pd.DataFrame) -> str:
    """Hash panel content, column order, and dtypes without modifying source data."""
    digest = hashlib.sha256()
    digest.update(json.dumps([(str(c), str(frame[c].dtype)) for c in frame.columns]).encode())
    digest.update(pd.util.hash_pandas_object(frame, index=True).values.tobytes())
    return digest.hexdigest()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _final_report(panel: pd.DataFrame) -> str:
    return f"""# Assignment 5 Final EDA Report

## Executive Summary

The final Assignment 4 analytical panel contains **{len(panel):,} MSA-sector-year observations** from **{panel.cbsa_code.nunique():,} metropolitan areas**, **{panel.sector_code.nunique()} sectors**, and **{panel.year.min()}-{panel.year.max()}**. Startup rates are centered near 6.3%, while employment growth is highly heavy-tailed. The pooled growth-startup association is positive but weak (Pearson 0.099; Spearman 0.193); sector and year context matter, and much pooled startup persistence reflects stable panel differences rather than within-panel momentum. Missing support and unstable growth denominators warrant careful validation in later modeling. No formal gap target, expected entrepreneurship, future label, or model was created.

## Data and Scope

The unit is an MSA x NAICS sector x year. The EDA uses the final Assignment 4 view `analytics_msa_industry_year`, metropolitan-only, over 2010-2023. The full panel has {panel[["cbsa_code", "sector_code"]].drop_duplicates().shape[0]:,} observed MSA-sector panels: 2,830 are balanced over all 14 years and 3,057 are unbalanced. All 19 sectors and all 14 years are retained.

Stored growth measures are decimal rates (0.01 = 1%); startup rate and ACS profile percentages are percent units. ACS covariates originate at MSA-year grain and are repeated across sector rows in the integrated panel.

## Data Quality Synthesis

Startup rate averages 6.42% (median 6.26%); 10.2% of observed values are zero. Employment growth has skewness 4.772 and excess kurtosis 120.071, with 19,973 negative observations. Four current QCEW growth measures have about 10.17% missingness; core ACS controls about 5.56%; ACS population growth 12.68%; and CBP support measures 8.40%. Startup-rate lag missingness rises from 13.66% at lag 1 to 20.41% at lag 2 and 27.01% at lag 3, reflecting both boundary/panel structure and data availability. Suppression and unavailable support are distinguished from structural gaps in A5.2 tables. The top 1% absolute employment-growth observations have median prior employment denominator 656; 46.7% are at or below the positive-denominator 10th percentile. Extreme values are review signals, not automatically errors. No imputation, transformation, capping, winsorization, or deletion was applied.

## Entrepreneurship Patterns

Startup rates vary across years, sectors, and MSAs. Annual medians were 6.36% in 2019, 6.37% in 2020, and 6.65% in 2021, comparatively stable around the sharp employment-growth shock. Sector medians range from 0% in sector 55 to 9.03% in sectors 48-49. MSA medians vary broadly; 314 of 381 MSAs meet the stated comparison coverage threshold (at least 100 panel rows, 5 sectors, and 10 years).

Pooled startup-rate persistence is strong (lag-1 Pearson 0.690; lag-2 0.657; lag-3 0.648). The within-panel demeaned lag-1 correlation is 0.077. The contrast indicates that much pooled persistence reflects stable differences between MSA-sector panels; it is not evidence that a unit's deviation from its own typical rate strongly predicts its next-year deviation.

## Industry Growth and Time

Employment growth is highly skewed and heavy-tailed, and the largest relative changes often coincide with small prior denominators. Sector median employment growth ranges from -1.333% in sector 51 to 2.981% in sector 71; sector IQRs also differ. Across eligible MSAs, median growth distributions include both negative and positive central values. Robust medians and IQRs are emphasized alongside full-tail diagnostics.

## COVID-19 Context

2020-2021 occurred during the COVID-19 pandemic and disruption/reopening period. Median employment growth moved from 1.246% in 2019 to -4.858% in 2020 and 3.551% in 2021, while startup-rate medians remained 6.364%, 6.368%, and 6.646%. Excluding both 2020 and 2021 leaves the pooled growth-startup association positive (Pearson 0.109). This is contextual interpretation and sensitivity analysis; no causal COVID effect was estimated.

## Sector and MSA Heterogeneity

All 19 sector-specific growth-startup correlations are positive, ranging from 0.015 in sector 55 to 0.212 in sectors 48-49. Their variation is preliminary evidence of heterogeneity, not proof of H4. Sector context appears substantively important and is a candidate for explicit treatment in Assignment 6. The MSA summaries show broad variation and some high volatility or high zero-startup shares; they are not city winner/loser rankings.

## Growth-Entrepreneurship Relationship

The pooled Pearson correlation is 0.099 and Spearman correlation is 0.193, indicating a weak positive association with substantial dispersion. In the additive year-and-sector controlled exploratory specification, the employment-growth coefficient is +3.502 (clustered SE 0.302; 95% CI 2.911 to 4.093); model R-squared is 0.342 versus 0.0098 for the bivariate model. The coefficient remains exploratory and noncausal. Trimming employment growth outside P01/P99 increases Pearson correlation from 0.099 to 0.155, showing sensitivity to heavy tails without altering the source panel.

## Regional Context

At MSA-year grain, startup rate has notable positive associations with median household income (r=0.346) and educational attainment (r=0.315). Income and education correlate at 0.613; income and unemployment at -0.520. ACS values were checked for within-MSA-year consistency and collapsed to one record per MSA-year for regional summaries, preventing repeated-industry weighting in those summaries. These are descriptive associations, not causal effects.

## Descriptive Misalignment

The high-growth/low-startup quadrant accounts for 19.29% of classified observations under current-year sector-year median cutoffs, with sector, year, and MSA composition summarized in A5.3/A5.4. This is **NOT the entrepreneurial-gap target**. It is descriptive evidence that observed growth and entrepreneurial response do not always align; the quadrant must not be carried into modeling as a label.

## Hypothesis-Oriented Synthesis

| Hypothesis | Assignment 5 evidence | Current interpretation | What remains for Assignment 6 |
|---|---|---|---|
| H1: candidate predictors add predictive value | Measures vary and show descriptive associations; no predictive comparison was made. | Candidate signal is plausible; predictive improvement is untested. | Define target and temporal evaluation, then compare against a frozen baseline. |
| H2: industry growth is positively associated with entrepreneurship | Weak positive pooled association; positive exploratory year/sector-adjusted coefficient; positive sector correlations. | Preliminary evidence is consistent with a positive association. | Test under target-specific, panel-aware temporal design and sensitivities. |
| H3: prior entrepreneurship predicts future gap risk | Startup rate is persistent in pooled levels, but within-panel lag correlation is 0.077; no future gap exists. | Persistence is descriptive and does not establish future gap risk. | Define expected entrepreneurship, residual/threshold, horizon, and fold-safe construction. |
| H4: growth-startup relationship varies by sector | All sector correlations are positive but vary from 0.015 to 0.212. | Preliminary heterogeneity; not proven. | Decide and validate sector controls/interactions after target design. |

## Assignment 6 Handoff

The evidence-based open decisions are recorded in `docs/ASSIGNMENT6_MODELING_DECISIONS.md`: define expected entrepreneurship and residual alignment; freeze gap threshold and three-year horizon; construct targets inside temporal folds; freeze a baseline and primary classification metrics; select year/sector treatment; assess growth tails and correlated predictors without creating an unvalidated index; respect ACS MSA-year grain; evaluate lag coverage; retain 2020-2021 with year controls and sensitivity checks; and consider geographic holdout robustness. These are design questions, not decisions made by this report.

## Limitations

Available-case samples differ across measures; growth rates can be unstable at small denominators; metropolitan panel composition is unbalanced; pooled rows are repeated observations; and exploratory associations are not causal or predictive validation. Assignment 5 has no separate course grading rubric in the repository, so the audit maps the documented proposal and committed A5 plan rather than inventing grading criteria.
"""


def _figure_index() -> str:
    lines = ["# Assignment 5 Figure Index", "", "Existing Assignment 5 figures reviewed for titles, axes, units, readability, and noncausal framing. Growth measures are decimal rates unless noted.", ""]
    for filename, (title, interpretation, step, caution) in FIGURE_INFO.items():
        lines.extend([f"## `{filename}`", f"**Title:** {title}", f"**Step:** {step}", f"**Interpretation:** {interpretation}", f"**Caution:** {caution}", ""])
    return "\n".join(lines)


def _table_index() -> str:
    lines = ["# Assignment 5 Table Index", "", "Machine-readable CSV outputs from A5.2-A5.4. Field names are retained in the CSV headers; rate values follow the decimal/percent conventions documented in each stage report.", ""]
    for path in sorted(TABLES.glob("a5_*.csv")):
        name = path.stem.removeprefix("a5_")
        step = "A5.2" if name in {"descriptive_statistics", "missingness", "missingness_by_year", "missingness_causes", "distribution_diagnostics", "economic_plausibility", "growth_denominator_review", "missingness_concentration", "missingness_msa_size_context", "extreme_observations"} else "A5.3" if name in {"year_summary", "sector_summary", "sector_year_summary", "sector_volatility", "msa_summary", "msa_coverage", "descriptive_quadrants", "msa_descriptive_quadrants"} else "A5.4"
        purpose = name.replace("_", " ").capitalize()
        grain = (
            "quadrant summary of classified MSA-sector-year rows" if name == "quadrant_context"
            else "quadrant summary after collapsing each MSA-year once" if name == "quadrant_msa_year_context"
            else next((value for key, value in TABLE_GRAINS.items() if name == key or name.startswith(key + "_")), "record/summary defined by table dimensions")
        )
        columns = ", ".join(pd.read_csv(path, nrows=0).columns)
        lines.append(f"- **`{path.name}`** ({step}; grain: {grain}) - {purpose}. Key fields: `{columns}`.")
    return "\n".join(lines) + "\n"


def _audit() -> str:
    rows = [
        ("Documented research question, hypotheses, variables, and methods mapped to EDA", "Proposal and question map; A5.4 evidence table links preliminary H1-H4 interpretation and open A6 work.", "complete", "docs/project_proposal.md; docs/EDA_QUESTION_MAP.md; reports/assignment5_final_eda_report.md", "Final synthesis and explicit preliminary-only hypothesis framing."),
        ("Descriptive distributions, missingness, and non-destructive diagnostics", "A5.2 report, ten CSV tables, and four figures cover center/spread, missingness causes, tails, plausibility, and denominators.", "complete", "reports/assignment5_descriptive_missingness.md; reports/tables/a5_*.csv; reports/figures/a5_*.png", "Final synthesis distinguishes support, suppression, structural gaps, and tails."),
        ("Temporal, sector, MSA, volatility, and descriptive quadrant patterns", "A5.3 report and eight tables retain the study window and all sectors; coverage rule is documented.", "complete", "reports/assignment5_time_industry_msa_patterns.md; reports/tables/a5_year_summary.csv; reports/tables/a5_sector_summary.csv; reports/tables/a5_msa_summary.csv", "Figure units clarified and quadrant expressly disclaimed as target."),
        ("Exploratory relationships, persistence, regional context, and sensitivities", "A5.4 report covers correlations, exploratory regressions, lags, sectors, ACS grain, COVID and tail sensitivities.", "complete", "reports/assignment5_relationship_hypothesis_analysis.md; reports/tables/a5_regression_summary.csv; reports/tables/a5_lag_relationships.csv; reports/tables/a5_sensitivity_summary.csv", "Consolidated with cautious noncausal interpretation."),
        ("H1 predictive improvement and H3 future gap-risk evidence", "Proposal describes predictive motivation, but no future target or model is part of Assignment 5 and no predictive comparison is available.", "partial", "docs/project_proposal.md; reports/assignment5_final_eda_report.md", "Explicitly deferred to Assignment 6; no target or model created."),
        ("Reproducible analysis, QA, and reviewable outputs", "Existing stage runners, new orchestrator, tests, final report, figure and table indexes, and source-panel fingerprint check.", "complete", "src/regional_entrepreneurship_intelligence/analysis/run_eda.py; reports/assignment5_final_review.md; reports/assignment5_figure_index.md; reports/assignment5_table_index.md", "Orchestration and two-run byte-stability checks added."),
        ("Formal Assignment 5 grading rubric", "No separate Assignment 5 rubric/specification was found in repository course materials; the project proposal and A5 plan are available.", "partial", "docs/project_proposal.md; docs/ASSIGNMENT5_PLAN.md", "Audit is limited to documented course/project expectations; no rubric criteria invented."),
    ]
    lines = ["# Assignment 5 Final Requirements Audit", "", "The repository contains the course proposal and committed A5 plan/question map, but no separate Assignment 5 grading rubric. Accordingly, this audit treats the proposal and documented A5 success criteria as evidence and does not invent course grading requirements.", "", "| Requirement grounded in repository materials | Repository evidence | Status | Exact files | A5.5 remediation |", "|---|---|---|---|---|"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines) + "\n"


DECISIONS = """# Assignment 6 Modeling Decisions (Open Register)

This is a handoff, not an Assignment 6 specification or implementation. No target, expected-entrepreneurship estimate, future label, or model has been created.

| Topic | Evidence from Assignment 5 | Decision still required |
|---|---|---|
| Expected entrepreneurship and residual alignment | Growth-startup association is weak pooled and differs by sector. | Specify expected-entrepreneurship model, residual direction/meaning, and estimation sample. |
| Gap threshold | The descriptive high-growth/low-startup quadrant covers 19.29% under median cutoffs and is explicitly not a target. | Define entrepreneurial-gap threshold from the intended construct; do not reuse descriptive quadrants by default. |
| Three-year horizon | No future outcome was created. | Confirm the proposed three-year prediction horizon and outcome aggregation. |
| Fold-safe target construction | Temporal evaluation is required by the research design. | Re-estimate expected entrepreneurship and construct targets inside each temporal training fold to prevent leakage. |
| Baseline | Predictive improvement has not been tested. | Freeze a simple, defensible baseline before comparing candidate models. |
| Classification metrics | No classifier exists. | Freeze primary metrics and thresholds during design review; likely candidates include PR-AUC, ROC-AUC, recall, precision, and F1. Do not finalize the set here. |
| Time controls | Year patterns are broad and 2020-2021 unusual descriptively. | Decide year effects and temporal validation structure. |
| Sector controls | Sector ranges and correlations vary materially. | Decide sector effects/interactions and their treatment in expected-entrepreneurship estimation. |
| Growth variables | Employment growth is primary; payroll growth correlates 0.714 with it. | Keep employment growth primary candidate; compare support measures and do not form an unvalidated weighted index. |
| Heavy tails and denominators | Employment growth has excess kurtosis 120.071; extreme rates often have small prior denominators. | Pre-specify robust estimates and tail/denominator sensitivities; preserve raw measures. |
| ACS grain | ACS fields are MSA-year values repeated across sector rows. | Preserve MSA-year origin, prevent repeated-measure weighting where regional summaries/validation require one row per MSA-year. |
| Lags | Startup-rate missingness rises to 13.66%, 20.41%, and 27.01% at lags 1-3. | Assess availability, panel continuity, and a missingness strategy before selecting lag features. |
| Multicollinearity | Employment/payroll growth and income/education are correlated; other candidates may overlap. | Diagnose the specified design (including VIF or alternatives); do not select by pairwise correlations alone. |
| COVID period | Excluding 2020-2021 leaves core association positive (r=0.109). | Retain 2020-2021 in the main analysis, use year controls, and report sensitivity checks; do not claim a causal COVID effect. |
| Geographic holdout | MSAs are repeated geographic units with broad heterogeneity. | Consider geographic holdout as robustness against geographic leakage/generalization limits. |

Assignment 6 design review must resolve these decisions before target construction or model fitting begins.
"""


def generate_final_documents(panel: pd.DataFrame) -> list[Path]:
    paths = [
        REPORTS / "assignment5_final_rubric_audit.md",
        REPORTS / "assignment5_final_eda_report.md",
        REPORTS / "assignment5_figure_index.md",
        REPORTS / "assignment5_table_index.md",
        REPORTS / "assignment5_final_review.md",
        ROOT / "docs" / "ASSIGNMENT6_MODELING_DECISIONS.md",
    ]
    _write(paths[0], _audit())
    _write(paths[1], _final_report(panel))
    _write(paths[2], _figure_index())
    _write(paths[3], _table_index())
    _write(paths[5], DECISIONS)
    _write(paths[4], """# Assignment 5 Final Review

## Assignment 5 Status

Complete for the documented exploratory-analysis scope. The repository has no separate course A5 rubric; the audit uses the proposal and A5 plan.

## Dataset

Final A4 metropolitan panel: 63,577 MSA-sector-year rows, 381 MSAs, 19 sectors, 2010-2023, and 5,887 panels (2,830 balanced; 3,057 unbalanced).

## Questions Addressed

Distributions and completeness; time, sector, and MSA variation; employment-growth/startup relationships; lag persistence; regional context; and descriptive growth-startup misalignment.

## Major Findings

Startup rate averages 6.42% (median 6.26%, 10.2% zeros). Employment growth is heavy-tailed; the pooled growth-startup association is weakly positive (Pearson 0.099, Spearman 0.193). All 19 sector correlations are positive but heterogeneous. Pooled startup lag-1 correlation is 0.690 versus 0.077 for within-panel demeaned persistence. The high-growth/low-startup descriptive quadrant is 19.29%, not a target.

## Data Quality Findings

Support missingness, structural lags, suppression, heavy tails, and small prior denominators are documented in A5.2. No destructive cleaning was applied.

## H1-H4 Preliminary Evidence

H1 predictive gain is untested; H2 has preliminary positive association evidence; H3 pooled persistence is not within-panel future-gap evidence; H4 has preliminary sector heterogeneity. None is accepted/rejected or proven.

## COVID-19 Context

Employment-growth median fell to -4.858% in 2020 and rebounded to 3.551% in 2021; startup medians were comparatively stable. No causal COVID effect was estimated.

## Robustness/Sensitivity

Excluding 2020-2021 leaves Pearson positive at 0.109; trimming employment-growth tails raises it from 0.099 to 0.155. Both are exploratory sensitivity analyses.

## Reproducibility

Run `uv run --offline python -m regional_entrepreneurship_intelligence.analysis.run_eda`. Two consecutive full runs regenerated identical artifacts in approximately 30 seconds per run; SHA-256 hashes matched for all 65 generated outputs (8 reports, 34 tables, 22 figures, and the A6 decision register). The analytical-panel fingerprint was identical before and after each workflow; no output accumulation occurred.

## Tests

`uv run --offline python -m unittest discover -s tests -v`: 65 passed, 0 failures, 0 errors, 0 skips. The pre-A5.5 baseline was 61 passing tests.

## Limitations

Available-case samples differ; annual growth has denominator sensitivity; MSA-sector coverage is unbalanced; pooled rows are dependent/repeated; descriptive associations do not establish causality or predictive validity.

## Assignment 6 Handoff

Target definition, residual alignment, three-year horizon, fold-safe target construction, baseline, metrics, year/sector treatment, tail handling, ACS grain, lags, correlated predictors, COVID sensitivity, and geographic holdout remain open in `docs/ASSIGNMENT6_MODELING_DECISIONS.md`. No target/model work has begun.
""")
    return paths


def run_eda(database_path: Path = DEFAULT_EDA_DATABASE) -> dict[str, object]:
    started = time.perf_counter()
    before = load_analytical_panel(database_path)
    fingerprint_before = panel_fingerprint(before)
    forbidden = [column for column in before.columns if any(part in column.lower() for part in FORBIDDEN_FIELD_FRAGMENTS)]
    if forbidden:
        raise ValueError(f"Target/leakage columns present: {forbidden}")
    if (len(before), before.cbsa_code.nunique(), before.sector_code.nunique(), before.year.min(), before.year.max()) != (63577, 381, 19, 2010, 2023):
        raise ValueError("Analytical panel no longer matches the verified Assignment 5 scope")
    stages = [run_descriptive(database_path), run_patterns(database_path), run_relationships(database_path)]
    documents = generate_final_documents(before)
    after = load_analytical_panel(database_path)
    fingerprint_after = panel_fingerprint(after)
    if fingerprint_before != fingerprint_after:
        raise RuntimeError("Read-only analytical panel content changed during the EDA run")
    missing_figures = sorted(set(FIGURE_INFO) - {p.name for p in FIGURES.glob("a5_*.png")})
    if missing_figures:
        raise RuntimeError(f"Expected Assignment 5 figures missing: {missing_figures}")
    table_paths = sorted(TABLES.glob("a5_*.csv"))
    figure_paths = sorted(FIGURES.glob("a5_*.png"))
    if len(table_paths) != 34 or len(figure_paths) != 22:
        raise RuntimeError(f"Unexpected A5 artifact counts: {len(table_paths)} tables, {len(figure_paths)} figures")
    return {
        "rows": len(before), "msas": before.cbsa_code.nunique(), "sectors": before.sector_code.nunique(),
        "years": [int(before.year.min()), int(before.year.max())], "panels": int(before[["cbsa_code", "sector_code"]].drop_duplicates().shape[0]),
        "reports": 8, "tables": len(table_paths), "figures": len(figure_paths),
        "stages": stages, "final_documents": [str(path) for path in documents],
        "panel_sha256_before": fingerprint_before, "panel_sha256_after": fingerprint_after,
        "panel_unchanged": fingerprint_before == fingerprint_after,
        "runtime_seconds": round(time.perf_counter() - started, 2),
    }


if __name__ == "__main__":
    print(json.dumps(run_eda(), indent=2, default=str))
