# Assignment 7 Logical Data Contracts

These are proposed logical contracts, not created datasets. A7.1 does not reshape, export, or materialize data. A7.2 must define schemas, keys, nullability, units, year roles, row-count reconciliation, source hashes, and validation before implementation.

## `dashboard_msa_industry_year`

**Grain/key:** one CBSA x 2-digit sector x descriptive calendar year; unique `(cbsa_code, sector_code, year)`.

**Proposed fields:** `cbsa_code` (string, preserve leading zeroes), `msa_name`, `sector_code`, `sector_name`, `year`, `startup_rate`, `expected_startup_rate`, `alignment_residual`, `alignment_label`, `observed_gap_status`, `employment_growth`, `coverage_status`, and provenance/eligibility flags. Optional `predicted_gap_probability_logistic`, `predicted_gap_probability_hgb`, `risk_category`, `predictor_year`, `target_year`, and `prediction_available` are populated only for an eligible exact CBSA-sector-predictor-year match. Do not collapse predictor and target years into one `year` field.

**Lineage:** descriptive fields originate from `v_analytics_msa_industry_year` in the canonical read-only A4 DB. The A6 panel does not contain expected rates, residual/alignment, or gap status; exact A6 development/holdout label/score artifacts or a separately documented derivation must supply them. The final holdout artifact only contains predictions for 2018–2020 predictor years and actual outcomes for 2021–2023; it is retrospective and must remain marked holdout. Any new output is an A7.2 transformation, never an A7.1 artifact.

## `dashboard_model_summary`

**Grain/key:** one fixed `(dataset, model, metric)` value, with `N`, prevalence, threshold policy where applicable, and artifact/version metadata.

**Lineage:** `a6_final_model_performance.csv` plus locked A6 development OOF artifacts when needed. Existing metrics are immutable; no UI-side fitting/recomputation. Distinguish `development_oof` from `holdout` and prevalence benchmark/logistic/HGB.

## `dashboard_model_predictions`

**Grain/key:** one `(cbsa_code, sector_code, predictor_year, target_year)` prediction pair; target must equal predictor year + 3.

**Fields:** identifiers/names, `predictor_year`, `target_year`, `actual_gap` (nullable and outcome-only), `predicted_probability_logistic`, `predicted_probability_hgb`, sample/model role, and eligibility/provenance. Never place target-year fields into predictor records.

**Lineage:** `a6_final_holdout_predictions.csv` is final-holdout only and contains realized future labels. It is suitable for retrospective diagnostics, not a general historical/deployed score feed. Any development OOF prediction source must be separate and explicitly tagged.

## `dashboard_coverage`

**Grain/key:** one CBSA with defined study window/coverage rule; optionally CBSA-sector if that is the displayed coverage unit.

**Fields:** CBSA code/name, observation count, sector count, year count, eligible-comparison flag/count, source availability/suppression summaries, `coverage_status`, and rule version.

**Lineage:** `a6_msa_coverage_audit.csv`, `a6_msa_coverage_summary.csv`, sample-selection audits, and source match/coverage flags in the canonical view. Define strong/moderate/thin thresholds and denominator in A7.2 before assigning categories; existing “thin” flags are specific to their source rule and are not model reliability labels.

## `dashboard_sources`

**Grain/key:** one source artifact/version/role record.

**Fields:** source name, years, unit/grain, role (descriptive/predictor/target/evaluation), authoritative citation/attribution, repository-relative artifact, build/version reference, and whether actual future outcomes are present.

**Lineage:** project source metadata, A4 metadata/manifests, A6 lock/report, and named A6 outputs. No machine-specific absolute paths.

## Lineage and Leakage Rules

- Descriptive observed history is not a model score.
- Development OOF and final holdout scores have distinct datasets, periods, and validation roles.
- Actual holdout outcomes are future targets relative to `predictor_year`; they are evaluation-only and never forecast inputs.
- Risk categories are views over frozen scores with a separately documented display rule, not a new target/classifier.
- The dashboard reads versioned, validated A7.2 outputs and frozen A6 artifacts; canonical SQLite remains read-only.
- No contract silently imputes, changes sector/geography vintage, or treats missing/suppressed values as zero.
