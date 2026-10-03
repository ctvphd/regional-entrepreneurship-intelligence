# Assignment 5 Plan: Exploratory Data Analysis

## Purpose

Assignment 5 will document the canonical Assignment 4 panel before any target construction or modeling. A5.1 defines the questions, variables, methods, and reusable foundation. It does not perform the full EDA.

## Research Question

**Can historical industry growth, entrepreneurial activity, labor-market conditions, and regional economic characteristics predict whether entrepreneurial activity within an MSA-industry combination will fall below its expected level over the subsequent three years?**

Assignment 5 examines the historical variables and descriptive relationships underlying that question; it does not answer its predictive claim.

## Unit of Analysis

One MSA x 2-digit NAICS industry x year, keyed by `geography_id + industry_id + year`. ACS controls originate at MSA-year grain and intentionally repeat across matched industries.

## Study Period

2010-2023 inclusive. Do not extend the panel during Assignment 5.

## EDA Questions

1. How does entrepreneurial activity vary across MSAs, industries, and time?
2. How does industry growth vary across MSAs, industries, and time?
3. How are industry growth and entrepreneurial activity associated descriptively?
4. How do regional economic conditions relate to entrepreneurship and industry growth?
5. Does the growth-entrepreneurship relationship appear to vary across sectors?
6. Where does strong industry growth coexist with relatively weak startup activity?

See `docs/EDA_QUESTION_MAP.md` for each question's research/hypothesis connection, variables, summaries, visuals, modeling relevance, and cautions.

## Hypothesis Mapping

- **H1:** inspect distributions, missingness, predictor relationships, plausible signal, and transformations; do not compare predictive performance.
- **H2:** describe historical growth-startup relationships overall, over time, and by sector; no causal or formal hypothesis claim.
- **H3:** describe startup-rate persistence and historical lag behavior; do not create future gaps or test future likelihood.
- **H4:** compare descriptive sector distributions and sector-specific relationships; do not fit the final interaction model.

## Variable Tiers

- **Tier 1, core:** `startup_rate`, `employment_growth`, year, sector, MSA, population growth, unemployment, education, and income.
- **Tier 2, supporting:** other QCEW levels/growth/lags; startup counts, entry measures and job creation; labor-force participation; and CBP measures for validation/context.
- **Tier 3, diagnostic/quality:** source suppression, availability, match, missing-control, and county-coverage flags; source-quality notes. Keys and display labels identify/group records but are not substantive measures.

The authoritative field-level assignments are in `docs/EDA_VARIABLE_INVENTORY.md` and `analysis.eda.VARIABLE_GROUPS`.

## Planned Descriptive Statistics

Report usable N and missing N alongside means, standard deviations, medians, IQRs, selected percentiles, and ranges where meaningful. Summarize overall and by year, sector, and MSA. Include missingness counts/percentages overall and by year/sector, and by MSA where it is analytically interpretable. Use Pearson correlations for approximately linear relationships and Spearman correlations as a rank-based sensitivity summary; report sample sizes. Grouped comparisons are descriptive. Use a bivariate regression only if a clearly stated summary question warrants it, and label it non-causal.

## Planned Visualizations

Use a restrained set tied to the six questions: startup and growth distributions; annual trend plots; sector distributions/trends; selected growth-startup scatterplots; regional-control relationships; and an explicitly descriptive quadrant plot. Consider a correlation heatmap only if it remains readable and handles missing samples transparently. Avoid redundant plots and large chart batches.

## Missingness Strategy

Use Assignment 4 source/panel audits as the baseline. Report count, percentage, and sample size for every relevant summary. Available-case samples may differ by analysis and must be stated. Break missingness out by year and sector, and by MSA when useful. Distinguish structural missingness: initial growth observations lack a valid prior year; lag fields require calendar-contiguous history; ACS/CBP support can be unmatched or unavailable; suppression is not zero. Do not impute in A5.1 or interpret structural lag gaps as random missingness. Remember the integrated core conditions on accepted BDS startup rates; consult upstream staging and quality audits for source-level BDS availability.

