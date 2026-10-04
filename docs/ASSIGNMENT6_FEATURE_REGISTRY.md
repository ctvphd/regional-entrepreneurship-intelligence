# Assignment 6 Preliminary Feature Registry

Candidate registry only; no feature matrix or transformed values are created. All predictive features are measured at `t` or earlier. `startup_rate` is the expected-model response at the benchmark year and a permissible predictor-year feature for the later gap classifier; it is not a same-year predictor of itself in the expected model.

| Variable | Source | Role | Timing | Tier | Expected-model eligibility | Predictive-model eligibility | Transformation policy | Missingness / risk notes |
|---|---|---|---|---|---|---|---|---|
| `startup_rate` | BDS | Primary entrepreneurship outcome | t | Primary | Response only | Yes, predictor-year value | Retain percent units | Never substitute t+3 value into X_t. |
| `startup_rate_lag1` | BDS | Prior entrepreneurship | t-1 | Primary | Yes | Yes | None specified | 13.66% missing in A5; calendar-contiguous lag. |
| `startup_rate_lag2` | BDS | Prior entrepreneurship | t-2 | Sensitivity | Sensitivity | Sensitivity | None specified | 20.41% missing; do not require in primary. |
| `startup_rate_lag3` | BDS | Prior entrepreneurship | t-3 | Sensitivity | Sensitivity | Sensitivity | None specified | 27.01% missing; do not require in primary. |
| `establishment_entry` | BDS | Supporting entrepreneurship | t | Sensitivity | Sensitivity | Sensitivity | Retain source count | Availability/scale differ from primary startup rate. |
| `establishment_entry_rate` | BDS | Supporting entrepreneurship | t | Sensitivity | Sensitivity | Sensitivity | Retain source units | Rate definition and values above 100 require care. |
| `firm_startups` | BDS | Supporting entrepreneurship | t | Sensitivity | Sensitivity | Sensitivity | Retain source count | Count measure; robustness only. |
| `startup_job_creation` | BDS | Supporting entrepreneurship | t | Sensitivity | Sensitivity | Sensitivity | Retain source count | Supporting measure; robustness only. |
| `employment_growth` | QCEW | Primary industry growth | t | Primary | Yes | Yes | Preserve decimal rate; robust sensitivity later | About 10.17% missing; heavy tails and denominator sensitivity. |
| `establishment_growth` | QCEW | Alternative industry growth | t | Supporting | Alternative | Alternative | Preserve decimal rate | Correlated growth content; do not auto-combine. |
| `payroll_growth` | QCEW | Alternative industry growth | t | Supporting | Alternative | Alternative | Preserve decimal rate | Correlation with employment growth is 0.714. |
| `wage_growth` | QCEW | Alternative industry growth | t | Supporting | Alternative | Alternative | Preserve decimal rate | Alternative specification/sensitivity. |
| `acs_population_growth` | ACS | Regional context | t, MSA-year | Candidate | Candidate | Candidate | Preserve decimal rate | 12.68% missing; repeated across sector rows. |
| `median_household_income` | ACS | Regional context | t, MSA-year | Candidate | Candidate | Candidate | Source dollars; no transform frozen | About 5.56% missing; r=0.613 with education. |
| `educational_attainment_pct` | ACS | Regional context | t, MSA-year | Candidate | Candidate | Candidate | Preserve percent units | About 5.56% missing; examine redundancy with income. |
| `labor_force_participation_pct` | ACS | Regional context | t, MSA-year | Candidate | Candidate | Candidate | Preserve percent units | About 5.56% missing; repeated across sector rows. |
| `unemployment_rate` | ACS | Regional context | t, MSA-year | Candidate | Candidate | Candidate | Preserve percent units | About 5.56% missing; repeated across sector rows. |
| `sector_code` | NAICS reference | Sector context | Fixed classification | Mandatory effect | Yes, fixed effect | Yes, baseline categorical feature | Categorical encoding fit on training only | 19 sectors retained; compare growth interaction. |
| `year` | Panel key | Year context | t | Mandatory effect | Yes, fixed effect | Yes, temporally valid year/time encoding | Encoding fitted within training fold | Retain COVID years; respect time order. |
| `cbsa_code` | Census geography reference | Geographic identity | Fixed | Sensitivity/grouping | Sensitivity-only FE | Grouping/holdout, not primary FE | No primary MSA FE | Geographic holdout is A6.6 robustness. |

## Prohibited Predictive Features

Never put future startup/growth/ACS fields, `gap_status_t_plus_3`, future residual/expected-rate values, or any target-derived transformation into `X_t`. The future target-year covariates needed internally to apply a fold-trained expected-entrepreneurship benchmark are label-construction inputs only, not predictive features.

Imputation and other missing-data/preprocessing choices remain open for A6.2/A6.4. Any fitted preprocessing must be trained inside each temporal training fold. Missing values must not be replaced by zero without a source-specific justification.

## A6.4 Baseline Implementation

Baseline 1 uses `startup_rate`, `startup_rate_lag1`, and `employment_growth`, plus sector contrasts and a standardized linear predictor-year trend. Baseline 2 adds the five ACS candidate controls above. The trend is used rather than validation-year dummy levels so future fold years remain scoreable. Numeric means/scales and sector levels are fitted from each training fold only; the extended-feature complete-case subset is shared across the prevalence, simple, extended, and ablation comparisons for paired evaluation. Rows lost to predictor-feature missingness are counted; no imputation or class rebalancing is performed. Current-year features always join on the predictor-year key, never the target-year row.
