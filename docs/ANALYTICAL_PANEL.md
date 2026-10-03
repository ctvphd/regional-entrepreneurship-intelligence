# Analytical Panel

## Unit And Scope

The canonical Assignment 4 unit is one metropolitan statistical area x 2022
NAICS two-digit sector x calendar year, keyed by
`geography_id + industry_id + year`. The study window is 2010-2023. Only rows
whose `ref_geography.geography_type` is `MSA` enter the primary panel;
micropolitan records remain available upstream. The valid industry set is the
intersection of BDS, QCEW, and CBP standardized sectors, not a name-based or
speculative concordance. A4.11's source-version audit finds all 19 private
business sectors directly comparable and no unresolved sectors.

## Source Roles And Merge Order

1. **BDS** supplies primary entrepreneurship outcomes: firm startups, startup
   rate and its one-, two-, and three-year lags, establishment entry and entry
   rate, and startup job creation.
2. **QCEW** supplies industry levels and growth: employment, establishments,
   payroll, average wage, growth rates, selected growth lags, county coverage,
   and suppression status.
3. **ACS** supplies MSA-year controls and selected one-year lags. ACS is unique
   on `geography_id + year`; the same MSA-year controls intentionally repeat
   across industries after the merge.
4. **CBP** supplies supporting business-structure levels. The columns use a
   `cbp_` prefix so they cannot be mistaken for overlapping QCEW measures.

The merge sequence is:

1. Restrict BDS and QCEW to MSA geography, 2010-2023, and common validated
   sectors. Inner join on `geography_id + industry_id + year`. This is the
   core panel because both the entrepreneurship outcome and industry-growth
   source are necessary for the primary research relationship. Unmatched BDS
   and QCEW keys are counted and documented before they are excluded.
2. Left join ACS on `geography_id + year`; preserve all core rows when controls
   are absent. A uniqueness audit runs before the join and a row-count
   assertion prevents one-to-many multiplication.
3. Left join CBP on `geography_id + industry_id + year`; preserve all core rows
   when supporting data is absent. Incomplete/suppressed CBP source groups
   remain absent from its intermediate and are represented by a false match
   flag rather than filled with zero.

The A4.11 BDS intermediate intentionally contains records with usable startup
rates only; suppressed, missing, and zero-denominator cases are retained in
BDS staging and the BDS quality audit, not in `int_entrepreneurship`. Thus the
core inner join conditions on an accepted BDS startup observation. This
selection is explicit and the BDS missingness audit remains part of the
production quality record.

## Names And Quality Flags

Measures retain source-specific names: `startup_rate`, `qcew_employment`,
`acs_population`, and `cbp_employment`, for example. Row flags identify BDS
startup availability/suppression, QCEW suppression/county completeness, ACS
match/suppression/missing controls, and CBP match/suppression/county
completeness. For CBP, mapped staging groups without an accepted intermediate
are flagged incomplete; suppression is checked in staging even when the group
was excluded. A missing CBP match with no corresponding staging group remains
unknown, not mislabeled as suppression or incompleteness.
`source_quality_notes` contains readable reasons only; it is not
a numeric or subjective quality score. Nominal payroll and income are not
deflated by this integration. QCEW payroll is stored in dollars; CBP annual and
first-quarter payroll remain in source-native $1,000. Only the QCEW-CBP
diagnostic scales the CBP values by 1,000, leaving stored values unchanged.

Human-readable identifiers are provided by
`v_analytics_msa_industry_year`, which adds CBSA code/name, sector code/title,
and retains year without duplicating labels in the normalized table.

## Validation And Leakage Boundary

The build records key uniqueness, three merge audits, variable-level
missingness, year/sector/MSA coverage, panel balance, and QCEW-CBP comparison
diagnostics. QCEW and CBP employment, establishments, and payroll differ in
coverage/reference period; diagnostics do not treat disagreement as a failed
record or imply either source is ground truth.

Assignment 4 creates predictors and source measures only. It does **not**
create expected entrepreneurship, alignment residuals, entrepreneurial-gap
labels, future leads, or other leakage-prone targets. Modeling and fold-specific
outcome construction remain outside Assignment 4.

## Production Results

The production inner join matched 63,577 of 88,562 metropolitan BDS rows
(71.79%) and 71,800 QCEW rows (88.55%); 24,985 BDS-only and 8,223 QCEW-only
keys were excluded. ACS matched 60,039 core rows (94.44%), while CBP matched
58,236 (91.60%); both left joins retained all 63,577 core rows. The panel has
381 MSAs, 19 sectors, 14 years, 5,887 MSA-sector panels, 2,830 balanced and
3,057 unbalanced panels, and zero duplicate keys.

ACS primary controls are unavailable on 3,538 rows (5.56%); the selected
one-year control lags are unavailable on 8,062 rows (12.68%). CBP measures are
unavailable on 5,341 rows (8.40%): 5,331 have mapped but incomplete/excluded
staging groups (4,877 carry a suppression flag) and 10 have no matching mapped
staging group. The analytical startup-rate field is complete by construction
because the accepted BDS intermediate includes usable startup observations
only; upstream BDS suppression and missingness remains documented in the A4.11
audit. QCEW employment growth is missing on 6,468 rows (10.17%), including all
4,509 panel rows in 2010 because no prior-year observation is in this study
window.

In 58,236 matched rows, QCEW-CBP correlations are 0.9932 for employment,
0.7858 for establishments, and 0.9834 for payroll after scaling CBP payroll
from $1,000 to dollars for the diagnostic only. Median absolute percentage
differences are 10.64%, 9.59%, and 10.85%, respectively. The merge report
contains year-, sector-, and MSA-level large-difference detail and full MSA
coverage counts. Run-scoped quality metrics are stored in `quality_table_metric`.
See `reports/assignment4_merge_audit.md` for complete tables.

## Reproduction

With the A4.11 production database available locally, run:

```powershell
$env:UV_CACHE_DIR='C:\Users\mcobp\Documents\Codex\2026-08-30\files-mentioned-by-the-user-you\work\uv-cache'
uv run --offline python -m regional_entrepreneurship_intelligence.etl.build_analytics_panel
```

The command rebuilds the table from the existing production intermediates,
persists run-specific metrics, writes the merge audit report, and refreshes
the ignored compressed CSV export under `data/processed/`.
