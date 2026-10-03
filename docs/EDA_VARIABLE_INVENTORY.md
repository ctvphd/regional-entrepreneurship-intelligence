# EDA Variable Inventory

## Scope And Source Of Truth

This inventory describes the 61 fields exposed by `v_analytics_msa_industry_year` in the Assignment 4 production database (`database/assignment4_production.sqlite`). It follows the active view, `docs/data_dictionary.md`, `docs/ANALYTICAL_PANEL.md`, source transformation documentation, and `database/schema.py`. The empty `database/regional_entrepreneurship.sqlite` is a legacy development database and is not the EDA input.

The active view contains 57 stored analytical/support fields plus four display labels (`cbsa_code`, `cbsa_name`, `sector_code`, `sector_title`). Its row grain is MSA x 2022 NAICS broad sector x year. All monetary figures retain documented source units/vintages; income is not common-year deflated, QCEW payroll is dollars, and CBP payroll is native $1,000.

`analytics_msa_industry_year` physically contains seven retired compatibility aliases (`employment`, `establishments`, `payroll`, `average_wage`, `population`, `business_structure_establishments`, `business_structure_employment`), documented in `data_dictionary.md`; they are all NULL in the production copy and are excluded from the active view and this inventory. The source-intermediate alias `lagged_startup_rate` is also omitted from the view; use explicit `startup_rate_lag1` for active EDA. `pipeline_run_id` is lineage metadata in the physical table, not an active view field.

## Field Inventory

All active numeric values are SQLite `INTEGER` or `REAL` as noted by the field's definition; labels and notes are `TEXT`. “EDA use” distinguishes substantive analysis from diagnostic or display-only use. Rate fields are stored in percentage units when the source definition says percentage; growth fields are simple decimal rates, not percentage points.

