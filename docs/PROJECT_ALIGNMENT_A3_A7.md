# Project Alignment: Assignments 3-7

## Assignment 3: Research Proposal

The proposal established the question of whether regional industry opportunity is associated with later entrepreneurial activity and proposed a 2005-2023 study window. Its central question remained stable through implementation.

## Assignment 4: Database and ETL

The proposal became a versioned, source-auditable data system integrating BDS, QCEW, ACS, and CBP. The resulting analytical panel is keyed at July 2023 CBSA/MSA x 2-digit 2022 NAICS sector x year, with source-native values, crosswalk decisions, missingness, and quality metadata retained through layered transformations.

## Assignment 5: Exploratory Analysis

EDA characterized panel coverage, startup activity, employment growth, missingness, and associations before a predictive target was defined. It established descriptive context without presenting those relationships as causal.

## Assignment 6: Expected Entrepreneurship and Prediction

Assignment 6 defined expected startup activity, model-relative alignment and the p20 gap label, then evaluated exact three-year-ahead prediction with temporal validation, a locked Logistic Regression primary model, HistGradientBoosting sensitivity, geographic and other robustness checks, and explicit leakage controls.

## Assignment 7: Dashboard and Reviewer-Ready Communication

Assignment 7 materialized frozen A6 results into an allow-listed dashboard data layer, built five user-facing routes, refined visualization and plain-language communication, and added a deterministic synthetic reviewer path. Production and synthetic results remain separate.

## Documented Scope Refinement

The proposal discussed 2005-2023. The final validated primary scope is 2010-2023 because that is the source-compatible and comparable window documented by the integrated panel. This is a **documented scope refinement**, not conceptual drift: the research question, analytical grain, primary startup construct, and forward prediction design remain aligned.

## Final Design Reference

See [Final Research Design](FINAL_RESEARCH_DESIGN.md) for the authoritative measures, target, timing, model hierarchy, holdout metrics, population definitions, and claim boundaries.
