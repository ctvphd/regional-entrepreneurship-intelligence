# Assignment 5.2: Descriptive Statistics & Missingness

## Scope and Data

The A5.1 read-only loader returned **63,577** MSA-sector-year observations across **381 MSAs**, **19 sectors**, and **2010–2023**. There are no duplicate panel keys. The active view has 61 fields; all remain within the documented Assignment 4 scope.

This report covers overall distributions, completeness, concentration checks, and initial outlier/plausibility diagnostics. It does not analyze trends, sector-specific relationships, causal effects, predictive performance, expected entrepreneurship, or entrepreneurial-gap status.

Stored growth measures are decimal rates (for example, 0.015 is 1.5%); startup rate and ACS profile percentages are expressed in percent units. Income is retained in ACS release-adjusted dollars and is not deflated to a common year.

## What the Data Show

### Entrepreneurship

| Variable | N | Missing % | Mean | Median | P05 | P95 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `startup_rate` | 63,577 | 0.00 | 6.417 | 6.262 | 0.000 | 12.500 | 0.000 | 80.000 |
| `establishment_entry` | 61,128 | 3.85 | 107.974 | 27.000 | 0.000 | 438.000 | 0.000 | 8,675.000 |
| `establishment_entry_rate` | 61,128 | 3.85 | 9.431 | 9.091 | 0.000 | 16.865 | 0.000 | 133.333 |
| `firm_startups` | 63,577 | 0.00 | 66.500 | 15.000 | 0.000 | 256.000 | 0.000 | 5,621.000 |
| `startup_job_creation` | 63,577 | 0.00 | 340.870 | 63.000 | 0.000 | 1,332.000 | 0.000 | 45,270.000 |
| `startup_rate_lag1` | 54,894 | 13.66 | 6.507 | 6.335 | 0.000 | 12.323 | 0.000 | 62.903 |
| `startup_rate_lag2` | 50,599 | 20.41 | 6.426 | 6.250 | 0.000 | 12.169 | 0.000 | 62.903 |
| `startup_rate_lag3` | 46,406 | 27.01 | 6.387 | 6.215 | 0.000 | 12.077 | 0.000 | 75.000 |

Startup rate has skewness 1.179 and excess kurtosis 9.669; 6,475 observed values are zero (10.2%). This is a descriptive distribution summary, not a decision to transform the variable.

### Industry Growth

| Variable | N | Missing % | Mean | Median | P05 | P95 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `employment_growth` | 57,109 | 10.17 | 0.015 | 0.015 | -0.097 | 0.120 | -0.850 | 3.448 |
| `average_pay_growth_lag1` | 51,409 | 19.14 | 0.038 | 0.033 | -0.034 | 0.119 | -0.728 | 6.578 |
| `employment_growth_lag1` | 51,409 | 19.14 | 0.015 | 0.015 | -0.099 | 0.121 | -0.837 | 6.156 |
| `employment_growth_lag2` | 46,687 | 26.57 | 0.012 | 0.013 | -0.103 | 0.115 | -0.850 | 6.156 |
| `employment_growth_lag3` | 42,178 | 33.66 | 0.009 | 0.011 | -0.107 | 0.106 | -0.850 | 3.673 |
| `establishment_growth` | 57,109 | 10.17 | 0.020 | 0.012 | -0.054 | 0.104 | -0.953 | 15.950 |
| `establishment_growth_lag1` | 51,409 | 19.14 | 0.019 | 0.011 | -0.054 | 0.101 | -0.953 | 15.950 |
| `establishment_growth_lag2` | 46,687 | 26.57 | 0.017 | 0.009 | -0.057 | 0.096 | -0.953 | 15.950 |
| `establishment_growth_lag3` | 42,178 | 33.66 | 0.016 | 0.008 | -0.058 | 0.092 | -0.953 | 15.950 |
| `payroll_growth` | 57,109 | 10.17 | 0.053 | 0.048 | -0.080 | 0.193 | -0.824 | 14.934 |
| `payroll_growth_lag1` | 51,409 | 19.14 | 0.053 | 0.047 | -0.083 | 0.195 | -0.849 | 14.934 |
| `wage_growth` | 57,109 | 10.17 | 0.038 | 0.034 | -0.034 | 0.118 | -0.728 | 6.578 |

Employment growth skewness is 4.772 with excess kurtosis 120.071. The distribution includes 19,973 negative observations and 315 exact zeros. Negative growth is economically possible.

### Regional Context