## Outlier Strategy

Do not delete or overwrite extreme values. Inspect percentiles and distribution plots, and distinguish valid economic extremes from source errors, unstable denominators, suppression, or missingness using source documentation and audit fields. Log transformations may be considered for positive level measures, not assumed for rates that can be zero/negative. Robust summaries and later winsorized sensitivity analyses may be considered if evidence warrants; preserve raw values. Visual zooms may supplement, never replace, full-range displays.

## Panel-Data Considerations

Rows are repeated observations within MSA-industry panels; pooled correlations and ordinary grouped standard errors do not make them independent. Later EDA should distinguish cross-sectional, within-panel temporal, between-sector, and between-MSA variation. ACS is MSA-year and repeated across industries by construction. Descriptive pooled relationships are not inferential or causal evidence.

## Time Analysis

Describe annual startup-rate, employment-growth, and regional-control trends. Consider pre/post large macroeconomic disruptions as labeled descriptive partitions only. Do not make causal event-study claims or assume structural breaks without evidence. Respect actual calendar-year continuity in lag interpretation.

## Sector Analysis

Use all 19 common sectors unless a documented data-validity issue requires an explicit exception. Describe startup rate, employment growth, volatility, and their association by sector. Do not drop inconvenient sectors or estimate the final interaction model in this step.

## MSA Analysis

Describe the distributions of startup rates and employment growth across MSAs, MSA-year patterns, and industries represented per MSA. Identify possible high-growth/low-startup cases only as neutral descriptive observations. Do not label MSAs “best” or “worst.”

## Descriptive Misalignment Framework

For later visualization only, compare growth and startup activity using documented empirical cutoffs such as medians or quantiles. The four descriptive quadrants are high/high, high-growth/low-startup, low-growth/high-startup, and low/low. Sensitivity to cutoff choice should be visible. A quadrant is not the formal entrepreneurial-gap target, expected entrepreneurship, alignment residual, dependent variable, or canonical stored field; never carry it into Assignment 6 as a target.

## Reusable Code Structure

The modest A5.1 foundation is `src/regional_entrepreneurship_intelligence/analysis/eda.py`: read-only loader for `database/assignment4_production.sqlite`, required-field/leakage checks, study-year and metropolitan-scope checks, and variable-group constants. Later steps may add reusable descriptive, relationship, panel-summary, and plot functions in this package without over-fragmenting it. A5.1 calculates no descriptive results.

## Planned Reports

- `reports/assignment5_descriptive_summary.md`
- `reports/assignment5_relationships.md`
- `reports/assignment5_final_eda_report.md`

Future visual artifacts should follow repository policy and avoid committing generated bulk output without a deliberate decision. None are generated in A5.1.

## Success Criteria

1. The analytical panel is understood descriptively.
2. Missingness is documented.
3. Distributions are understood.
4. Temporal patterns are documented.
5. Sector heterogeneity is documented.
6. MSA heterogeneity is documented.
7. Entrepreneurship-growth relationships are explored.
8. Regional controls are contextualized.
9. Potential mismatch patterns are visible descriptively.
10. Assignment 6 modeling choices are informed by evidence rather than assumption.

These are Assignment 5 completion criteria, not outputs of A5.1 alone.

## EDA Decisions That May Affect Assignment 6

- Does startup rate require transformation?
- Are growth variables excessively skewed?
- Are extreme observations economically meaningful?
- Which industry-growth measure should be primary?
- Which regional controls appear redundant?
- Are predictor correlations high enough to create multicollinearity concerns?
- Are lags sufficiently populated?
- Are there strong sector differences?
- Are some years structurally unusual?
- Does missingness threaten temporal validation?
- Should geographic holdouts be stratified?

These questions remain open until later EDA evidence is available.

## Planned Assignment 5 Sequence

- A5.1 EDA Plan & Question Mapping
- A5.2 Descriptive Statistics & Missingness
- A5.3 Time, Industry & MSA Patterns
- A5.4 Relationship & Hypothesis-Oriented Analysis
- A5.5 EDA Report, Reusable Module & QA
