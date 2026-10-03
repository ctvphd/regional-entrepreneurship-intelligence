# Assignment 4 Final Quality Report

This report records verified national production coverage and the final integration definition. The production database and source files are local, ignored artifacts; source and intermediate counts were stable across three complete cache-only A4.13 runs.

## Database And Source Layers

The SQLite database is `database/assignment4_production.sqlite`, locally 5,793,292,288 bytes (about 5.79 GB decimal) after repeated A4.13 runs; it is Git-ignored. It was about 4.74 GB beforehand. Append-only run/rejection audit history explains the growth; source fact and analytics cardinalities remained stable. Counts are raw/staging/intermediate rows.

| Source | Raw | Staging | Intermediate | Documented quality/exclusion count |
|---|---:|---:|---:|---|
| BDS | 492,100 across MSA-sector and firm-age tables | 246,050 | 178,382 all geographies; 88,562 MSA | 67,668 staged startup measures unavailable upstream: 53,855 age-0 numerator suppression, 10,931 denominator suppression, 2,882 zero denominators. |
| QCEW | 811,113 | 245,012 | 179,731 | 384,589 rows rejected/excluded by source transformation; 65,281 incomplete county-aggregation groups tracked separately. |
| ACS | 27,075 | 5,415 | 5,194 | 221 rows rejected/unmapped; five profile concepts with paired MOEs. Education concept uses year-specific IDs. |
| CBP | 755,249 | 755,249 | 189,474 | 374,302 rows rejected/excluded. The integrated panel reports 5,331 mapped support groups unavailable and 4,877 suppression flags; these are not row-level rejection counts. |

The QCEW incomplete-group count is not additive to its raw rejection count. CBP flags/noise, missing values, incomplete county aggregation, and excluded county records are distinct states; none is converted to zero. BDS startup missingness is upstream source availability, not a fabricated startup count.

## Integrated Panel

- 63,577 rows; 381 metropolitan statistical areas; 19 common 2022 NAICS broad sectors; 2010-2023.
- 5,887 MSA-sector panels: 2,830 balanced over 14 years and 3,057 unbalanced.
- Duplicate source keys: zero in BDS (178,382 rows), QCEW (179,731), ACS (5,194), and CBP (189,474). Analytical duplicate keys: zero.
- BDS-QCEW inner core: 63,577 matched of 88,562 BDS and 71,800 QCEW keys. Match rates are 71.79% and 88.55%; 24,985 BDS-only and 8,223 QCEW-only keys do not enter the core.
- ACS left support: 60,039 matched (94.44%); 3,538 unmatched. CBP left support: 58,236 matched (91.60%); 5,341 unavailable. Neither support join reduces the core.

## Missingness And Cross-Source Checks

| Measure | Missing/unavailable rows | Share |
|---|---:|---:|
| Startup rate | 0 in accepted integrated core; upstream BDS missing cases are documented above | 0.00% |
| Startup-rate lags 1/2/3 | 8,683 / 12,978 / 17,171 | 13.66% / 20.41% / 27.01% |
| QCEW employment level | 0 | 0.00% |
| QCEW employment growth | 6,468 | 10.17% |
| ACS primary controls / selected one-year lags | 3,538 / 8,062 | 5.56% / 12.68% |
| CBP measures unavailable | 5,341 | 8.40% |

In 58,236 QCEW-CBP matched rows, employment/establishment/payroll correlations are 0.9932/0.7858/0.9834. Median absolute percentage differences are 10.64%/9.59%/10.85%. CBP payroll is multiplied by 1,000 for the comparison only; stored source units remain unchanged. Differences are diagnostics, not grounds to designate either source as truth.

## Bad-Record Actions

| Condition | Action |
|---|---|
| Unresolved geography or industry | Preserve source/staging evidence and mapping status where available; exclude unresolved records from standardized intermediate measures and report mapping counts. |
| Excluded ownership, geography scope, or invalid year | Exclude from the relevant analytical intermediate; retain source raw data and auditable reason/quality counts. |
| Incomplete county aggregation | Keep component/staging evidence and completeness counts; do not sum partial county sets into accepted QCEW/CBP intermediate values. |
| Suppression/noise | Preserve source flags; do not interpret as zero. Depending on source rules, retain flagged staging rows and exclude their group from complete aggregation. |
| Missing required startup measure | Retain BDS raw/staging and reason-specific missingness; do not create a startup value or include unusable measures in accepted entrepreneurship rows. |
| Invalid numeric value / missing required field | Source ingestion or transform raises/rejects with a reason; do not silently coerce to zero. |
| Duplicate source/intermediate key | Fail validation before rebuild/integration; duplicate analytical keys are prohibited by the declared grain. |
| Unmatched BDS/QCEW integration key | Count and exclude from the inner core, with BDS-only/QCEW-only totals reported. |
| Unmatched ACS/CBP support | Keep the BDS-QCEW core row; preserve null support measures and explicit match/completeness flags. |

Counts in source production reports refer to source-specific rejection/exclusion semantics and are not one common mutually exclusive “bad row” total. The integrated merge exclusions and unmatched support rows are separately counted above.

## A4.13 End-To-End Reproduction

Three full executions of `uv run python -m regional_entrepreneurship_intelligence.etl.run_pipeline` completed with cached production files and no downloads. Runs 2 and 3 used the finalized runner and returned identical source-stage counts, 63,577 panel rows, zero duplicates, 826,780 source-runner rejection/exclusion counts, 164,011 quality-warning condition observations, and zero errors. The warning total sums separate categories and is not a unique-record count: 67,668 BDS missing-startup observations, 65,281 QCEW incomplete aggregation groups, 700 unresolved ACS geography classifications, and 30,362 CBP incomplete aggregation groups. Source-level rejection/exclusion totals were BDS 67,668; QCEW 384,589; ACS 221; CBP 374,302. These source-specific measures are not a common mutually exclusive bad-row definition.

The two finalized panel builds produced identical **76 of 76** run-scoped quality metric values. Final database validation found zero duplicate analytical keys and zero `PRAGMA foreign_key_check` violations. Raw, staging, intermediate, and final fact row counts remained unchanged across runs. Run metadata and quality/rejection audit records are intentionally append-only, so the SQLite file grows with execution history; this growth does not represent duplicate analytical facts.

| Finalized run | Run ID | Runtime | Status |
|---|---|---:|---|
| 2 | `830f0111-34b4-4b5b-92fb-712b54f5b364` | 954.4 sec (15m 54s) | success |
| 3 | `533b07de-38c6-45db-a31d-7e27664a9636` | 2,087.8 sec (34m 48s) | success |

The first A4.13 run also succeeded with 63,577 rows, zero duplicates, and zero errors in 1,061.7 seconds (17m 42s). Timestamped logs are stored under ignored `logs/`.

## Reproducibility And Limitations

Production source file hashes, URLs, versions, and row counts are recorded in `metadata_source_manifest`; stage runs and quality metrics are in SQLite. Source transformations and panel integration have rerun/idempotency tests. All three complete orchestration runs and the finalized-run comparison are recorded above and in `reports/assignment4_final_review.md`.

Known limitations: unbalanced panels; Census/BLS disclosure and availability constraints; ACS estimates and margins of error; nominal QCEW dollar values are not inflation-adjusted; source timing/definitions differ; CBP payroll and QCEW payroll have different native units; and code overlap alone does not establish historical CBSA boundary equivalence. No future targets or model features are present.
