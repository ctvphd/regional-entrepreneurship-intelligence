# Final Limitations and Strengths

## Limitations

1. The outcome is a model-relative gap, not an administrative measure of entrepreneurial failure or a normative definition of a healthy ecosystem.
2. Firm startup rate is a narrow measure of entrepreneurship and does not capture every form of business formation or innovation.
3. Predictive association does not establish that industry growth causes entrepreneurship or identify mechanisms behind a particular metro's result.
4. Two-digit NAICS aggregation conceals within-sector heterogeneity.
5. The validated study period is 2010-2023; the proposal's earlier years are outside the comparable final panel.
6. The prediction horizon is a fixed three years and does not describe shorter or longer horizons.
7. Complete-case eligibility excludes a patterned subset; smaller and lower-startup metros are less represented in some analyses.
8. Geographic dependence is not explicitly modeled in the primary classifier.
9. The final target years include pandemic and post-pandemic conditions that may differ from other regimes.
10. Probability calibration is imperfect; the primary result is ranking performance, not a promise of calibrated individual probabilities.
11. Temporal generalization is evaluated on one final holdout period.
12. Production empirical reproduction requires the authorized source cache; the clean-clone fixture validates software behavior, not empirical estimates.

## Strengths

- Large metropolitan-industry-year panel assembled from multiple federal statistical sources.
- Explicit relational database architecture, source lineage, and crosswalk/version documentation.
- Temporal holdout evaluation with exact `t` to `t+3` pairing and fold-local target construction.
- Leakage controls and a precommitted model hierarchy.
- Multiple predictive models and target-definition sensitivity analyses.
- Geographic holdout, MSA-size, sector, and other robustness analyses.
- Explicit complete-case selection, suppression, missingness, and coverage reporting.
- Frozen dashboard artifacts with metric reconciliation and source traceability.
- Interactive dashboard with historical, evaluation, coverage, and methods distinctions.
- Deterministic synthetic reviewer fixture that exercises real loaders and transformations without presenting synthetic estimates as empirical findings.
- Extensive automated tests and documented production-cache boundaries.
