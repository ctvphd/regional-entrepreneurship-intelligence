# Assignment 7 Future Map Specification

**Status: Deferred until post-A7 visualization/presentation phase. No map, geometry, or mapping dependency is built in A7.1.**

## Required Join and Attributes

- CBSA identifier (`cbsa_code`, string) and display name (`msa_name`), with geography vintage and source.
- Descriptive or predictor/target year roles, kept distinct.
- Optional sector code/name and dominant sector only where its definition and denominator are explicit.
- Observed startup rate, expected startup rate, alignment residual/label, and observed gap status where sourced.
- Predicted gap probability and presentation category only for eligible predictor-year rows, plus model/version and horizon.
- Coverage status, underlying count/rule, and source availability.
- Geometry identifier and licensed/authoritative polygon source with vintage, CRS, and crosswalk audit.

## Future Modes

- Entrepreneurial alignment (observed versus expected activity/residual).
- Predicted future gap risk (probability, not deterministic class).
- Sector/year filtering with explicit eligible coverage.
- MSA highlighting and popup details for time roles, observed/expected values, score, category rule, and caveat.

No geometry source is selected here. A future map must validate CBSA vintage compatibility and disclose unmatched/aggregated geographies rather than assume a code match. Final A6 holdout actual outcomes remain retrospective evaluation data, not contemporaneous map inputs.
