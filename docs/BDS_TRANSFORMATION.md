# BDS Transformation

## Raw Sources

A4.6 uses two official Census BDS 2023 bulk products through committed permitted samples:

- `bds2023_msa_sec_sample_2010_2023.csv`
- `bds2023_msa_sec_fac_sample_2010_2023.csv`

The source-native files are preserved under `data/raw/bds/sample/`. The full national files are not committed.

## Geography Audit

BDS native geography is `msa`. A4.6 compares BDS `msa` codes with `ref_geography.cbsa_code` for the July 2023 CBSA delineation.

Sample audit result:

- unique BDS MSA codes: 2
- direct matches: 2
- crosswalk-required: 0
- unresolved: 0

No records are forced into the analytical geography if unresolved. The sample codes are direct matches, but this does not prove the full BDS source is fully compatible with the July 2023 CBSA vintage.

## Industry Audit

BDS native industry coding is treated as 2017 NAICS sector coding. The analytical reference is 2022 NAICS.

A4.6 classifies BDS sectors by exact sector-code evidence in the 2022 NAICS reference:

- directly comparable
- official mapping required
- unresolved

Sample audit result:

- unique BDS sectors: 4
- directly comparable: 4
- official mapping required: 0
- unresolved: 0

Combined sectors such as `31-33` and `44-45` are preserved as official combined sector codes and are not split.

## Staging Rules

`stg_bds` is rebuilt from source-native age-0 firm-age rows and the MSA-sector backbone. Staging retains unresolved or suppressed records with flags instead of silently dropping them.

Important staging fields include:

- source-native `msa`, `sector`, and `fagecoarse`
- standardized geography and industry IDs when mapping is supported
- geography and industry mapping status
- firm startup count
- startup rate
- establishment entry and establishment entry rate
- startup job creation
- suppression and missingness flags

## Startup Construction

Primary source table:

- BDS MSA by Sector by Firm Age Coarse

Firm age category:

- `a) 0`

Numerator:

- `firms` from age-0 rows, interpreted as firm startups.

Denominator:

- `firms` from the BDS MSA by Sector backbone for the same `msa x sector x year`.

Formula:

```text
startup_rate = age_0_firms / all_firms * 100
```

If either the age-0 numerator or backbone denominator is suppressed, unavailable, nonnumeric, or zero, the startup rate is set to null. Suppressed values are not converted to zero.

## Supporting Measures

A4.6 carries supporting measures where available:

- establishment entry
- establishment entry rate
- startup job creation

These support robustness and validation but do not replace the primary age-0 startup concept.

## Lag Construction

Lags are created only after standardization in `int_entrepreneurship`.

Lag variables:

- `startup_rate_lag1`
- `startup_rate_lag2`
- `startup_rate_lag3`

Grouping keys:

- `geography_id`
- `industry_id`

Calendar-year rule:

- lag1 must use year `t - 1`
- lag2 must use year `t - 2`
- lag3 must use year `t - 3`

Missing-year behavior:

- panel gaps produce null lag values
- values are not forward-filled
- suppressed prior startup rates do not become valid lag values

## Exclusions

Records are retained in `stg_bds` but excluded from `int_entrepreneurship` when:

- geography is unresolved
- industry is unresolved
- the required startup count or rate cannot be constructed

For the current sample, 8 staged rows have missing startup measures due to suppression or unavailable source values and are excluded from `int_entrepreneurship`.

## Quality Checks

A4.6 records quality metrics for:

- raw BDS rows
- raw BDS firm-age rows
- staged rows
- intermediate rows
- unresolved geography rows
- unresolved industry rows
- suppressed staging rows
- missing startup measure rows
- duplicate staging keys
- duplicate intermediate keys
- lag missingness
- valid MSA-sector panels

## Final Intermediate Grain

`int_entrepreneurship` grain:

```text
standardized MSA x directly comparable sector x year
```

The table does not contain expected entrepreneurship, alignment residuals, entrepreneurial-gap targets, QCEW measures, ACS controls, or CBP measures.

## A4.11 Production Behavior

The national BDS build uses the existing MSA-sector-year staging and
entrepreneurship transformations. Full-scale data showed that an age-0 or
backbone row can have a D/S flag on an unrelated measure while both firm
counts needed for startup rate are numeric. `stg_bds.is_suppressed` therefore
tracks suppression of the age-0 firms numerator or all-firms denominator for
this measure; source-wide flags remain in raw data. Production quality metrics
now include raw suppression, startup missingness, all three lag missingness
counts, year coverage, panel counts, and run-specific rejected rows.