| Variable | N | Missing % | Mean | Median | P05 | P95 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `acs_population_growth` | 55,515 | 12.68 | 0.008 | 0.006 | -0.007 | 0.026 | -0.695 | 2.017 |
| `unemployment_rate` | 60,039 | 5.56 | 7.144 | 6.700 | 3.700 | 12.200 | 2.100 | 18.500 |
| `educational_attainment_pct` | 60,039 | 5.56 | 27.871 | 26.700 | 16.100 | 44.300 | 11.800 | 63.900 |
| `median_household_income` | 60,039 | 5.56 | 57,131.843 | 54,392.000 | 40,894.000 | 82,099.000 | 31,264.000 | 157,444.000 |
| `labor_force_participation_pct` | 60,039 | 5.56 | 62.410 | 62.600 | 53.700 | 70.600 | 25.100 | 75.900 |

ACS control gaps are distinct from panel lags: income, education, participation, and unemployment each have 5.56% missingness, corresponding to unmatched ACS support rows in the integration flags. Income is not common-year deflated. ACS values repeat across sector rows at MSA-year grain and are not independent regional observations.

### Business Structure

| Variable | N | Missing % | Mean | Median | P05 | P95 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `cbp_annual_payroll` | 58,236 | 8.40 | 950,768.793 | 170,968.500 | 11,959.750 | 3,702,042.750 | 28.000 | 153,694,057.000 |
| `cbp_employment` | 58,236 | 8.40 | 17,775.838 | 4,436.500 | 303.000 | 73,926.750 | 2.000 | 1,804,859.000 |
| `cbp_establishments` | 58,236 | 8.40 | 1,169.791 | 340.000 | 21.000 | 4,730.250 | 3.000 | 77,063.000 |
| `cbp_first_quarter_payroll` | 58,236 | 8.40 | 239,841.529 | 40,404.500 | 2,807.000 | 921,130.000 | 13.000 | 63,992,253.000 |

CBP employment is missing in 8.40% of core panel rows. The source flags distinguish unmatched/incomplete aggregates from rows marked as suppressed; native CBP payroll units remain $1,000. CBP support missingness does not remove a BDS-QCEW core row.

## Missingness

Overall rates are in `reports/tables/a5_missingness.csv`; selected year-level rates are in `a5_missingness_by_year.csv`. The cause table is an auditable partition, not an imputation model.

- **Expected structural/unavailable:** 201,310 missing cells classified as outside the study-window predecessor or lacking a prior calendar-year panel key for a lag.
- **Source/data-quality flagged:** 21,324 missing cells associated with source suppression, ACS missing-control, or CBP completeness flags.
- **Support source unmatched:** 35,496 missing cells with an ACS or CBP source-match flag set to unavailable.
- **Unexplained by available flags:** 28,500 cells remain unexplained; no cause is imputed from the pattern alone.

Growth variables are missing for all 2010 panel rows because the prior year is outside the locked study panel; later missingness can also reflect gaps in valid prior source observations or denominators. Explicit lags require actual prior calendar years and otherwise remain null. ACS source matching is separate from lag availability. CBP is a left-joined support source; unmatched, suppressed, or incomplete CBP does not invalidate the core BDS-QCEW observation. Suppression is not zero.

The annual missingness table shows QCEW growth missingness at `employment_growth` 10.2%, `establishment_growth` 10.2%, `payroll_growth` 10.2%, `wage_growth` 10.2%. Highest missingness is concentrated at the initial study boundary for growth and lag families. The concentration table checks only leading missingness rates for selected fields (minimum group size 50); it is not a sector/MSA performance ranking.

- `startup_rate_lag1`: highest sector missingness was 42.3% (sector 11); median sector rate was 14.5%.
  Across MSAs with at least 50 panel rows, the highest observed rate was 32.0% (median MSA rate 12.5%).
- `employment_growth`: highest sector missingness was 14.4% (sector 11); median sector rate was 10.5%.
  Across MSAs with at least 50 panel rows, the highest observed rate was 34.5% (median MSA rate 9.5%).
- `acs_population_growth`: highest sector missingness was 13.7% (sector 11); median sector rate was 12.7%.
  Across MSAs with at least 50 panel rows, the highest observed rate was 100.0% (median MSA rate 7.2%).
- `median_household_income`: highest sector missingness was 6.8% (sector 62); median sector rate was 5.6%.
  Across MSAs with at least 50 panel rows, the highest observed rate was 93.6% (median MSA rate 0.0%).
