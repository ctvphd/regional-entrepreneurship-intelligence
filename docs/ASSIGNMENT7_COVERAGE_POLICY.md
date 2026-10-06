# Assignment 7 Coverage Policy

## Purpose

Coverage status describes completeness of the historical MSA panel under the established A5 descriptive screen. It is not a model-confidence score, probability interval, or guarantee of equal prediction quality.

## Source and Exact Rule

Use the finalized `reports/tables/a5_msa_coverage.csv` fields, carried forward and cross-checked in `a6_msa_coverage_audit.csv`:

- `row_count` (dashboard `observation_count`): number of MSA-industry-year panel rows.
- `sector_count`: distinct analytical sectors represented.
- `year_count`: distinct calendar years represented.
- `eligible_for_comparison`: existing A5 eligibility flag.

The source A5 rule is **at least 100 panel rows, at least 5 sectors, and at least 10 years**. A7.2 validates the source flag against these exact thresholds and against the analytical panel counts. Passing is labeled `comparison_eligible`; not passing is labeled `thin`. No “strong” or “moderate” category is introduced.

`first_year` and `last_year` are derived as min/max available panel year per CBSA. `model_eligible_flag` and `a6_oof_row_count` come from A6: the flag means at least one A6 development OOF row, not all-year model support. Counts and booleans remain separate from the descriptive A5 status.

## Display and Limitations

Show counts and exact status/definition in text; never convey status using color alone. `comparison_eligible` only means the geography passed a descriptive comparison screen. `thin` is a coverage caveat, not a judgment about a place. This A5 threshold is not an A6 training eligibility criterion. The final holdout has its own complete-case sample audit and should not be inferred from the all-period coverage flag. Any new status rule requires explicit documentation and cannot be chosen from holdout outcomes.
