# Final Research Design

## Scope and Unit

The study asks whether metropolitan industry growth predicts later startup activity below a model-based expectation. The unit is a July 2023 CBSA/MSA x 2-digit 2022 NAICS industry x year. The validated primary study window is 2010-2023. The proposal discussed 2005-2023; narrowing to the comparable source window is a documented scope refinement, not a change in the research question.

## Measures and Gap

Startup rate is the primary entrepreneurship measure: age-0 BDS firms divided by all BDS firms in the same metro-industry-year. Employment growth is the primary industry-opportunity measure. Expected startup activity is estimated by the development-stage expected-entrepreneurship model. Alignment is observed startup rate minus expected startup rate. A gap is a model-relative negative deviation at or below the development-derived p20 residual threshold. It is not an administrative outcome, a causal ecosystem failure, or a normative ideal.

The final predictive outcome is constructed fold-locally. Expected-model estimation, residual construction, and thresholding use development information only as prescribed for each fold. The cutoff is not globally normalized using future outcomes.

## Prediction and Validation

Predictors are measured in year `t`; the outcome is the exact same CBSA-sector in year `t+3`. Predictor-year inputs are the only classifier features; target-year information used by the expected-startup benchmark is confined to label construction. Lag features use prior calendar years only. The 2021-2023 target years are the final temporal holdout and were not used for model selection.

The primary model is the preselected, interpretable Logistic Regression reference. HistGradientBoosting is the nonlinear sensitivity model. The final holdout comparison did not retroactively select the primary model. Average Precision is the primary ranking metric and is interpreted against natural prevalence; ROC-AUC, Brier score, recall, precision, F1, lift, and calibration are secondary diagnostics. Evidence is predictive/associational, not causal.

## Canonical Results

Values are rounded consistently to three decimals except prevalence and lift, which are shown as percentages and a multiplier.

| Sample | Model | N | Prevalence | AP | ROC-AUC | Brier | Recall | Precision | F1 | Top-decile lift |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Development OOF | Logistic Regression | 13,633 | 19.1% | 0.367 | 0.693 | 0.142 | - | - | - | - |
| Final temporal holdout | Logistic Regression (primary) | 10,304 | 23.3% | 0.404 | 0.692 | 0.164 | 0.708 | 0.328 | 0.448 | 1.99x |
| Final temporal holdout | HistGradientBoosting (sensitivity) | 10,304 | 23.3% | 0.424 | 0.708 | 0.161 | - | - | - | 2.09x |

The model does not perfectly classify future entrepreneurial gaps, but it provides meaningful ranking signal. Average Precision exceeded the natural prevalence benchmark, ROC-AUC remained stable between development and the final temporal holdout, and the highest-scored 10% experienced gaps at roughly twice the overall holdout rate.

The logistic model is primary because it was the preselected reference, is interpretable, and nearly matched more flexible alternatives; the holdout was not used to choose it. HistGradientBoosting tests nonlinear predictive structure and had modestly better holdout ranking, but remains secondary by design.

## Population Labels and Claim Boundaries

The descriptive dashboard panel covers 381 MSAs. The final holdout model population contains 365 MSAs and 19 sectors (10,304 eligible metro-industry pairs). In the A5 comparison-coverage definition, 314 of 381 MSAs have good comparison coverage and 67 have limited coverage. These are different populations/eligibility definitions, not contradictory counts.

| Claim | Supported? |
| --- | --- |
| Predict future model-relative gaps | Yes, within the evaluated historical sample |
| Rank higher-risk cases | Yes, with AP above prevalence and positive lift |
| Show temporal generalization | Yes, within the 2021-2023 final holdout |
| Show some geographic robustness | Yes, in development robustness analysis |
| Establish industry growth causes entrepreneurship | No |
| Diagnose why a specific metro has a gap | No |
| Predict current/live conditions | No |
| Generalize universally | No |

## Practical Interpretation

The framework can prioritize metro-industry combinations for further investigation and support regional economic-development screening or follow-up ecosystem research. It does not prescribe policy, allocate funding, diagnose causes, or guarantee future outcomes.

## Provenance

Production dashboard values trace to the frozen A7.2 artifacts, finalized A6 outputs, and documented A4-A6 source lineage. The synthetic reviewer database and Parquet panel are isolated under `data/review/`; they contain no production estimates or synthetic model-performance metrics. See [reviewer reproducibility](REVIEWER_REPRODUCIBILITY.md) for the clean-clone versus production-cache boundary.
