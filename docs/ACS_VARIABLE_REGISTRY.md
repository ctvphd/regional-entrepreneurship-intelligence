# ACS 5-Year Data Profile Concept Registry

The machine-readable registry is `data/external/reference/acs_variable_registry.csv` (70 concept-year records). It was generated from official Census ACS 5-year Data Profile `variables.json` and group metadata for every year 2010-2023. `run_acs_production.py` uses these records to request exact estimate and margin-of-error variables; no historical ID is assumed from a recent sample.

| Concept | 2010-2018 estimate / MOE | 2019-2023 estimate / MOE | Universe and interpretation |
| --- | --- | --- | --- |
| Total population | DP05_0001E / DP05_0001M | Same | Total population, count |
| Median household income | DP03_0062E / DP03_0062M | Same | Households, median dollars adjusted to each release year |
| Bachelor's degree or higher | DP02_0067PE / DP02_0067PM | DP02_0068PE / DP02_0068PM | Population age 25+, percent |
| Labor-force participation | DP03_0002PE / DP03_0002PM | Same | Population age 16+, percent in labor force |
| Unemployment rate | DP03_0009PE / DP03_0009PM | Same | Civilian labor force, percent unemployed |

The education ID changes in 2019. `DP02_0068PE` does **not** mean bachelor's degree or higher in earlier releases. Registry construction verifies each year's official label, paired MOE, and expected concept; the CSV retains the exact label and metadata URL for audit. The education denominator comes from the `EDUCATIONAL ATTAINMENT` section's population-25-and-over base. Income concept continuity does not make dollar amounts directly comparable across years: each release reports its own inflation-adjusted dollar vintage. No deflation is performed here.

Acquisition requests metro areas from the official ACS API, retains source geography names and codes, and omits the API key from saved URLs, CSV rows, and manifests. The transformation matches source codes to the fixed July 2023 CBSA reference; unmatched historical codes remain in staging and are rejected from `int_regional_controls`. A code match alone does not establish that historical metropolitan boundaries were identical. No ACS control is forward-filled.

To regenerate the registry after revalidating official metadata, run `uv run python -m regional_entrepreneurship_intelligence.etl.acs_variable_registry`. To rerun the local production build, set `CENSUS_API_KEY` in the shell and run `uv run python -m regional_entrepreneurship_intelligence.etl.run_acs_production`. National source files and the production SQLite database remain Git-ignored.
