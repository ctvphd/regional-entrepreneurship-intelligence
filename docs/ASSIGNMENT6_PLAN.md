# Assignment 6 Iterative Plan

| Step | Scope | Status / boundary |
|---|---|---|
| A6.1 | Target Definition, Baseline & Temporal Validation Design | Complete as design/scaffolding only. No model fit, expected values, residuals, or labels. |
| A6.2 | Expected Entrepreneurship Model | Complete. Model A selected on development folds; robust/interaction/feature sensitivities, residual diagnostics, leakage audit, and outputs documented. Holdout unused; no labels created. |
| A6.3 | Entrepreneurial Gap Target Construction | Complete for development folds only. Fold-local p20 labels, robustness cutoffs, selection/negative-prediction audits, and leakage checks documented. Complete-case scope is materially selective and must be disclosed in A6.4. No classifier or holdout labels. |
| A6.4 | Baseline Prediction Model | Not started. Compare prevalence and transparent logistic baselines. |
| A6.5 | Advanced Predictive Models | Not started. Only after baseline and leakage review. |
| A6.6 | Robustness, Interpretation & Generalization | Not started. Include geographic holdout as robustness, tail/COVID sensitivities. |
| A6.7 | Final Analytics Engine, QA & Assignment 6 Completion | Not started. |

The authoritative A6.1 specification is `docs/ASSIGNMENT6_DESIGN.md`; A6.2 implementation details and decision are in `docs/ASSIGNMENT6_EXPECTED_MODEL.md`; A6.3 target definition and outputs are in `docs/ASSIGNMENT6_GAP_TARGET.md` and `reports/assignment6_entrepreneurial_gap_target.md`. Later steps may report data/feature feasibility constraints, but must not silently change the three-year horizon, primary outcome, bottom-20% primary candidate, fold-only cutoff rule, or untouched temporal holdout. A6.4 must retain the complete-case population caveat and never use target-year label-construction fields as predictor-year features.
