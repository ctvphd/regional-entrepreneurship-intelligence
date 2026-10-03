# Assignment 4.11 Production Quality Report

Status: **A4.11 production work complete; A4.12 integration is not started.** The
ignored production database contains four source-specific national pipelines
for 2010-2023. No measures were joined across sources, and
`analytics_msa_industry_year` remains empty. Expected entrepreneurship,
alignment residuals, and entrepreneurial-gap targets were not created.

The local database and full source files are Git-ignored; committed samples
remain unchanged. The report's counts describe the local production database.

## Production Counts

| Source | Raw | Staging | Intermediate | Run-specific rejected/unavailable | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| BDS | 492,100 across two raw tables | 246,050 | 178,382 all-scope; 88,562 MSA | 67,668 startup rows missing | Age-0 firms / all firms; 14 years, 19 sectors |
| QCEW | 811,113 | 245,012 | 179,731 | 384,589 | Private ownership, annual county records, 19 broad sectors |
| ACS | 27,075 | 5,415 | 5,194 | 221 | Five profile concepts with paired MOEs; 2010-2023 |
| CBP | 755,249 | 755,249 | 189,474 | 374,302 | County-level raw rows; only complete CBSA-sector-year aggregates enter the intermediate |

QCEW additionally flagged 65,281 incomplete aggregation groups. That is a
separate group-level completeness measure, not an additional number of raw
rows rejected. Suppression and unavailable values are retained or classified
under source-specific rules rather than interpreted as zero.

## Historical Definitions

The target industry classification is 2022 NAICS broad sectors. Source-year
vintages are recorded explicitly and the official concordance chain
2007 -> 2012 -> 2017 -> 2022 is used to test broad-sector comparability.
Across all 19 retained private-business sectors, every source/year row in the
QCEW and CBP version audit was directly comparable to the target sector; there
were zero officially mapped, unresolved, or excluded rows. This conclusion is
limited to broad sectors and does not establish detailed-industry equivalence.

| Source | Native NAICS by years |
| --- | --- |
| BDS 2023 historical release | 2017, 2010-2023 |
| QCEW | 2007 (2010); 2012 (2011-2016); 2017 (2017-2021); 2022 (2022-2023) |
| CBP | 2007 (2010-2011); 2012 (2012-2016); 2017 (2017-2023) |

ACS controls use the year-specific official profile registry. Bachelor's
degree or higher changes from `DP02_0067PE/PM` in 2010-2018 to
`DP02_0068PE/PM` in 2019-2023; the registry confirms the same concept and
population-25+ universe. The other four estimate/MOE pairs are validated for
each year. Household-income estimates are in each release year's adjusted
dollars and are not deflated to a common year.

## BDS Missingness And Scope

Of 246,050 staged BDS rows, 67,668 lack a startup rate. The auditable primary
reasons are 53,855 suppressed age-0 numerators (79.59%), 10,931 suppressed
all-firm denominators (16.15%), and 2,882 zero denominators (4.26%). There
were no residual “other” missing cases. Among metropolitan records, 88,562
startup rates are complete and 14,380 are missing. The MSA intermediate
contains 88,562 rows across 387 MSA codes, 19 sectors, and 14 years; its
available startup-rate lags 1/2/3 are 75,322 / 69,464 / 63,621. Micropolitan
records remain in source/staging/all-scope intermediate data but are omitted
from the A4.11 primary metropolitan readiness view.

## Cross-Source Readiness

All four sources contain source-specific intermediate rows in every year from
2010 through 2023. The cross-source audit found 387 metropolitan codes in BDS,
QCEW, and ACS; 392 in CBP; and 381 codes common to all four. This is an
observed-code overlap only, not proof that historical CBSA boundaries are
equivalent. County-based QCEW/CBP use the fixed July 2023 county crosswalk;
BDS/ACS code matches preserve the historical-boundary caveat. No additional
geography crosswalk was inferred.

All four sources expose the same 19 broad sectors in their intermediate
layers. Row availability differs by source and year and must be assessed at
cell level before any future analytical join. The detailed year-by-year
production counts and the full geography list are preserved in the ignored
generated audit file `reports/generated/a411b_readiness.json`; historical
sector classifications are in `reports/generated/a411b_source_versions.json`.

## Reproducibility And Validation

Full source files, the production database, and generated JSON audits are
ignored by Git. Production runners are under
`src/regional_entrepreneurship_intelligence/etl/`; the ACS registry and NAICS
strategy are documented in `docs/ACS_VARIABLE_REGISTRY.md` and
`docs/NAICS_VERSION_STRATEGY.md`. Source-specific instructions and quality
rules are in each source's profile and transformation document.

The full offline test suite passed **30 tests** with no failures or skips.
The four intermediate tables have zero duplicate keys at their declared
grains. The production analytics table has zero rows. Production runner
idempotency was verified for ACS and BDS; CBP raw acquisition and transformation
were rerun successfully. QCEW transformation passed the full national build
and focused synthetic idempotency tests; a second full national QCEW rebuild
was not run because it takes about 13 minutes.

The production SQLite database is approximately 4.72 GB locally and remains
ignored. The regenerated final README and all A4.12 joining/target work are
intentionally deferred.
