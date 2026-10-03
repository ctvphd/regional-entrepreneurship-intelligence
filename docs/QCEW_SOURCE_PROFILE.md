# QCEW Source Profile

## Source

Assignment 4.7 profiles the U.S. Bureau of Labor Statistics Quarterly Census of Employment and Wages (QCEW) annual CSV open-data files.

Primary source family:

- Product: QCEW NAICS-Based Annual CSV Data
- Preferred full-scale bulk pattern: `https://data.bls.gov/cew/data/files/{year}/csv/{year}_annual_by_area.zip`
- Committed sample: `data/raw/qcew/sample/qcew_annual_area_sample_2022_2023.csv`
- Sample access pattern: `https://data.bls.gov/cew/data/api/{year}/a/area/{area_fips}.csv`
- Access method: official BLS QCEW CSV open data

The full annual by-area zip for a single year is large, so A4.7 commits a small official sample only. Full 2010-2023 acquisition should use the annual by-area zip files and keep full raw files Git-ignored.

## Geography

Native geography field:

- `area_fips`

Native geography options:

- county-level FIPS codes are available in annual area files
- MSA-style area codes are available in QCEW open data, but historical MSA definitions may vary over time

Recommendation for A4.8:

- use county-level QCEW rows and aggregate to the fixed July 2023 CBSA standard through `ref_geography_county_crosswalk`

Rationale:

- the project uses a fixed July 2023 CBSA analytical geography
- county rows provide a clearer path to fixed-vintage CBSA aggregation
- direct historical MSA QCEW records risk silently mixing changing definitions

A4.7 does not perform the aggregation.

## Industry

Native industry field:

- `industry_code`

The annual NAICS-based files include aggregate and detailed industry codes, including sector-level codes and combined-sector codes where published. A4.7 preserves native QCEW industry codes in `raw_qcew`.

NAICS version behavior:

- QCEW files are NAICS-based, but the native NAICS vintage can vary over the 2010-2023 period as BLS updates classifications.
- A4.7 does not assume direct compatibility with the project's 2022 NAICS reference.

A4.8 must classify each source industry code as directly comparable, requiring official mapping, or unresolved before standardization.

## Ownership

Native ownership field:

- `own_code`

Ownership categories include total covered employment, federal government, state government, local government, and private sector.

Recommended analytical ownership scope:

- private sector (`own_code = 5`) for the industry-growth panel, unless a later research decision explicitly requires total covered employment.

Double-counting risk:

- do not combine total ownership rows with ownership-specific rows. `own_code = 0` already represents total covered employment.

The A4.7 sample includes private-sector rows for the planned analytical scope and a small number of non-private status rows to test disclosure handling.

## Measures

Annual QCEW source fields preserved for A4.7 include:

- `annual_avg_estabs`
- `annual_avg_emplvl`
- `total_annual_wages`
- `avg_annual_pay`

A4.7 does not calculate growth rates.

## Suppression

QCEW disclosure and status information is preserved from:

- `disclosure_code`
- `lq_disclosure_code`
- `oty_disclosure_code`

Rows with status values are flagged in `raw_qcew.is_suppressed`, but source values remain in `raw_payload`. Missing, non-disclosed, and zero values are not treated as equivalent.

## Coverage

The QCEW annual open-data files support the required 2010-2023 period. The committed sample covers 2022-2023 for selected Texas counties in the Abilene-area geography used by earlier BDS examples.

## Raw Grain

The raw sample grain is:

```text
area_fips x own_code x industry_code x size_code x year x qtr
```

For annual files, `qtr = A`.

## A4.8 Requirements

Before `stg_qcew` and `int_industry_growth` can be built, A4.8 must:

- acquire or read the full required 2010-2023 annual QCEW files
- decide whether to use only private ownership or another documented ownership scope
- aggregate county-level rows to July 2023 CBSA using the county crosswalk
- classify QCEW native industry codes against the 2022 NAICS reference
- preserve disclosure codes and avoid converting non-disclosed values to zero
- calculate employment, establishment, payroll, and pay growth only after standardization

## A4.8 Resolution

A4.8 implements the county-level aggregation strategy recommended above. Private ownership (`own_code = 5`) is the selected analytical scope. County records are mapped through the July 2023 CBSA county crosswalk, additive measures are summed, and average annual pay is recalculated from aggregated total annual wages divided by annual average employment.

The transformation documentation is maintained in `docs/QCEW_TRANSFORMATION.md`.

## A4.11 Vintage Audit

BLS documents QCEW source vintages as 2007 NAICS for 2010, 2012 NAICS for
2011-2016, 2017 NAICS for 2017-2021, and 2022 NAICS from 2022 onward.
The project reference bundle does not yet include a 2007-to-2022 sector
mapping. The national QCEW build is paused at the 2010 vintage boundary.
See the official BLS [industry classifications](https://www.bls.gov/cew/classifications/industry/industry-titles.htm).
