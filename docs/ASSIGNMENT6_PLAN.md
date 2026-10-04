# Assignment 6 Iterative Plan

| Step | Scope | Status / boundary |
|---|---|---|
| A6.1 | Target Definition, Baseline & Temporal Validation Design | Complete as design/scaffolding only. No model fit, expected values, residuals, or labels. |
| A6.2 | Expected Entrepreneurship Model | Complete. Model A selected on development folds; robust/interaction/feature sensitivities, residual diagnostics, leakage audit, and outputs documented. Holdout unused; no labels created. |
| A6.3 | Entrepreneurial Gap Target Construction | Complete for development folds only. Fold-local p20 labels, robustness cutoffs, selection/negative-prediction audits, and leakage checks documented. Complete-case scope is materially selective and must be disclosed in A6.4. No classifier or holdout labels. |
| A6.4 | Baseline Prediction Model | Complete on development folds only. Training-prevalence, simple logistic, and extended logistic benchmarks; OOF metrics, calibration/lift, predictor ablations, and leakage audit documented. Complete-case scope retained; final holdout untouched. |
| A6.5 | Advanced Predictive Models | Complete on the same development folds and A6.4 complete-case OOF sample. Random Forest and HistGradientBoosting compared with the locked simple logistic baseline using fold-local inner temporal tuning, paired ablations, calibration/lift, and validation-only permutation diagnostics. Small pooled AP gains are reported conservatively; final holdout untouched. |
| A6.6 | Robustness, Interpretation & Generalization | Complete on development data only. Gap/Huber target, growth, tail, pandemic, geographic, MSA-size, sector, startup-history, and complete-case coverage sensitivities documented. Final temporal holdout untouched; A6.7 not started. |
| A6.7 | Final Analytics Engine, QA & Assignment 6 Completion | Not started. |

The authoritative A6.1 specification is `docs/ASSIGNMENT6_DESIGN.md`; A6.2 implementation details and decision are in `docs/ASSIGNMENT6_EXPECTED_MODEL.md`; A6.3 target definition and outputs are in `docs/ASSIGNMENT6_GAP_TARGET.md` and `reports/assignment6_entrepreneurial_gap_target.md`. Later steps may report data/feature feasibility constraints, but must not silently change the three-year horizon, primary outcome, bottom-20% primary candidate, fold-only cutoff rule, or untouched temporal holdout. A6.4 must retain the complete-case population caveat and never use target-year label-construction fields as predictor-year features.
