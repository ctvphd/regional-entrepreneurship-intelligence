# Assignment 7 Logical Data Contracts

These logical contracts were implemented in A7.2. Physical schemas, types, field definitions, nullability, source columns, and uses are in `ASSIGNMENT7_DATA_DICTIONARY.md`; field transformations are audited in `reports/tables/a7_dashboard_lineage_audit.csv`.

## `dashboard_msa_industry_year`

**Grain/key:** one CBSA x 2-digit sector x descriptive calendar year; unique `(cbsa_code, sector_code, year)`.

**Implemented fields:** canonical measures/quality flags, `expected_startup_rate`, `alignment_residual`, `alignment_label`, `observed_historical_gap_status`, `gap_label_predictor_year`, MSA coverage counts/status, and eligibility flags. Expected/alignment/gap fields are populated only from A6 fold-validation target records. Prediction scores stay in a separate table to preserve temporal semantics. No `risk_category` is created.

**Lineage:** descriptive fields originate from `v_analytics_msa_industry_year` in the canonical read-only A4 DB. The A6 panel does not contain expected rates, residual/alignment, or gap status; exact A6 development/holdout label/score artifacts or a separately documented derivation must supply them. The final holdout artifact only contains predictions for 2018–2020 predictor years and actual outcomes for 2021–2023; it is retrospective and must remain marked holdout. Any new output is an A7.2 transformation, never an A7.1 artifact.

## `dashboard_model_summary`

**Grain/key:** one fixed `(dataset, model, metric)` value, with `N`, prevalence, threshold policy where applicable, and artifact/version metadata.

**Lineage:** `a6_final_model_performance.csv` plus locked A6 OOF artifacts when needed. Existing metrics are immutable; no UI-side fitting/recomputation. Splits are `development_oof` and `final_holdout`; models are prevalence benchmark, logistic, and HGB.

## `dashboard_model_predictions`

**Grain/key:** one `(cbsa_code, sector_code, predictor_year, target_year)` prediction pair; target must equal predictor year + 3.

**Fields:** identifiers/names, `predictor_year`, `target_year`, `actual_gap`, `development_or_holdout`, fold where applicable, `logistic_probability`, `hgb_probability`, primary-model flag, and coverage status. Scores and outcome are present for finalized A6 records; outcome is always explicitly a later realized target. Never place target-year covariates into predictor records.

**Lineage:** combines A6 development OOF artifacts and `a6_final_holdout_predictions.csv`, explicitly tagged by split. Holdout records are retrospective diagnostics, not a general historical/deployed score feed.

## `dashboard_coverage`

**Grain/key:** one CBSA with defined study window/coverage rule; optionally CBSA-sector if that is the displayed coverage unit.

**Fields:** CBSA code/name, observation count, sector count, year count, eligible-comparison flag/count, source availability/suppression summaries, `coverage_status`, and rule version.

**Lineage:** A5/A6 coverage audit plus observed panel year endpoints. Status is `comparison_eligible` or `thin` using A5's exact 100-row/5-sector/10-year rule. Existing “thin” is not a model reliability label.

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
- `risk_category` is omitted because no non-holdout presentation rule was frozen; use continuous probability/rank only.
