# Historical NAICS Version Strategy

The analytical target is 2022 NAICS at the broad sector level. The explicit source/year registry is `database/naics_versions.py`; transforms and production acquisition consult it. Census's official six-digit concordances retained in `data/external/reference/` establish the possible chain `2007 -> 2012 -> 2017 -> 2022`. The 2007-to-2012 and reverse XLS files come from the [Census concordance archive](https://www2.census.gov/library/reference/naics/technical-documentation/concordance/). All reference files are checksummed and manifested by the reference loader.

| Source | Years | Native NAICS |
| --- | --- | --- |
| QCEW | 2010 | 2007 |
| QCEW | 2011-2016 | 2012 |
| QCEW | 2017-2021 | 2017 |
| QCEW | 2022-2023 | 2022 |
| CBP | 2010-2011 | 2007 |
| CBP | 2012-2016 | 2012 |
| CBP | 2017-2023 | 2017 |
| BDS 2023 historical release | 2010-2023 | 2017 |

For a source sector, `classify_sector` follows each official six-digit concordance step and groups destinations to the 2022 broad-sector code. A sector is accepted only when all supported paths lead to one target sector **and** that target does not also receive another old broad sector. Otherwise it is unresolved and cannot enter a standardized intermediate table. The combined sectors `31-33`, `44-45`, and `48-49` remain combined. All 19 private-business sectors used by BDS/CBP were directly comparable by this test; this is not permission to map arbitrary detailed industries. `92` is not in the CBP county-business scope used here.

The registry documents classification standards, not historical geographic boundary equivalence. County-based QCEW and CBP records use the fixed July 2023 county-to-CBSA crosswalk. BDS and ACS source CBSA codes are audited against the fixed reference; a matching code alone cannot prove identical historical boundaries. No production runner writes to the four-source analytical panel.
