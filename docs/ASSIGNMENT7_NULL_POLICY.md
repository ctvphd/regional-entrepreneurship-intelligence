# Assignment 7 Data Null Policy

Nulls preserve source missingness and analytical eligibility. Never replace them with zero, carry values forward, impute in the dashboard, or silently drop a row. Parquet nulls are intentional and the UI must distinguish “not observed,” “not eligible,” and “not applicable” where the source permits.

| Dataset / field group | Why null can occur | Expected? | Dashboard behavior |
| --- | --- | --- | --- |
| `dashboard_msa_industry_year`: `cbsa_code`, `msa_name`, `sector_code`, `sector_name`, `year`, coverage fields | These are primary keys/reference and audited coverage. | No | Builder fails if missing. |
| Historical panel startup, lag, growth, ACS, and optional source measures | Source missingness, suppression, unavailable predecessor, unmatched geography/year, or incomplete county/source coverage. | Yes | Preserve null; show source match/suppression/coverage flags and do not plot as zero. |
| Panel `expected_startup_rate`, `alignment_residual`, `observed_historical_gap_status`, `gap_label_predictor_year`, `alignment_label` | Only A6 fold-validation target rows have approved expected rates/residuals/p20 labels; early/history rows outside those OOF target records have no such value. Holdout labels are deliberately kept out of this descriptive panel. | Yes | Show as unavailable; never extrapolate. Explain label is OOF/development and row year is the target year. |
| `dashboard_model_predictions`: keys, split, actual gap, probabilities, names, coverage | These finalized eligible predictions/labels are complete in A6 artifacts and join to audited MSA/sector references. | No | Builder fails for null. Holdout outcomes remain retrospective. |
| Prediction `fold` | Final holdout is one final refit, not an A6 development fold. | Yes for holdout only | Null for `final_holdout`; populated for `development_oof`. |
| `dashboard_model_summary`: metric `value` | Some metrics can be mathematically undefined for a one-class subgroup; the all-sample A6 table is expected to provide its published metric values. | Not expected in current summary | Retain source null if present and label; overall null values fail current QA until reviewed. Prevalence is never substituted for AP. |
| `dashboard_calibration`: bin metrics | Every emitted source bin has positive `n` and both predicted mean and observed rate. | No in current artifacts | Builder/QA should fail if required bin values or `n` are null. |
| `dashboard_model_by_year`: metrics | All current yearly holdout cells contain both classes and published scores. | No in current artifacts | Preserve source values; fail if a supposedly required field becomes null without updated policy. |
| `dashboard_model_by_sector`: AP/ROC-AUC | A6 suppresses unstable estimates for fewer than 30 positive events or no negative class. | Yes, specifically when `sufficient_sample_flag` is false | Preserve nulls and the flag. Do not calculate replacement scores. Explain suppression reason. |
| `dashboard_model_by_msa_size`: metrics and counts | Current finalized size groups are populated; future source limitations could yield unavailable values. | Not in current artifact | Preserve null, show unavailable, and require review if this occurs. |
| `dashboard_coverage`: identifiers, counts, years, status, note | Coverage is constructed for the complete analytical CBSA reference set and validated. | No | Builder fails on missing key/count/status. `model_eligible_flag` is false when no development OOF row, not null. |
| `dashboard_sources`: source metadata | The used-source manifest provides agency, dataset, and vintage metadata for included sources. | No for required fields | Missing source record/manifest is a build error; do not fabricate source attribution. |

`risk_category` is not a field in this data layer: A7.1 approved no frozen non-holdout cutpoints. Raw probabilities and rank can be shown; the UI must not map missing category to a default band.
