# Data Feasibility Assessment

## Research Design Tested

- Anticipated unit of analysis: Metropolitan Statistical Area x 2-digit NAICS Industry x Year
- Pilot geography: five Metropolitan Statistical Areas verified against BLS QCEW area titles
- Pilot years: 2018-2023 where available
- Industry level: 2-digit NAICS sectors

## Pilot Geography

| pilot_label | cbsa_code | qcew_area_fips | official_name | states |
| --- | --- | --- | --- | --- |
| Huntsville, AL | 26620 | C2662 | Huntsville, AL MSA | AL |
| Nashville, TN | 34980 | C3498 | Nashville-Davidson--Murfreesboro--Franklin, TN MSA | TN |
| Chattanooga, TN-GA | 16860 | C1686 | Chattanooga, TN-GA MSA | TN-GA |
| Florence-Muscle Shoals, AL | 22520 | C2252 | Florence-Muscle Shoals, AL MSA | AL |
| Austin, TX | 12420 | C1242 | Austin-Round Rock-San Marcos, TX MSA | TX |

## Source Assessment

| Source | Available years tested | Geography tested | MSA x sector exists | Industry resolution | Key variables | Identifiers | Suppression notes | Download/API method |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Business Dynamics Statistics (BDS) | 1978-2023 in 2023 time-series bulk files | MSA via BDS MSA-sector bulk file; metro/nonmetro also available separately | Yes, in bds2023_msa_sec.csv | 2-digit NAICS sector | firms, estabs, estabs_entry, estabs_entry_rate, job_creation_births, job_creation_rate_births | msa, sector, year | Bulk file tested has numeric released values; Census API documents indicator flags for suppression/disclosure in API responses | Official Census bulk CSV; Census API now requires an API key for data queries |
| Quarterly Census of Employment and Wages (QCEW) | 2018-2023 annual averages | Official BLS MSA area codes | Yes, through annual area slices filtered to 2-digit NAICS, private ownership | 2-digit NAICS plus higher/lower aggregation levels | annual_avg_emplvl, annual_avg_estabs, total_annual_wages, avg_annual_pay | area_fips, industry_code, year | Suppressed cells are absent from published data slices rather than explicitly present as rows | Official BLS QCEW Open Data CSV slices |
| County Business Patterns (CBP) | 2022 bulk file; API data access requires a Census API key | MSA/micropolitan supported by documentation; keyless API blocked | Supported by Census CBP API documentation, but pilot API retrieval requires key | 2- through 6-digit NAICS in CBP documentation | ESTAB, EMP, PAYANN, PAYQTR1 and flags | CBSA, NAICS, YEAR | Employment/payroll use flags/noise indicators; API exposes EMP_F, PAYANN_F, PAYQTR1_F | Census API requires key; bulk files can support offline validation after download |
| American Community Survey (ACS) | 2018-2023 ACS 1-year profile endpoint metadata; data API requires key | Metropolitan/micropolitan statistical area | No industry dimension; joins as CBSA x year controls | Not applicable for regional controls | population, median household income, educational attainment, labor-force participation, unemployment | CBSA, YEAR | ACS margins of error and population thresholds matter; not a cell-suppression structure like business data | Census API requires key for data queries |

Official sources consulted:

- Census BDS bulk time-series files: https://www2.census.gov/programs-surveys/bds/tables/time-series/2023/
- Census BDS API documentation and variables: https://www.census.gov/programs-surveys/bds/data.API.html
- BLS QCEW Open Data Access: https://www.bls.gov/cew/additional-resources/open-data/home.htm
- BLS QCEW data files and availability documentation: https://www.bls.gov/cew/downloadable-data-files.htm
- Census CBP API documentation: https://www.census.gov/data/developers/data-sets/cbp-zbp/cbp-api.2020.html
- Census ACS API variables: https://api.census.gov/data/2023/acs/acs1/profile/variables.html

## BDS Entrepreneurship Feasibility

| measure | available_rows | missing_rows | percent_missing | zero_rows | percent_zero | suppressed_rows | usable_msa_sector_year_cells | total_candidate_cells |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| estabs_entry | 530 | 40 | 7.0 | 35 | 6.1 | 0 | 530 | 570 |
| estabs_entry_rate | 525 | 45 | 7.9 | 30 | 5.3 | 0 | 525 | 570 |
| job_creation_births | 530 | 40 | 7.0 | 35 | 6.1 | 0 | 530 | 570 |
| job_creation_rate_births | 525 | 45 | 7.9 | 30 | 5.3 | 0 | 525 | 570 |
| firms | 569 | 1 | 0.2 | 5 | 0.9 | 0 | 569 | 570 |
| estabs | 569 | 1 | 0.2 | 5 | 0.9 | 0 | 569 | 570 |

BDS supports the requested MSA x sector x year concept through the official `bds2023_msa_sec.csv` time-series bulk file. In the pilot extract, establishment entry rate is normalized, interpretable, and mostly complete, making it the best primary entrepreneurship measure for Assignment 3 design work.

## Entrepreneurship Measure Recommendation

- Best primary measure: `estabs_entry_rate`
- Backup measures: `estabs_entry` and `job_creation_births`
- Completeness: `estabs_entry_rate` was usable for 525 of 570 selected MSA x sector x year cells; raw entry and startup job-creation birth counts were usable for 530 of 570 cells.
- Important limitation: raw startup or entry counts should not be compared across MSAs without normalization because metro economies differ greatly in size.

## QCEW Industry-Growth Feasibility