- `cbp_employment`: highest sector missingness was 32.0% (sector 22); median sector rate was 7.5%.
  Across MSAs with at least 50 panel rows, the highest observed rate was 54.7% (median MSA rate 7.6%).
- `cbp_establishments`: highest sector missingness was 32.0% (sector 22); median sector rate was 7.5%.
  Across MSAs with at least 50 panel rows, the highest observed rate was 54.7% (median MSA rate 7.6%).

MSA-size context is a limited missingness check using MSA mean ACS population among MSAs with observed population and at least 50 panel rows; it does not rank regional performance:
- `startup_rate_lag1`: Spearman rho between MSA mean population and missing share = -0.781; lower/middle/upper population-tercile missingness was 18.5% / 12.7% / 9.5% (n=366 MSAs).
- `employment_growth`: Spearman rho between MSA mean population and missing share = 0.081; lower/middle/upper population-tercile missingness was 11.1% / 11.2% / 11.8% (n=366 MSAs).
- `acs_population_growth`: Spearman rho between MSA mean population and missing share = -0.123; lower/middle/upper population-tercile missingness was 17.4% / 10.6% / 9.7% (n=366 MSAs).
- `median_household_income`: Spearman rho between MSA mean population and missing share = -0.233; lower/middle/upper population-tercile missingness was 10.2% / 3.5% / 2.6% (n=366 MSAs).
- `cbp_employment`: Spearman rho between MSA mean population and missing share = 0.074; lower/middle/upper population-tercile missingness was 10.3% / 10.0% / 11.7% (n=366 MSAs).
- `cbp_establishments`: Spearman rho between MSA mean population and missing share = 0.074; lower/middle/upper population-tercile missingness was 10.3% / 10.0% / 11.7% (n=366 MSAs).

## Distribution and Outlier Diagnostics

The distribution table reports skewness, excess kurtosis, percentile tails, exact zeros, negatives, IQR flags, and 3-SD flags. IQR flags are screening counts, not errors. The two histograms zoom the x-axis to P01-P99 and therefore omit tail observations from the visible window; full-range values remain in the tables and extreme-observation output. The growth boxplot hides fliers only for readability; source values remain unchanged.

| Variable | Skewness | Excess kurtosis | Zero N | Negative N | Shape notes |
|---|---:|---:|---:|---:|---|
| `startup_rate` | 1.179 | 9.669 | 6,475 | 0 | moderately skewed; heavy-tailed screening signal; zero-concentrated; bounded percentage/rate; observed within 0-100 review range |
| `employment_growth` | 4.772 | 120.071 | 315 | 19,973 | highly skewed; heavy-tailed screening signal; includes negative values; interpretation depends on measure |
| `establishment_growth` | 45.419 | 3,771.172 | 3,649 | 18,217 | highly skewed; heavy-tailed screening signal; zero-concentrated; includes negative values; interpretation depends on measure |
| `payroll_growth` | 31.008 | 3,116.799 | 0 | 10,896 | highly skewed; heavy-tailed screening signal; includes negative values; interpretation depends on measure |
| `wage_growth` | 26.963 | 2,202.179 | 16 | 8,626 | highly skewed; heavy-tailed screening signal; includes negative values; interpretation depends on measure |
| `acs_population_growth` | 20.058 | 858.647 | 0 | 12,676 | highly skewed; heavy-tailed screening signal; includes negative values; interpretation depends on measure |
| `median_household_income` | 1.353 | 3.385 | 0 | 0 | moderately skewed; heavy-tailed screening signal |
| `unemployment_rate` | 0.908 | 0.779 | 0 | 0 | roughly symmetric by skewness; bounded percentage/rate; observed within 0-100 review range |
| `educational_attainment_pct` | 0.796 | 0.618 | 0 | 0 | roughly symmetric by skewness; bounded percentage/rate; observed within 0-100 review range |
| `labor_force_participation_pct` | -0.749 | 1.974 | 0 | 0 | roughly symmetric by skewness; bounded percentage/rate; observed within 0-100 review range |

