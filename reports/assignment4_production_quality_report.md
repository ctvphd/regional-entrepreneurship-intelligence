# Assignment 4.11 Production Quality Report

Status: **A4.11 production and A4.12 integrated panel are complete.** The
ignored production database contains four source-specific national pipelines
for 2010-2023 and the integrated metropolitan panel. Expected entrepreneurship,
alignment residuals, future leads, and entrepreneurial-gap targets were not
created.

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

At the A4.11 boundary, the full offline suite passed 30 tests. After A4.12
integration coverage was added, the full offline suite passed **34 tests** with
no failures, errors, or skips.
The four intermediate tables have zero duplicate keys at their declared
grains. The production analytics table has zero rows. Production runner
idempotency was verified for ACS and BDS; CBP raw acquisition and transformation
were rerun successfully. QCEW transformation passed the full national build
and focused synthetic idempotency tests; a second full national QCEW rebuild
was not run because it takes about 13 minutes.

The production SQLite database is approximately 4.72 GB locally and remains
ignored. Expected entrepreneurship, alignment/gap targets, future leads, and
the regenerated final README are intentionally deferred.

## A4.12 Integration Results

The canonical panel is `geography_id x industry_id x year` (MSA x 2022 NAICS
broad sector x year), 2010-2023. BDS is the primary entrepreneurship source;
QCEW is the growth source; ACS controls join at MSA-year; CBP supplies
source-labeled business-structure support. The inner BDS-QCEW core contains
63,577 rows from 88,562 metropolitan BDS keys and 71,800 metropolitan QCEW
keys: 24,985 BDS-only and 8,223 QCEW-only keys were not retained. The BDS
match rate is 71.79%; the QCEW match rate is 88.55%. Left-joined ACS matches
60,039 core rows (94.44%), and CBP matches 58,236 (91.60%); neither support
join reduces the core row count.

The resulting panel contains 63,577 rows, 381 MSAs, all 19 common sectors, and
all 14 study years. It has 5,887 MSA-sector panels: 2,830 balanced across all
14 years and 3,057 unbalanced. Average observations per panel are 10.80.
Duplicate primary keys: zero. The source-key audit also found zero duplicates
in BDS (178,382 rows), QCEW (179,731), ACS (5,194), and CBP (189,474).

| Availability / missingness | Count | Share of final rows |
| --- | ---: | ---: |
| Startup rate missing | 0 | 0.00% |
| Startup-rate lag 1 / 2 / 3 missing | 8,683 / 12,978 / 17,171 | 13.66% / 20.41% / 27.01% |
| QCEW employment missing | 0 | 0.00% |
| QCEW employment growth missing | 6,468 | 10.17% |
| ACS row unmatched; primary controls missing | 3,538 | 5.56% |
| ACS one-year controls/lags missing | 8,062 | 12.68% |
| CBP measures unavailable | 5,341 | 8.40% |
| CBP incomplete mapped staging groups | 5,331 | 8.39% |
| CBP suppression flag carried from staging | 4,877 | 7.67% |

The QCEW-CBP validation uses 58,236 matched rows. Correlations are 0.9932 for
employment, 0.7858 for establishments, and 0.9834 for payroll. Median CBP/QCEW
ratios are 1.0275, 0.9773, and 0.9903, respectively. CBP payroll was scaled
from $1,000 to dollars for this diagnostic only; source-native stored values
are unchanged. Differences over 100% occur in 1,075 employment, 134
establishment, and 1,082 payroll observations. Year/sector/MSA detail is in
`reports/assignment4_merge_audit.md` and the ignored generated JSON audit.
These discrepancies are validation signals, not grounds to automatically
reject either source.

CBP support is unavailable for 5,341 core rows. Of those, 5,331 have a mapped
staging group that failed to produce an accepted complete intermediate; 4,877
rows carry a staging suppression flag. Ten unmatched rows have no corresponding
mapped staging group. These distinctions are carried by CBP match,
suppression, and completeness flags plus `source_quality_notes`.

Two final production panel builds (runs `d1625537-e26f-4c2b-b0aa-d213fcd6640d` and
`c55846fe-78ca-4814-9ebe-e300d652e600`) produced identical panel payloads,
merge counts, and all 76 run-scoped quality metric values. The 10.5 MB gzip
export remains ignored. No target or future-lead columns are present. Historical
CBSA code matches do not establish historical boundary equivalence; BDS
suppressed/missing startup outcomes remain excluded upstream from its
intermediate, and source coverage differs by year and sector.
