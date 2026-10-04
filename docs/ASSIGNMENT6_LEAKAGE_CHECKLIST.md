# Assignment 6 Leakage Checklist

Apply this checklist to every fold, preprocessing pipeline, expected-rate benchmark, residual cutoff, classifier, and reported metric.

## Prohibited

- [ ] Fit expected entrepreneurship once on the full 2010-2023 panel before cross-validation.
- [ ] Calculate a residual gap threshold from the full panel, validation data, or final holdout.
- [ ] Use `startup_rate`, growth, ACS, or other values from t+1/t+2/t+3 as predictors at t.
- [ ] Use future residuals, expected rates, gap labels, predictions, or outcome-derived summaries as predictors.
- [ ] Match the third subsequent available row instead of exact calendar year t+3.
- [ ] Let an observation whose target outcome is after a fold's training cutoff influence first-stage fitting or threshold calculation.
- [ ] Fit imputation, scaling, encoding, feature selection, dimensionality reduction, or other preprocessing on validation/test/holdout data.
- [ ] Use validation or final-holdout outcomes for model/specification/hyperparameter selection.
- [ ] Tune the primary gap threshold to improve classifier metrics or force equal prevalence by year.
- [ ] Use A5 high-growth/low-startup quadrants to define/tune the formal target.
- [ ] Train on micropolitan observations in the primary MSA design.

## Required Fold Procedure

- [ ] Establish exact same-MSA, same-sector predictor `t` and outcome `t+3` keys.
- [ ] Define each training outcome cutoff and exclude later outcomes from all training-derived operations.
- [ ] Fit the expected-entrepreneurship model within the fold using training years only.
- [ ] Generate training residuals and calculate the primary 20th-percentile cutoff from training residuals only.
- [ ] Apply the fitted expected model and unchanged training cutoff to future validation/test rows.
- [ ] Use target-year covariates only inside fold-fitted expected-rate label construction; never include them in `X_t`.
- [ ] Fit all predictive-model preprocessing and feature selection using training records only.
- [ ] Keep the 2018-2020 predictor / 2021-2023 outcome holdout untouched until the design and model choices are frozen.
- [ ] Preserve natural target prevalence and report it rather than rebalancing by year.
- [ ] Record fold years, target cutoff, training-only threshold, sample counts, and unavailable exact calendar pairs.

## A6.1 Implementation Boundary

The A6.1 scaffolding validates year pairing, fold boundaries, MSA scope, and feature timing. It does not calculate expected values, residuals, thresholds from observations, labels, or model predictions.

## A6.2 Leakage Audit

- [x] Load the analytical panel read-only and use the frozen A6.1 fold configuration.
- [x] Fit each expected-rate model only on complete-case rows through that fold's first-stage fit cutoff (2016, 2017, or 2018).
- [x] Restrict validation residuals to exact same-CBSA/same-sector t-to-t+3 calendar pairs.
- [x] Keep the final 2018-2020 predictor / 2021-2023 outcome holdout out of fitting, scoring, and model selection.
- [x] Do not impute, cap, or trim values in the primary expected-rate model.
- [x] Use target-year features only within fold-local expected-rate scoring and residual diagnostics; do not put them in any predictor matrix.
- [x] Record the unseen validation-year fixed-effect rule: carry forward the latest fitted training-year effect, without validation outcomes.
- [x] Keep MSA fixed effects sensitivity-only; validation MSAs without a complete training observation are not estimable in that sensitivity and are counted separately.
- [x] Do not create residual quantile thresholds, gap labels, classifiers, or final-holdout predictions in A6.2.

This audit concerns the expected-rate benchmark and its diagnostics only. A6.3 must separately implement and test fold-local residual cutoffs and labels before any predictive-model features or outcomes are assembled.
