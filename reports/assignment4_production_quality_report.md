# Assignment 4.11 Production Quality Report

Status: **partial; not ready for A4.12**. The BDS 2010-2023 national run completed.
The QCEW, ACS, and CBP national pipelines were stopped at source-year definition
boundaries documented below. Counts below describe the ignored local production
database, not the small committed samples. No cross-source table or model target
was created.

## BDS

The official 2023 [MSA by Sector](https://www2.census.gov/programs-surveys/bds/tables/time-series/2023/bds2023_msa_sec.csv)
and [MSA by Sector by Firm Age Coarse](https://www2.census.gov/programs-surveys/bds/tables/time-series/2023/bds2023_msa_sec_fac.csv)
bulk files were acquired. Their SHA-256 checksums are respectively
`69f2040952dc73d1c02cf8363e24d9b680f0f52dbee337a7b317f9ead5f494f9`
and `e5673f22276699d10a0f81c2ad1b3c60aabf04a6640d15e822100ac7a6fcfc1b`.
The full files contain 808,450 and 4,042,250 rows across all release years.
The production extracts select all 246,050 MSA-sector rows in 2010-2023 and
the 246,050 age-0 firm rows in the same window. Both full files and extracts
are Git-ignored; the SQLite manifest records URLs, checksums, counts, release,
and retrieval timestamps.

| Measure | National result |
| --- | ---: |
| `raw_bds` rows | 246,050 |
| `raw_bds_firm_age` age-0 rows | 246,050 |
| `stg_bds` rows | 246,050 |
| `int_entrepreneurship` rows | 178,382 |
| Distinct mapped CBSA codes | 925 |
| Metropolitan / micropolitan codes | 387 / 538 |
| Distinct sector codes | 19 |
| Years | 14 (2010-2023) |
| MSA-sector panels | 16,930 |
| Balanced 14-year panels | 5,962 |
| Missing startup rate in staging | 67,668 |
| Lag 1 / 2 / 3 available | 137,432 / 126,351 / 115,585 |
| Raw backbone rows with any D/S flag | 98,352 |
| Raw age-0 rows with any D/S flag | 53,856 |
| Staging rows with a suppressed startup input | 64,786 |
| Geography / industry code matches | 925/925 and 19/19 |
| Unresolved geography / industry codes | 0 / 0 |
| Duplicate staging / intermediate keys | 0 / 0 |
| Rejected startup rows | 67,668 |

The startup rate uses age-0 firms divided by all firms in the same MSA-sector-year.
Only suppression of those two firm counts invalidates the startup measure;
flags on unrelated BDS measures remain visible in raw data. Code matching
against the July 2023 CBSA reference is 100%, but matching codes alone do not
prove historical boundary equivalence. The BDS intermediate is available for
review, with that geography caveat and substantial legitimate startup missingness.
The 925 codes include 538 micropolitan areas; a metropolitan-only analytical
scope must filter these explicitly before integration.

## QCEW

The 2010-2023 national county pipeline was not run. The official BLS
[NAICS history](https://www.bls.gov/cew/classifications/industry/industry-titles.htm)
identifies 2007 NAICS for 2010, 2012 NAICS for 2011-2016, 2017 NAICS for
2017-2021, and 2022 NAICS for 2022-2023. The current project reference set has
no 2007-to-2022 sector mapping, and the sample transformation's exact-code
check does not establish vintage comparability for 2010. The
[annual by-area archives](https://www.bls.gov/cew/downloadable-data-files.htm)
were verified as available, but no national raw/staging/intermediate rows were
loaded. County completeness, ownership exclusions, suppression, growth, lags,
and rejected-row counts are therefore not measurable at production scale yet.

## ACS

The national ACS pipeline was stopped before loading rows. Official Census
metadata for [`DP02_0068PE` in 2010](https://api.census.gov/data/2010/acs/acs5/profile/variables/DP02_0068PE.json)
labels it as civilian population 18 years and over under veteran status.
The ID remains in that category through 2018. In
[2019](https://api.census.gov/data/2019/acs/acs5/profile/variables/DP02_0068PE.json)
it becomes bachelor's degree or higher for population 25 years and over,
the meaning retained in [2023](https://api.census.gov/data/2023/acs/acs5/profile/variables/DP02_0068PE.json).
The locked 2010-2023 education definition is therefore incompatible. No
silent variable substitution or false education values were produced. National
geography, controls, MOE, missingness, growth, lag, and rejection results are
unavailable until the variable decision is made.

## CBP

The national county pipeline was not run. Official CBP API variable metadata
shows `NAICS2007` for 2010-2011, `NAICS2012` for 2012-2016, and `NAICS2017`
for 2017-2023. The project has no 2007 mapping, and the current loader expects
the later source field. See the Census metadata for
[2010](https://api.census.gov/data/2010/cbp/variables.html),
[2012](https://api.census.gov/data/2012/cbp/variables.html), and
[2023](https://api.census.gov/data/2023/cbp/variables.html).
No national raw/staging/intermediate CBP rows were loaded; county coverage,
noise/suppression, rejected records, and completeness remain unmeasured at
production scale.

## Cross-Source Geography And Industry

| Source | Unique source geographies | Direct matches | Crosswalk matches | Unresolved | Row share matched |
| --- | ---: | ---: | ---: | ---: | ---: |
| BDS | 925 | 925 | 0 | 0 | 100% by code |
| QCEW | Not acquired | Not measured | Not measured | Not measured | Not measured |
| ACS | Not acquired | Not measured | Not measured | Not measured | Not measured |
| CBP | Not acquired | Not measured | Not measured | Not measured | Not measured |

| Source | Native NAICS | 2022 sector treatment | Unresolved |
| --- | --- | --- | --- |
| BDS | 2017 | 19 source sector codes match the 2022 reference by code, including combined sectors; no official concordance applied | 0 codes |
| QCEW | 2007 / 2012 / 2017 / 2022 by year | Official vintage mapping still required for a national run | 2010 vintage unresolved |
| CBP | 2007 / 2012 / 2017 by year | Source-year field and vintage handling required | 2010-2011 vintage unresolved |

## Year Coverage

Here *available* means a production intermediate year was built; *partial*
means the official source is available but the national pipeline has not been
run; *unusable* means the locked definition or mapping blocks that year.

| Year | BDS | QCEW | ACS | CBP |
| --- | --- | --- | --- | --- |
| 2010 | available | unusable | unusable | unusable |
| 2011 | available | partial | unusable | unusable |
| 2012 | available | partial | unusable | partial |
| 2013 | available | partial | unusable | partial |
| 2014 | available | partial | unusable | partial |
| 2015 | available | partial | unusable | partial |
| 2016 | available | partial | unusable | partial |
| 2017 | available | partial | unusable | partial |
| 2018 | available | partial | unusable | partial |
| 2019 | available | partial | partial | partial |
| 2020 | available | partial | partial | partial |
| 2021 | available | partial | partial | partial |
| 2022 | available | partial | partial | partial |
| 2023 | available | partial | partial | partial |

## Idempotency And Resources

The BDS production command is:

```powershell
$env:UV_CACHE_DIR='C:\Users\mcobp\Documents\Codex\2026-08-30\files-mentioned-by-the-user-you\work\uv-cache'
uv run --offline python -m regional_entrepreneurship_intelligence.etl.run_bds_production
```

It reuses cached official files, recomputes study-window extracts, checks raw
row identifiers before insertion, and rebuilds staging/intermediate tables.
| Pass | Raw backbone | Raw age-0 | Staging | Intermediate | Run-specific rejections |
| --- | ---: | ---: | ---: | ---: | ---: |
| Initial national run | 246,050 | 246,050 | 246,050 | 132,420 | 67,668 |
| Corrected production command | 246,050 | 246,050 | 246,050 | 178,382 | 67,668 |
| Same-code transformation rerun | 246,050 | 246,050 | 246,050 | 178,382 | 67,668 |

The first run took 304 seconds and exposed an overly broad suppression filter.
The corrected production command took 389 seconds; its raw loaders inserted
zero new rows. The same-code transformation rerun took about 375 seconds. Its
12 quality metrics shared with the preceding run have identical values; seven
additional production metrics were added before this final rerun. The
`quality_rejected_record` table retains run history, so its cumulative count
is 203,004 rather than 67,668. Raw, staging, and intermediate keys have no
duplicates. Four BDS manifests (two original files, two extracts) remain
stable; six reference manifests are also present.

The full official BDS files occupy 493,881,797 bytes; the two study extracts
occupy 48,260,956 bytes. The SQLite database is 801,452,032 bytes. All are
Git-ignored. In-memory CSV reads and row-by-row SQLite/rejection insertion
are the largest performance costs. The latest run persisted 19 quality
metrics, including panel counts, year coverage, lags, suppression, missingness,
duplicates, and rejected rows.

## Tests

The baseline suite passed 22 tests before production changes. The final
offline suite passed 23 tests, with zero failures, errors, or skips:

```powershell
$env:UV_CACHE_DIR='C:\Users\mcobp\Documents\Codex\2026-08-30\files-mentioned-by-the-user-you\work\uv-cache'
uv run --offline python -m unittest discover -s tests -v
```

## Cross-Source Readiness

`int_entrepreneurship` is populated nationally for 2010-2023, including
metropolitan and micropolitan codes.
`int_industry_growth`, `int_regional_controls`, and `int_business_structure`
are not populated nationally. A4.11 is incomplete, and A4.12 integration
must wait for explicit ACS variable handling and authoritative early-year
NAICS comparability decisions, followed by production runs and audits.
