# Synthetic Reviewer Sources

All records are fictional and generated deterministically by
`regional_entrepreneurship_intelligence.review.build_reviewer_fixture`. The
builder writes seven compact CSVs here so they can be inspected and committed;
it does not read production caches or make network calls.

| File | Shape and purpose |
| --- | --- |
| `bds_msa_sector.csv` | BDS MSA-sector backbone, years 2010-2023, two fictional MSAs and sectors 11/54; also includes one intentionally unmapped code. |
| `bds_msa_sector_age.csv` | Firm-age-coarse age-0 records for startup numerator; has a true zero, a Census-style `D` suppression, and an unmapped row. |
| `qcew_county_sector.csv` | County-sector annual employment records for 2017-2023; exercises county-to-CBSA aggregation and growth/lag creation. |
| `acs_metro_controls.csv` | Five regional controls for 2017-2023. One unemployment estimate is blank to test missingness preservation. |
| `cbp_county_sector.csv` | Fictional CBP county-sector records for 2022-2023, with unsuppressed counts. |
| `synthetic_cbsa_county_crosswalk.csv` | Fictional county GEOIDs 99001/99003 mapped to fictional CBSA 99901/99902 using the July 2023 schema. |
| `synthetic_naics_crosswalk.csv` | Identity-compatible fictional mappings for sectors 11/54 and an explicitly unmatched synthetic code 98. |

The expected final core is 2 MSAs x 2 sectors x 7 years, less the single
suppressed BDS MSA-sector-year: **27 rows**. The 2019 CBSA 99902 / sector 54
record is excluded from the core because startup count is suppressed, not zero.
The 2018 CBSA 99901 / sector 11 age-0 count is a real synthetic zero and should
remain a valid zero startup rate. The missing ACS control remains null and does
not remove a BDS-QCEW core row. The unmapped geography/sector records are audited
but do not enter the final analytical panel.

The analytical key is CBSA x 2022 NAICS 2-digit sector x year. The fixture
contains a 2020-to-2023 exact three-calendar-year pair for each surviving panel;
lags use prior calendar years only. These are test values, not observations or
estimates about any real place, industry, or business population.
