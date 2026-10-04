# Assignment 6 Modeling Decisions (Open Register)

This register is superseded for resolved A6.1 choices by `docs/ASSIGNMENT6_DESIGN.md`. Assignment 6.1 freezes the primary startup-rate outcome, employment-growth predictor, residual sign, training-fold-only bottom-20% primary threshold, exact t+3 horizon, expanding temporal folds, final holdout, baselines, and metrics. It remains a handoff, not a model implementation: no target, expected-entrepreneurship estimate, future label, or model has been created.

| Topic | Evidence from Assignment 5 | Decision still required |
|---|---|---|
| Expected entrepreneurship and residual alignment | Startup rate is the primary outcome; A5 found a weak pooled association and material sector differences. | A6.1 freezes the conceptual expected-rate definition and `observed - expected` residual; A6.2 still selects the empirical specification using diagnostics. |
| Gap threshold | A5's descriptive high-growth/low-startup quadrant covers 19.29% and is not a target. | A6.1 locks bottom 20% of training residuals as primary candidate; A6.3 must test bottom 10%, bottom 25%, and below training mean minus 1 SD. |
| Three-year horizon | The panel ends in 2023; 2020 is latest targetable predictor year. | A6.1 locks exact calendar t+3; do not use any-time-in-next-three-years or third-observed-row substitutes. |
| Fold-safe target construction | Temporal evaluation is required by the research design. | A6.1 specifies fold-only expected model and residual cutoff; A6.2/A6.3 implement and audit it. |
| Baseline | Predictive improvement has not been tested. | A6.1 specifies prevalence and limited logistic baselines; A6.4 implements after target construction. |
| Classification metrics | No classifier exists. | A6.1 locks Average Precision as primary and ROC-AUC, recall, precision, F1, Brier/calibration as secondary; no operating threshold is fixed. |
| Time controls | Year patterns are broad and 2020-2021 unusual descriptively. | A6.1 makes year effects mandatory in the expected-rate candidate and specifies expanding windows; implementation remains future work. |
| Sector controls | Sector ranges and correlations vary materially. | A6.1 makes sector effects mandatory and requires comparing growth-by-sector interactions in A6.2. |
| Growth variables | Employment growth is primary; payroll growth correlates 0.714 with it. | Keep employment growth primary candidate; compare support measures and do not form an unvalidated weighted index. |
| Heavy tails and denominators | Employment growth has excess kurtosis 120.071; extreme rates often have small prior denominators. | Pre-specify robust estimates and tail/denominator sensitivities; preserve raw measures. |
| ACS grain | ACS fields are MSA-year values repeated across sector rows. | Preserve MSA-year origin, prevent repeated-measure weighting where regional summaries/validation require one row per MSA-year. |
| Lags | Startup-rate missingness rises to 13.66%, 20.41%, and 27.01% at lags 1-3. | Assess availability, panel continuity, and a missingness strategy before selecting lag features. |
| Multicollinearity | Employment/payroll growth and income/education are correlated; other candidates may overlap. | Diagnose the specified design (including VIF or alternatives); do not select by pairwise correlations alone. |
| COVID period | Excluding 2020-2021 leaves core association positive (r=0.109). | Retain 2020-2021 in the main analysis, use year controls, and report sensitivity checks; do not claim a causal COVID effect. |
| Geographic holdout | MSAs are repeated geographic units with broad heterogeneity. | A6.1 keeps temporal validation primary; unseen-MSA holdout remains A6.6 robustness. |

The governing A6.1 choices are specified in `docs/ASSIGNMENT6_DESIGN.md`. A6.2 must review first-stage feature completeness, temporal out-of-sample feasibility, residual stability, coefficient stability, and interaction complexity before selecting the expected-rate specification. No later-stage work is authorized here.