| Field | Source | Type | Conceptual role | Expected unit / meaning | EDA use | Exclude from substantive analysis? |
|---|---|---|---|---|---|---|
| `geography_id` | Reference | INTEGER | Identifier | Internal MSA geography key | Join/group key | Yes, not a measure |
| `industry_id` | Reference | INTEGER | Identifier | Internal 2022 NAICS sector key | Join/group key | Yes, not a measure |
| `year` | Reference | INTEGER | Identifier/time | Calendar year, 2010-2023 | Time summaries | No |
| `cbsa_code` | Census reference | TEXT | Identifier/display | CBSA code | Labels and geography checks | Yes, not a measure |
| `cbsa_name` | Census reference | TEXT | Identifier/display | CBSA name | Labels | Yes, not a measure |
| `sector_code` | NAICS reference | TEXT | Identifier/display | 2022 NAICS sector code | Sector grouping | Yes, not a measure |
| `sector_title` | NAICS reference | TEXT | Identifier/display | 2022 NAICS sector title | Sector labels | Yes, not a measure |
| `startup_rate` | BDS | REAL | Entrepreneurship | Age-0 firms / all firms x 100 | Primary descriptive measure | No |
| `firm_startups` | BDS | REAL | Entrepreneurship | Source-defined age-0 firm count/measure | Supporting count | No; distinguish from rate |
| `startup_rate_lag1` | BDS | REAL | Entrepreneurship, lag | Prior calendar-year startup rate, percent | Persistence summaries | No; historical only |
| `startup_rate_lag2` | BDS | REAL | Entrepreneurship, lag | Two-calendar-year lagged rate, percent | Supporting persistence | No; historical only |
| `startup_rate_lag3` | BDS | REAL | Entrepreneurship, lag | Three-calendar-year lagged rate, percent | Supporting persistence | No; historical only |
| `establishment_entry` | BDS | REAL | Entrepreneurship | Establishment entry/birth measure | Supporting alternative | No; not firm startups |
| `establishment_entry_rate` | BDS | REAL | Entrepreneurship | Source-defined establishment entry rate | Supporting alternative | No; not firm startup rate |
| `startup_job_creation` | BDS | REAL | Entrepreneurship | Jobs created by startup firms | Supporting measure | No |
| `qcew_employment` | QCEW | REAL | Industry growth/level | Annual employment level; source units | Level distributions/context | No |
| `qcew_establishments` | QCEW | REAL | Industry growth/level | Annual establishment count | Level distributions/context | No |
| `qcew_payroll` | QCEW | REAL | Industry growth/level | Payroll, nominal dollars per dictionary | Supporting level | No; retain source label |
| `qcew_average_wage` | QCEW | REAL | Industry growth/level | QCEW average wage/pay measure | Supporting level | No; nominal/source definition |
| `qcew_total_annual_wages_nominal` | QCEW | REAL | Industry growth/level | Total annual wages, nominal dollars | Supporting level | No; not inflation adjusted |
| `qcew_average_annual_pay_nominal` | QCEW | REAL | Industry growth/level | Recalculated average annual pay, nominal | Supporting level | No; not inflation adjusted |
| `employment_growth` | QCEW | REAL | Industry growth | Annual simple employment growth rate | Primary growth measure | No |
| `establishment_growth` | QCEW | REAL | Industry growth | Annual simple establishment growth rate | Supporting growth measure | No |
| `payroll_growth` | QCEW | REAL | Industry growth | Annual simple payroll growth rate | Supporting growth measure | No |
| `wage_growth` | QCEW | REAL | Industry growth | Annual simple average-wage growth rate | Supporting growth measure | No |
| `employment_growth_lag1` | QCEW | REAL | Industry growth, lag | Prior-calendar-year employment growth | Historical predictor summaries | No |
| `employment_growth_lag2` | QCEW | REAL | Industry growth, lag | Two-year lagged employment growth | Historical predictor summaries | No |
| `employment_growth_lag3` | QCEW | REAL | Industry growth, lag | Three-year lagged employment growth | Historical predictor summaries | No |
| `establishment_growth_lag1` | QCEW | REAL | Industry growth, lag | Prior-calendar-year establishment growth | Supporting historical measure | No |
| `establishment_growth_lag2` | QCEW | REAL | Industry growth, lag | Two-year lagged establishment growth | Supporting historical measure | No |
| `establishment_growth_lag3` | QCEW | REAL | Industry growth, lag | Three-year lagged establishment growth | Supporting historical measure | No |
| `payroll_growth_lag1` | QCEW | REAL | Industry growth, lag | Prior-calendar-year payroll growth | Supporting historical measure | No |
| `average_pay_growth_lag1` | QCEW | REAL | Industry growth, lag | Prior-calendar-year average-pay growth | Supporting historical measure | No |
| `acs_population` | ACS | REAL | Regional control | Population estimate, MSA-year | Regional context | No; repeated across sectors by design |
| `acs_population_growth` | ACS | REAL | Regional control | Annual population growth rate | Core regional context | No; repeated across sectors by design |
| `acs_population_growth_lag1` | ACS | REAL | Regional control, lag | Prior-year population growth | Historical regional context | No; repeated across sectors by design |
| `median_household_income` | ACS | REAL | Regional control | ACS estimate in release-adjusted dollars | Core regional context | No; not common-year deflated |
| `median_household_income_lag1` | ACS | REAL | Regional control, lag | Prior-year ACS income estimate | Historical regional context | No; same dollar caveat |
| `educational_attainment_pct` | ACS | REAL | Regional control | ACS profile educational attainment percent | Core regional context | No; concept definition follows ACS registry |
| `educational_attainment_pct_lag1` | ACS | REAL | Regional control, lag | Prior-year education percentage | Historical regional context | No |
| `labor_force_participation_pct` | ACS | REAL | Regional control | ACS labor-force participation percent | Core/supporting context | No |
| `labor_force_participation_pct_lag1` | ACS | REAL | Regional control, lag | Prior-year participation percentage | Historical regional context | No |
| `unemployment_rate` | ACS | REAL | Regional control | ACS unemployment percentage | Core regional context | No |
| `unemployment_rate_lag1` | ACS | REAL | Regional control, lag | Prior-year unemployment percentage | Historical regional context | No |
| `cbp_establishments` | CBP | REAL | Business structure | Establishment count | Supporting/validation only | No; not interchangeable with QCEW |
| `cbp_employment` | CBP | REAL | Business structure | CBP employment measure | Supporting/validation only | No; not interchangeable with QCEW |
| `cbp_annual_payroll` | CBP | REAL | Business structure | Annual payroll, native $1,000 | Supporting/validation only | No; honor native units |
| `cbp_first_quarter_payroll` | CBP | REAL | Business structure | First-quarter payroll, native $1,000 | Supporting/validation only | No; honor native units |
| `bds_has_suppression` | BDS | INTEGER | Quality flag | 0/1 suppression indicator | Missingness/quality stratification | Yes, not a substantive predictor by default |
| `bds_startup_available` | BDS | INTEGER | Quality flag | 0/1 startup availability | Availability diagnostic | Yes, not a substantive predictor by default |
| `qcew_has_suppression` | QCEW | INTEGER | Quality flag | 0/1 suppression indicator | Missingness/quality stratification | Yes, not a substantive predictor by default |
| `qcew_is_complete_county_coverage` | QCEW | INTEGER, nullable | Quality flag | 1 complete, 0 incomplete, NULL unknown | Coverage diagnostic | Yes, not a substantive predictor by default |
| `qcew_is_real_adjusted` | QCEW | INTEGER | Quality flag | 0/1 real-adjustment indicator | Definition diagnostic | Yes; values are not assumed adjusted |
| `acs_matched` | ACS | INTEGER | Quality flag | 0/1 MSA-year match | Coverage diagnostic | Yes, not a substantive predictor by default |
| `acs_has_suppression` | ACS | INTEGER | Quality flag | 0/1 suppression indicator | Missingness/quality stratification | Yes, not a substantive predictor by default |
| `acs_has_missing_controls` | ACS | INTEGER | Quality flag | 0/1 missing-control indicator | Missingness diagnostic | Yes, not a substantive predictor by default |
| `cbp_matched` | CBP | INTEGER | Quality flag | 0/1 CBP match | Coverage diagnostic | Yes, not a substantive predictor by default |
| `cbp_has_suppression` | CBP | INTEGER | Quality flag | 0/1 suppression indicator | Missingness/quality stratification | Yes, not a substantive predictor by default |
| `cbp_is_complete_county_coverage` | CBP | INTEGER, nullable | Quality flag | 1 complete, 0 incomplete, NULL unknown | Coverage diagnostic | Yes, not a substantive predictor by default |
| `has_suppression` | Integration QA | INTEGER | Quality flag | 0/1 combined suppression indicator | Diagnostic only; source-specific flags preferred | Yes, not a substantive predictor by default |
| `source_quality_notes` | Integration QA | TEXT | Metadata/supporting | Human-readable source-quality/join notes | Audit only | Yes, not numeric/substantive |

The 61 fields are partitioned in `analysis.eda.VARIABLE_GROUPS`. Lags remain within their conceptual domain and are additionally identified by the `_lagN` suffix. The human-readable code/title fields are identifiers, not numerical measures. No formal target or future outcome is present.

## Preliminary Variable Tiers

- **Tier 1, core:** `startup_rate`, `employment_growth`, `year`, `sector_code`, `cbsa_code`, `acs_population_growth`, `unemployment_rate`, `educational_attainment_pct`, `median_household_income`.
- **Tier 2, supporting:** employment/establishment/payroll levels and growth, all explicit lags, startup counts, establishment entry measures, startup job creation, labor-force participation, and CBP support measures.
- **Tier 3, diagnostic/quality:** suppression, availability, match, missing-control, and county-coverage flags; `source_quality_notes`; display labels and internal keys are identifiers rather than analysis variables.

Tier status prioritizes planned EDA, not a final model feature decision. ACS measures are repeated across industries by design; CBP is supporting/validation data and is not interchangeable with QCEW.