| measure | available_rows | missing_rows | percent_missing | zero_rows | percent_zero | suppressed_rows | usable_msa_sector_year_cells | total_candidate_cells |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| annual_avg_emplvl | 570 | 0 | 0.0 | 106 | 18.6 | 106 | 570 | 570 |
| annual_avg_estabs | 570 | 0 | 0.0 | 0 | 0.0 | 106 | 570 | 570 |
| total_annual_wages | 570 | 0 | 0.0 | 106 | 18.6 | 106 | 570 | 570 |
| avg_annual_pay | 570 | 0 | 0.0 | 106 | 18.6 | 106 | 570 | 570 |

QCEW supports employment, establishments, total annual wages, and average annual pay for pilot MSA-sector-year observations. Year-over-year employment growth, establishment growth, nominal payroll growth, and nominal wage growth can be calculated after sorting by MSA, sector, and year.

## Industry Growth Recommendation

- Usable components: employment growth, establishment growth, nominal payroll growth, and nominal wage growth.
- Problematic components: payroll and wage growth require inflation adjustment before being described as real growth.
- Composite feasibility: an equal-weight standardized composite is technically feasible for rows with all four growth measures, but weights should remain provisional until the research design is finalized.

## CBP Assessment

CBP documentation supports MSA/micropolitan/county geographies and 2- through 6-digit NAICS detail with establishments, employment, first-quarter payroll, annual payroll, and suppression flags. In this run, the Census API redirected data queries to a missing-key page, so CBP should be treated as feasible but not yet empirically matched until a Census API key is available.

## ACS Assessment

ACS profile metadata supports Metropolitan Statistical Area/Micropolitan Statistical Area geography and regional control variables such as population, income, educational attainment, labor-force participation, and unemployment. In this run, the Census API redirected data queries to a missing-key page, so ACS should be joined after adding a Census API key.

## Merge Assessment

| metric | value |
| --- | --- |
| BDS pilot rows | 570.0 |
| QCEW pilot rows | 570.0 |
| Outer merged rows | 570.0 |
| Rows matched BDS and QCEW | 570.0 |
| BDS-only rows | 0.0 |
| QCEW-only rows | 0.0 |
| BDS-QCEW match percentage of merged rows | 100.0 |

The BDS-QCEW merge matched 100.0% of merged pilot rows. ACS controls were represented as a join-ready placeholder because live ACS data queries require a Census API key.

## Gap Concept Assessment

The expected-vs-observed entrepreneurship concept is technically feasible as a diagnostic exercise using BDS establishment entry rate and QCEW growth variables. The diagnostic model result was:

```json
{
  "estimable": true,
  "nobs": 366,
  "rsquared": 0.637,
  "note": "Diagnostic OLS only; not a final model."
}
```

Threshold sensitivity:

| threshold | gap_observations | percent_gap | top_gap_industries | gap_count_by_msa |
| --- | --- | --- | --- | --- |
| bottom_10_percent | 37 | 10.1 | {'48-49': 4, '56': 4, '51': 4, '11': 3, '71': 3} | {'Florence-Muscle Shoals, AL': 14, 'Huntsville, AL': 8, 'Nashville, TN': 6, 'Austin, TX': 5, 'Chattanooga, TN-GA': 4} |
| bottom_20_percent | 74 | 20.2 | {'56': 7, '53': 6, '51': 6, '71': 6, '11': 5} | {'Huntsville, AL': 18, 'Florence-Muscle Shoals, AL': 17, 'Austin, TX': 14, 'Nashville, TN': 13, 'Chattanooga, TN-GA': 12} |
| bottom_25_percent | 92 | 25.1 | {'53': 8, '56': 8, '71': 8, '48-49': 7, '51': 7} | {'Huntsville, AL': 23, 'Florence-Muscle Shoals, AL': 20, 'Austin, TX': 19, 'Nashville, TN': 16, 'Chattanooga, TN-GA': 14} |
| below_minus_1_sd | 34 | 9.3 | {'48-49': 4, '56': 4, '51': 4, '11': 3, '22': 3} | {'Florence-Muscle Shoals, AL': 13, 'Huntsville, AL': 8, 'Austin, TX': 5, 'Chattanooga, TN-GA': 4, 'Nashville, TN': 4} |

These thresholds are practical for sensitivity testing, but none should be finalized before Assignment 3 defines the research design.

## Historical Window Recommendation

A 2010-2023 full-project window is recommended over 2005-2023 for the first complete study design. It keeps enough history for lagged features and a possible three-year prediction horizon while reducing risks from changes in MSA boundaries, industry classification, and ACS availability. A longer 2005-2023 window may be possible but should be treated as a robustness extension after geography and NAICS consistency are resolved.

## Feasibility Scorecard

| Category | Result | Rationale |
| --- | --- | --- |
| Entrepreneurship data | PASS | BDS MSA-sector-year bulk data support establishment entry and startup job-creation measures. |
| Industry-growth data | PASS | QCEW supports MSA-sector-year employment, establishments, payroll, and wage measures for the pilot. |
| MSA-industry-year join | PASS WITH LIMITATIONS | BDS and QCEW match well; CBP/ACS require Census API-key access for full empirical matching. |
| Three-year prediction horizon | PASS WITH LIMITATIONS | 2010-2023 likely supports lag/target construction, but 2021-2023 targets constrain recent horizons. |
| National replicability | PASS WITH LIMITATIONS | Official CBSA/NAICS/year identifiers support replication, subject to suppression and boundary harmonization. |

## Final Recommendation

**GO WITH MODIFICATIONS**

The proposed project is empirically supportable enough to write Assignment 3 confidently, provided the design acknowledges three implementation limits: Census API-key access is needed for CBP and ACS retrieval, geography should use stable CBSA definitions or a documented crosswalk, and payroll/wage growth should be inflation-adjusted before being interpreted as real growth.
