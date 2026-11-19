# Presentation Data Provenance

All presentation values are reformatted from frozen committed Assignment 4–7 outputs. The presentation does not retrain models, recalculate targets, or alter predictions.

| Slide | Claim | Canonical source | Exact field / value |
|---:|---|---|---|
| 1, 5 | Study period 2010–2023 | `reports/assignment4_final_quality_report.md` | production panel year range |
| 5 | 63,577 observations; 381 MSAs; 19 sectors | `reports/assignment4_final_quality_report.md`; `reports/assignment4_merge_audit.md` | canonical panel counts |
| 5 | BDS / QCEW / ACS / CBP roles | `docs/ANALYTICAL_PANEL.md`; `reports/assignment4_final_review.md` | source lineage and analytical fields |
| 5 | July 2023 CBSA; 2022 NAICS | `docs/ANALYTICAL_PANEL.md`; Assignment 4 geography and industry reference documentation | standardized reference vintages |
| 6 | Alignment = observed minus expected | `reports/assignment6_entrepreneurial_gap_target.md` | `alignment_residual` construction |
| 6 | p20 gap threshold | `reports/assignment6_entrepreneurial_gap_target.md`; `docs/ASSIGNMENT6_DESIGN.md` | training-fold residual quantile = 0.20 |
| 7 | Development predictor years 2010–2017 | `docs/ASSIGNMENT6_TEMPORAL_FOLDS.md` | final-holdout training predictor range |
| 7 | Holdout predictors 2018–2020; targets 2021–2023 | `docs/ASSIGNMENT6_TEMPORAL_FOLDS.md` | exact t to t+3 final-holdout calendar |
| 7 | 12,091 exact calendar candidates | `docs/ASSIGNMENT6_TEMPORAL_FOLDS.md`; `reports/assignment6_final_analytics_engine.md` | `candidate_pairs = 12091` |
| 8 | Growth coefficient +3.502 | `reports/assignment5_relationship_hypothesis_analysis.md` | year-sector controlled employment-growth coefficient = 3.502 |
| 8 | 5-point growth difference → +0.175 startup-rate points | same as above | 3.502 × 0.05 = 0.1751, displayed 0.175 |
| 8 | Pooled lag-1 0.690; within-panel 0.077 | `reports/assignment5_final_eda_report.md` | lag-1 Pearson values |
| 8 notes | Simulated null ≈ −0.085 | Assignment 5 persistence/null output documented in project artifacts | null reference, rounded |
| 9 | OLS expected model; Logistic primary; HGB sensitivity | `reports/assignment6_expected_entrepreneurship_model.md`; `reports/assignment6_final_analytics_engine.md` | locked model roles |
| 10 | Logistic AP 0.404225 → 0.404 | `reports/assignment6_bootstrap_uncertainty.md`; `reports/tables/a6_final_model_performance.csv` | `average_precision = 0.404225` |
| 10 | Prevalence 0.232531 → 23.3% | `reports/tables/a6_final_model_performance.csv`; `reports/assignment6_final_analytics_engine.md` | holdout prevalence |
| 10 | ROC-AUC 0.692; Brier 0.164 | `reports/tables/a6_final_model_performance.csv` | Logistic holdout metrics |
| 10 | Top-decile lift 1.99× | `reports/tables/a6_final_model_performance.csv`; `reports/assignment6_final_analytics_engine.md` | `top_decile_lift = 1.985`, rounded |
| 10 notes / B1 | Recall 70.8%; precision 32.8% at development threshold | `reports/tables/a6_final_model_performance.csv` | frozen-threshold holdout metrics |
| 11 | Logistic AP CI 0.380–0.429 | `reports/assignment6_bootstrap_uncertainty.md`; `reports/tables/a6_holdout_ap_cluster_bootstrap.csv` | percentile CI [0.380018, 0.429251] |
| 11 | HGB AP 0.424; CI 0.398–0.450 | same sources | observed HGB AP and percentile CI |
| 11 | HGB − Logistic +0.020; CI +0.006 to +0.034 | same sources | 0.020014; [0.005531, 0.033684] |
| 11 | 48.7% exceed +0.02 | `reports/assignment6_bootstrap_uncertainty.md` | practical-threshold exceedance |
| 11 | 2/3 development folds; pooled +0.004 | `reports/assignment6_bootstrap_uncertainty.md`; Assignment 6 development model tables | predeclared model-selection evidence |
| 11 visual | Bootstrap distribution | `reports/figures/a6_holdout_ap_difference_bootstrap.png` | copied without data alteration |
| 12 | AP sequence 0.233 / 0.325 / 0.404 / 0.424 | `reports/assignment6_sector_only_benchmark.md`; `reports/tables/a6_sector_only_model_comparison.csv` | prevalence, sector-only, Logistic, HGB |
| 12 | Logistic incremental AP +0.079; CI +0.061 to +0.098 | same sources | paired cluster-bootstrap comparison |
| 12 | Logistic beats sector prevalence in 17/17 evaluable sectors | `reports/tables/a6_sector_within_logistic_ranking.csv`; `reports/assignment6_sector_only_benchmark.md` | evaluable-sector count |
| 13 | 1,031 reviewed; 476 gaps; 555 non-gaps | `reports/tables/a6_decision_rule_comparison.csv`; `reports/assignment6_decision_calibration.md` | top-10% row counts |
| 13 | Precision 46.2%; recall 19.9%; lift 1.99×; FP/TP 1.17 | same sources | top-10% decision metrics |
| 14 | 12,091 candidates; 10,304 scoreable; 85.2%; 14.8% | `reports/assignment6_holdout_drift_and_coverage.md`; `reports/assignment6_final_analytics_engine.md` | holdout candidate / eligible counts |
| 14 | Small / middle / large exclusion 17.3% / 10.7% / 6.6% | `reports/tables/a6_holdout_exclusion_by_msa_size.csv` | `excluded_rate` by MSA-size group |
| 15 | Development prevalence 19.1%; holdout 23.3% | `reports/tables/a6_holdout_drift_summary.csv`; `reports/assignment6_holdout_drift_and_coverage.md` | period prevalence |
| 15 | Observed startup increased; composition explains little | `reports/tables/a6_holdout_drift_summary.csv`; `reports/tables/a6_holdout_composition_standardization.csv` | mean startup and standardized prevalence results |
| 16 | Pittsburgh case: 14 observed years, 4 comparison years, 3 prediction records | running frozen A7 Explorer; `data/dashboard/dashboard_model_predictions.parquet`; frozen dashboard panel | visible selected-state counts |
| 16 | Pittsburgh target-2023 Logistic 0.439518; HGB 0.384180 | `reports/tables/a6_final_holdout_predictions.csv` | CBSA Pittsburgh, sector 71, predictor 2020, target 2023 |
| 16 screenshot | Actual current dashboard | `assets/screenshots/pittsburgh-arts-explorer.png` | captured from local Streamlit Explorer with selected filters |
| 17 | Supported / unsupported conclusions | `reports/assignment6_final_analytics_engine.md`; `docs/ASSIGNMENT6_LIMITATIONS.md` | final evidence classification and documented boundaries |

## Visual asset lineage

- `assets/figures/bootstrap-ap-difference.png` is a byte-for-byte copy of `reports/figures/a6_holdout_ap_difference_bootstrap.png`.
- `assets/figures/sector-benchmark.png` is a byte-for-byte copy of `reports/figures/a6_sector_only_ap_comparison.png`.
- `assets/figures/holdout-shift.png` is a byte-for-byte copy of `reports/figures/a6_holdout_alignment_evidence.png` and is retained for reviewer/backup use.
- All other diagrams and charts are native HTML/CSS encodings of the frozen values listed above.
