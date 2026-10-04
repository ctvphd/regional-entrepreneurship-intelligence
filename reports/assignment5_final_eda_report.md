# Assignment 5 Final EDA Report

## Executive Summary

The final Assignment 4 analytical panel contains **63,577 MSA-sector-year observations** from **381 metropolitan areas**, **19 sectors**, and **2010-2023**. Startup rates are centered near 6.3%, while employment growth is highly heavy-tailed. The pooled growth-startup association is positive but weak (Pearson 0.099; Spearman 0.193); sector and year context matter, and much pooled startup persistence reflects stable panel differences rather than within-panel momentum. Missing support and unstable growth denominators warrant careful validation in later modeling. No formal gap target, expected entrepreneurship, future label, or model was created.

## Data and Scope

The unit is an MSA x NAICS sector x year. The EDA uses the final Assignment 4 view `analytics_msa_industry_year`, metropolitan-only, over 2010-2023. The full panel has 5,887 observed MSA-sector panels: 2,830 are balanced over all 14 years and 3,057 are unbalanced. All 19 sectors and all 14 years are retained.

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
