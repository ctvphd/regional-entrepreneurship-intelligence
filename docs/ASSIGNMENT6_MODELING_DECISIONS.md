# Assignment 6 Modeling Decisions (Open Register)

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