Among the selected core measures, `employment_growth` has the most IQR flags (5,000); `employment_growth` has the most 3-SD flags (910). These thresholds are descriptive screens, not deletion rules.
- `startup_rate` lowest: 0.000 in Abilene, TX, sector 11, 2010.
- `startup_rate` highest: 80.000 in Bay City, MI, sector 11, 2015.
- `employment_growth` lowest: -0.850 in Wildwood-The Villages, FL, sector 71, 2012.
- `employment_growth` highest: 3.448 in Lewiston-Auburn, ME, sector 55, 2014.
- `establishment_growth` lowest: -0.953 in El Centro, CA, sector 81, 2013.
- `establishment_growth` highest: 15.950 in El Centro, CA, sector 62, 2013.
- `payroll_growth` lowest: -0.824 in Great Falls, MT, sector 21, 2018.
- `payroll_growth` highest: 14.934 in Homosassa Springs, FL, sector 55, 2021.
- `wage_growth` lowest: -0.728 in Lawrence, KS, sector 55, 2020.
- `wage_growth` highest: 6.578 in Homosassa Springs, FL, sector 55, 2021.
- `acs_population_growth` lowest: -0.695 in Salisbury, MD, sector 23, 2023.
- `acs_population_growth` highest: 2.017 in Salisbury, MD, sector 23, 2013.
- `median_household_income` lowest: 31,264.000 in Brownsville-Harlingen, TX, sector 11, 2010.
- `median_household_income` highest: 157,444.000 in San Jose-Sunnyvale-Santa Clara, CA, sector 23, 2023.
- `unemployment_rate` lowest: 2.100 in Bismarck, ND, sector 23, 2019.
- `unemployment_rate` highest: 18.500 in El Centro, CA, sector 22, 2013.
- `educational_attainment_pct` lowest: 11.800 in Hanford-Corcoran, CA, sector 22, 2010.
- `educational_attainment_pct` highest: 63.900 in Boulder, CO, sector 23, 2023.
- `labor_force_participation_pct` lowest: 25.100 in Wildwood-The Villages, FL, sector 22, 2023.
- `labor_force_participation_pct` highest: 75.900 in Fargo, ND-MN, sector 23, 2012.

### Plausibility Flags

- `establishment_entry_rate` / `outside_0_100`: 2 flagged. Rate outside 0 to 100; review source definition and denominator before calling invalid.

Negative growth is valid. The range checks produced 2 rate/percentage flags; these are review prompts, not proof of invalid data and not cleaning rules. Nonnegative count/level measures also receive sign checks. No extreme finite growth observation is treated as impossible solely because it is large.

### Prior-Denominator Review

- `employment_growth`: top 1% absolute-growth observations have median prior denominator 656.000; 46.7% fall at or below the full-sample positive-denominator 10th percentile. Of 6,468 missing-growth rows, 0 have a zero prior denominator, 0 a negative denominator, and 6,468 no matched prior denominator.
- `establishment_growth`: top 1% absolute-growth observations have median prior denominator 52.000; 49.0% fall at or below the full-sample positive-denominator 10th percentile. Of 6,468 missing-growth rows, 0 have a zero prior denominator, 0 a negative denominator, and 6,468 no matched prior denominator.
- `payroll_growth`: top 1% absolute-growth observations have median prior denominator 34,545,042.500; 40.2% fall at or below the full-sample positive-denominator 10th percentile. Of 6,468 missing-growth rows, 0 have a zero prior denominator, 0 a negative denominator, and 6,468 no matched prior denominator.
- `wage_growth`: top 1% absolute-growth observations have median prior denominator 51,219.000; 9.8% fall at or below the full-sample positive-denominator 10th percentile. Of 6,468 missing-growth rows, 0 have a zero prior denominator, 0 a negative denominator, and 6,468 no matched prior denominator.

The comparison uses prior-year QCEW intermediate levels and the top 1% of absolute finite growth observations. Low denominators can make percentage changes volatile; this is a review signal, not proof of an error. No value is altered.

## Limited Figures

- `reports/figures/a5_startup_rate_histogram.png`
- `reports/figures/a5_employment_growth_histogram.png`
- `reports/figures/a5_growth_boxplot.png`
- `reports/figures/a5_missingness_summary.png`

## Implications for Later Analysis

Revisit transformations for skewed positive level variables, robust summaries for heavy-tailed growth, whether controls with limited support availability belong in each later sample, and denominator sensitivity for extreme growth. Lag availability may constrain complete-history specifications and temporal validation. No transformation, deletion, capping, winsorization, imputation, or feature selection was performed here.

## What Cannot Yet Be Concluded

These summaries do not establish causality, predictive importance, hypothesis support, an entrepreneurial gap, expected entrepreneurship, or model performance. The panel is repeated over MSA-industry units; pooled observations are not independent. Time, sector, and MSA patterns are reported in A5.3, and relationships are reported in A5.4.
