# Final Project Summary

## Executive Summary

Regional Entrepreneurship Intelligence studies whether metropolitan industry opportunity predicts later business startup activity below a model-based expectation. It combines federal business-demography, employment, regional-control, and business-pattern data, then evaluates exact three-year-ahead prediction and presents the historical evidence in an interactive dashboard. The project is a predictive and descriptive decision-support framework, not a causal diagnosis or live forecast.

## Research Question and Contribution

Do metro-industry combinations with stronger employment growth subsequently show startup activity consistent with their modeled expectation, and can year-t information rank cases at higher risk of a model-relative gap at t+3? The contribution is an auditable data pipeline and an explicit expected-startup benchmark paired with temporally validated gap-risk ranking.

## Data and Analytical Design

The unit is July 2023 CBSA/MSA x 2-digit 2022 NAICS industry x year. BDS supplies age-0 firm startups and total firms; QCEW supplies employment and industry growth; ACS supplies regional controls; CBP supplies supporting business-structure measures. The final validated primary period is 2010-2023. The proposal's 2005-2023 window was narrowed for source comparability and feasibility; this is a documented scope refinement.

Startup rate is age-0 firms divided by all firms. Expected startup activity is estimated using the development-stage expected-entrepreneurship model. Alignment is observed minus expected startup rate; the entrepreneurial response gap is a model-relative negative deviation at or below the training-derived p20 residual cutoff. It is not an administrative label, a causal ecosystem failure, or a normative ideal.

Predictors use year t and the outcome is the same CBSA-sector at exact t+3. Target-year expected-model inputs are label-construction inputs only, not classifier predictors. Lag features are backward-looking; benchmark estimation and threshold construction are fold-local; the 2021-2023 target years are the final holdout and were not used for model selection.

## Predictive Modeling and Results

Logistic Regression is the preselected primary reference model. HistGradientBoosting is a nonlinear sensitivity model; its modestly higher holdout ranking does not retroactively change the model hierarchy. Average Precision is primary and is compared with natural prevalence.

| Sample | Model | N | Prevalence | AP | ROC-AUC | Brier | Recall | Precision | F1 | Top-decile lift |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Development OOF | Logistic Regression | 13,633 | 19.1% | 0.367 | 0.693 | 0.142 | - | - | - | - |
| Final holdout | Logistic Regression | 10,304 | 23.3% | 0.404 | 0.692 | 0.164 | 0.708 | 0.328 | 0.448 | 1.99x |
| Final holdout | HistGradientBoosting | 10,304 | 23.3% | 0.424 | 0.708 | 0.161 | - | - | - | 2.09x |

Average Precision exceeds the 23.3% holdout prevalence and the highest-scored decile has roughly twice the overall gap rate. This is meaningful ranking signal, not perfect classification or causal evidence. Detailed metrics and their authoritative source are in [Final Research Design](../docs/FINAL_RESEARCH_DESIGN.md) and the [Assignment 6 final report](assignment6_final_analytics_engine.md).

## Dashboard and Reproducibility

The dashboard presents Overview, Explore Markets, Model Insights, Data & Confidence, and About the Analysis. Its production metrics come from frozen A7.2 artifacts and finalized A6 outputs. The synthetic reviewer fixture exercises the source loaders, transformations, review database, quality checks, and dashboard descriptive-panel loader without synthesizing model results.

A clean clone can reproduce code-level tests and the synthetic review path. Rebuilding the full 63,577-row empirical panel, production suppression/crosswalk prevalence, target prevalence, final model metrics, and empirical generalization results requires the authorized production cache. Do not describe the empirical results as fully reproducible from this repository alone.

## Limitations and Practical Implications

The startup measure is narrow; sectors are aggregated; complete-case selection is patterned; smaller and lower-startup metros are less represented in some analyses; geographic dependence is not explicit in the primary model; calibration is imperfect; and one temporal holdout cannot establish universal or live performance. Results can help prioritize cases for further investigation and support regional screening. They should not automate funding, prescribe policy, diagnose causes, or guarantee future outcomes.

## Future Research and Course Deliverables

Possible dissertation extensions are: (1) measurement and prediction of entrepreneurial response gaps, (2) spatial clustering and regional spillovers, and (3) ecosystem mechanisms that may help regions convert opportunity into entrepreneurship, including capital access, universities/HBCUs, innovation, broadband, human capital, procurement, and industrial diversity. These are future directions, not analyses completed here.

Assignments 3-7 progress from proposal to database/ETL, EDA, expected-entrepreneurship and predictive validation, then dashboard communication and reviewer reproducibility. See [Assignment Alignment](../docs/PROJECT_ALIGNMENT_A3_A7.md) and the [final presentation outline](../docs/FINAL_PRESENTATION_OUTLINE.md).
