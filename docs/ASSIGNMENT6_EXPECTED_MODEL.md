# Assignment 6.2 Expected Entrepreneurship Model

**Status:** Estimated and compared on development folds only. The final holdout remains unused.

## Construct and primary specification

The response is the observed BDS firm startup rate. The selected expected-rate benchmark is Model A: `startup_rate ~ startup_rate_lag1 + employment_growth + ACS regional controls + sector fixed effects + year fixed effects`. The ACS controls are population growth, median household income, educational attainment, labor-force participation, and unemployment. All predictors refer to the outcome-year observation or earlier. Estimation uses complete cases only; no imputation or winsorization is used in the primary fit.

Selection rationale: The linear baseline has the lower pooled development-fold MAE and is the parsimonious choice. Huber Model C reduced MAE in all three development folds (mean 1.494 versus 1.528 for Model A), but its mean RMSE was 2.189 and exceeded Model A in 2 of three folds; its later-fold positive residual drift also remained. It is retained as a typical-error robustness check, not selected as the primary benchmark because that MAE-only gain does not improve tail-sensitive error or temporal calibration consistently.

Model A is the additive OLS baseline. Model B adds `employment_growth × sector` while retaining sector fixed effects. Model C applies Huber M-estimation to the Model A formula as a robust sensitivity, not a primary candidate. The selection comparison is based on three expanding development folds and includes MAE, RMSE, out-of-sample R-squared against the training mean, residual distribution/stability, and coefficient stability. The Model B interaction is retained only for a consistent material improvement; otherwise parsimony favors Model A.

## Fold and time handling

The exact A6.1 fold file determines fit end years 2016, 2017, and 2018. The full analytical panel within each fold's expected-model fit window is used for fitting; validation scoring is restricted to exact same-CBSA/same-sector t-to-t+3 calendar pairs. Fit rows with any missing model field are excluded; no data are imputed. Year and sector effects are fit using training rows only. Because a validation year is not represented in a training-only year fixed-effect design, its year effect is forecast by carrying forward the latest training-year effect. This persistence rule is outcome-free, preserves the mandatory year effects, and is included in every candidate prediction. It is an explicit extrapolation assumption, not a coefficient estimated for the validation year.

Target-year covariates and observed startup rates are used only to estimate/score the fold-local expected-rate benchmark and calculate its diagnostic residuals. They are not predictive features at predictor year t. No residual quantile threshold, gap status, classifier, or final-holdout prediction is created here.

## Model choice

The linear baseline has the lower pooled development-fold MAE and is the parsimonious choice. Huber Model C reduced MAE in all three development folds (mean 1.494 versus 1.528 for Model A), but its mean RMSE was 2.189 and exceeded Model A in 2 of three folds; its later-fold positive residual drift also remained. It is retained as a typical-error robustness check, not selected as the primary benchmark because that MAE-only gain does not improve tail-sensitive error or temporal calibration consistently.

Model C and feature alternatives remain documented sensitivity results. The selection does not use the 2018-2020 predictor block or 2021-2023 final outcomes. No causal interpretation is intended.
