# ACS Source Profile

## Product Chosen

Assignment 4.9 uses the U.S. Census Bureau American Community Survey (ACS) 5-year Data Profile API.

Chosen product:

- ACS 5-year estimates
- Data Profile endpoint: `https://api.census.gov/data/{year}/acs/acs5/profile`
- Geography: metropolitan statistical area/micropolitan statistical area
- Committed sample: `data/raw/acs/sample/acs5_profile_msa_sample_2020_2023.csv`

ACS 5-year estimates are selected instead of ACS 1-year estimates because the project needs consistent MSA/CBSA-style regional coverage. ACS 1-year estimates are more limited for smaller geographies, while ACS 5-year profile endpoints support metropolitan/micropolitan statistical areas across the study period.

## Access Method

A4.9 uses the official Census API. The committed sample preserves API request URLs without storing the API key.

The sample includes:

- years 2020-2023
- CBSAs `10180`, `12060`, and `19100`
- five regional controls
- ACS estimates and margins of error

Full production acquisition should query the same variables for all study CBSAs and years 2010-2023.

## Selected Variables

| Control | Estimate variable | MOE variable | Universe / denominator |
| --- | --- | --- | --- |
| Total population | `DP05_0001E` | `DP05_0001M` | Total population |
| Median household income | `DP03_0062E` | `DP03_0062M` | Total households |
| Bachelor degree or higher | `DP02_0068PE` | `DP02_0068PM` | Population 25 years and over |
| Labor-force participation | `DP03_0002PE` | `DP03_0002PM` | Population 16 years and over |
| Unemployment rate | `DP03_0009PE` | `DP03_0009PM` | Civilian labor force |

The selected percentage variables are official ACS percentage estimates. A4.9 does not construct these percentages manually.

## MOE Treatment

ACS values are survey estimates. A4.9 preserves margins of error in `raw_acs` and `stg_acs` where available. The intermediate `int_regional_controls` table uses point estimates; survey-error modeling is deferred.

Census special negative MOE codes are preserved in raw and converted to null in staging.

## Geography

Native ACS geography field:

- `metropolitan statistical area/micropolitan statistical area`

A4.9 audits ACS geography codes against the fixed July 2023 CBSA reference in `ref_geography`. The committed sample directly matches the project CBSA reference.

## Raw Grain

The raw ACS sample grain is:

```text
ACS product x year x source geography x variable
```

Staging pivots this to:

```text
MSA/CBSA x year
```

## Transformation Requirements

Before ACS can contribute to the final analytical panel, A4.9 must:

- preserve source-native estimates, MOEs, variable IDs, and geography codes in `raw_acs`
- standardize geography to `ref_geography`
- pivot selected variables to `stg_acs`
- construct `int_regional_controls` at MSA-year grain
- calculate population growth only after standardization
- create selected one-year regional-control lags with calendar continuity
- avoid industry duplication and avoid integration with BDS/QCEW until a later assignment
