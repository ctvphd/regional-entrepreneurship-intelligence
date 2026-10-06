# Assignment 7 Source Lineage

This document describes the A7.2 lineage boundary. The exhaustive dataset-field-to-source-field mapping, transformation, verification flag, and notes are in `reports/tables/a7_dashboard_lineage_audit.csv`; dataset grains, schemas, counts, keys, and pages are in `reports/tables/a7_dashboard_dataset_inventory.csv`.

## Authoritative Inputs

| Input | Downstream use | Time/role | Important caveat |
| --- | --- | --- | --- |
| `database/assignment4_production.sqlite`, view `v_analytics_msa_industry_year` | Descriptive MSA-sector-year panel, source quality flags, labels, and observed source measures. Read through SQLite `mode=ro` plus `PRAGMA query_only=ON`. | Historical panel 2010–2023. | The view has no fitted expected-startup rate, A6 residual/alignment, or gap label. No dashboard build writes to it. |
| `reports/tables/a6_gap_target_pairs.csv` | Expected target startup rate, alignment residual, and `gap_p20` status in the descriptive panel, filtered strictly to `split_role=validation`. | Fold-validation OOF outcomes, target years through 2020. | Fold-specific A6 outputs; not recomputed. Each CBSA-sector-target-year must be unique and match the canonical panel's observed target startup rate. |
| `a6_baseline_oof_predictions.csv` and `a6_advanced_oof_predictions.csv` | Development logistic and HGB probabilities, actual gap, fold, and exact pair keys. | Development OOF, outcomes through 2020. | Join on CBSA, sector, predictor year, and target year; labels must agree. No retraining. |
| `a6_final_holdout_predictions.csv` | Final logistic/HGB holdout probability and actual gap with CBSA, sector, predictor/target years. | Predictor 2018–2020; realized target 2021–2023. | Retrospective holdout only; never label live/current or merge actual target outcome into predictor-time features. |
| `a6_final_model_performance.csv` | Long-format fixed metric summary. | Development OOF and final holdout. | Values copied unchanged; source dataset/model names retained. |
| A6 calibration/year/sector/MSA-size tables | Fixed diagnostics datasets. | OOF and holdout as identified per table. | No calibration, subgroup score, or threshold is refit. Sector score suppression is retained. |
| `a5_msa_coverage.csv`, `a6_msa_coverage_audit.csv` | CBSA coverage summary and eligibility/model OOF flags. | All-period descriptive coverage and A6 development eligibility. | A5 flag uses fixed 100-row/5-sector/10-year screen; not a model-reliability or training-eligibility claim. |
| `metadata_source_manifest` in canonical database | Used-source names, agencies, datasets, source vintages. | Source acquisition metadata. | Dashboard source catalog includes only BDS MSA-by-Sector, QCEW, CBP, ACS, CBSA/NAICS references used, and the finalized A6 outputs. |

## Dataset Lineage and Semantics

- `dashboard_msa_industry_year`: canonical view fields; A6 expected/residual/`gap_p20` joined only from fold-validation labels by CBSA, sector, and target year; A5/A6 coverage joined many-to-one by CBSA. Historical descriptive `year` remains distinct from `gap_label_predictor_year`. No predicted probability or risk category is put into this grain.
- `dashboard_model_predictions`: development logistic/HGB OOF records joined on exact pair keys, then final A6 holdout records appended with explicit split role. `actual_gap` is the realized target for the pair; predictor and target years remain separate. HGB is sensitivity; logistic remains primary.
- `dashboard_model_summary`: exact A6 performance values reshaped long; split, model, sample size, and prevalence remain explicit.
- `dashboard_calibration`: development benchmark/logistic bins from A6 baseline calibration, development HGB bins from A6 advanced calibration, and holdout bins from final A6 calibration. No new bins/calibration model are computed.
- `dashboard_model_by_year`, `dashboard_model_by_sector`, `dashboard_model_by_msa_size`: finalized holdout tables with source metrics preserved; sector names are joined to the canonical reference only.
- `dashboard_coverage`: A5 counts/eligibility and A6 development OOF count/eligibility; first/last year independently summarized from the read-only panel. Threshold rule is documented in `ASSIGNMENT7_COVERAGE_POLICY.md`.
- `dashboard_sources`: curated actual-input source manifest plus A6 finalized research outputs; no unused source or invented citation.

## Temporal and Model Boundary

Historical panel rows, development OOF predictions, and final holdout predictions are separate concepts and files. The A6 holdout contains 10,304 final eligible pairs. No holdout probability/actual gap is propagated into the historical descriptive panel; no final model is fit again; no p20 threshold or label is recreated. Risk category is omitted because A7.1 did not freeze a non-holdout category rule. Source database remains read-only.

## A7.6 Performance Diagnostics

- Fixed KPI cards, model comparisons, and lift values come from
  `dashboard_model_summary`; calibration points come from
  `dashboard_calibration`; target-year, MSA-size, and sector results come from
  their matching finalized A7.2 tables. The primary/sensitivity hierarchy is
  read from A7.2 metadata and labels.
- Pointwise PR and ROC chart coordinates are created deterministically from
  `dashboard_model_predictions`: the selected split's `actual_gap` is the
  observed label and the unchanged logistic/HGB probability is the score. The
  transformation uses standard precision-recall and ROC coordinate
  calculations only. It does not train or refit a model, alter scores, choose
  a threshold, or recalculate the published summary metrics. The split is
  always explicit, and the PR/ROC references are prevalence and random
  ranking, respectively. This narrow transformation is approved in the A7.2
  logical contracts for A7.6 presentation only.
- Risk-concentration table values display the frozen top-10/20/25 lift and
  prevalence from `dashboard_model_summary`; observed prevalence within each
  share is shown as lift multiplied by overall prevalence. Selected N follows
  the finalized A6 ceiling-of-fraction rule. No row-level outcome metric is
  recomputed.
- Sector metrics and `sufficient_sample_flag` are used as published. The chart
  includes only sufficient logistic sectors; the table preserves all sectors
  and blank A6-suppressed metrics. Random Forest is omitted because the frozen
  A7.2 model summary contains no Random Forest rows.

## A7.7 Data Quality & Limitations

- MSA coverage, A5 eligibility, A6 OOF participation, and sector support use
  the matching validated A7.2 coverage and subgroup artifacts; source catalog
  fields come from `dashboard_sources`.
- Complete-case counts and inclusion/exclusion comparisons are displayed from
  `a6_gap_complete_case_selection.csv` and `a6_sample_selection_audit.csv`;
  unseen-MSA results are displayed from `a6_geographic_generalization.csv`.
  The page does not recompute model, target, or sample-selection statistics.
- Missing values and A6-suppressed sector metrics remain unavailable. The A5
  coverage screen is not described as a model-confidence or quality measure.
