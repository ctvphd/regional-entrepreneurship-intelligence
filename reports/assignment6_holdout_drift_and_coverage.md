# Assignment 6.8E: Holdout Prevalence Drift and Complete-Case Scope

## Purpose

This diagnostic explains the development-to-holdout prevalence increase and pairs predictive performance with the population that can actually be scored. It uses committed labels, probabilities, expected-model validation predictions, sample audits, and the frozen descriptive panel. No model was refit, no excluded value was imputed, and no production rule changed.

## Development vs Holdout Prevalence

Pooled development OOF prevalence is 19.130%; final holdout prevalence is 23.253%, an increase of 4.123 percentage points. The development OOF labels use fold-local expected models and thresholds; the final holdout uses the frozen full-development expected model and cutoff, so the comparison combines temporal outcome change with benchmark-transfer differences.

## Observed vs Expected Startup Activity

Mean observed startup activity rises from 6.734 in development OOF rows to 7.386 in eligible holdout rows; medians rise from 6.532 to 7.219. A simple decline in raw observed startup activity therefore does not explain the higher gap prevalence.

Development OOF expected activity averages 6.681, with mean residual 0.053. Row-level final-holdout expected values and continuous residuals were not committed. Recreating them would require refitting the production expected model, which this diagnostic explicitly forbids. Accordingly, the analysis does not claim whether expected activity moved upward or quantify a continuous holdout residual shift.

## Residual Distribution Shift

Available development OOF residuals have mean 0.053, median -0.066, SD 2.126, p10 -2.224, p20 -1.416, and p25 -1.124. 19.0% fall below the frozen final cutoff of -1.478345. These fold-validation residuals are not interchangeable with final-model in-sample residuals. Holdout residual quantiles are reported as unavailable, not reconstructed.

## Holdout Years

- 2021: prevalence 24.3%, observed startup mean/median 7.177/6.895, Logistic AP 0.435.
- 2022: prevalence 18.1%, observed startup mean/median 7.668/7.511, Logistic AP 0.355.
- 2023: prevalence 27.3%, observed startup mean/median 7.312/7.288, Logistic AP 0.427.

The low 2022 prevalence followed by the high 2023 prevalence supports temporal heterogeneity rather than a uniform one-direction shift.

## Composition Standardization

Reweighting holdout sector rates to development sector shares gives 23.123%, versus raw holdout prevalence 23.253%. Sector mix accounts for only 0.130 percentage points of the raw increase. MSA-size standardization gives 23.390%; its composition contribution is -0.137 points. Joint sector-by-size standardization gives 23.264%, leaving an adjusted increase of 4.134 points. Composition therefore does not explain the 4.123-point shift.

## Complete-Case Eligibility

The exact holdout universe has 12,091 t-to-t+3 candidate pairs. 10,924 have complete expected-model target inputs, 10,304 satisfy both target and predictor completeness, and 1,787 are excluded (14.780%). Scoreable coverage is 85.220%.

## Who Is Excluded?

Eligible predictor-year population averages 832,815, versus 506,442 among available excluded rows. Predictor-year startup rate averages 6.836 versus 5.833. Target-year observed startup rate is available for all candidates and averages 7.386 versus 6.173. Standardized differences and available Ns are retained in the comparison CSV so structural missingness is never converted to zero.

- large: 282 of 4,250 excluded (6.6%).
- middle: 426 of 3,976 excluded (10.7%).
- small: 583 of 3,369 excluded (17.3%).
- unclassified_missing_population: 496 of 496 excluded (100.0%).

Highest sector exclusion rates are 11 (47.9%), 21 (38.4%), 55 (36.4%); lowest are 44-45 (5.5%), 23 (5.9%), 62 (7.8%). Exclusion describes scoreability, not predictive performance.

## Exclusion Reasons

Target benchmark inputs are incomplete for 1,167 candidates; predictor complete-case inputs are incomplete for 1,308; 688 have both problems. Counts overlap by design. Field-level reasons are reported separately, with no imputation.

## Interpretation of Drift

The evidence supports a mixed benchmark-relative temporal shift, not a raw startup decline or composition-only explanation. Raw observed startup activity is higher in the holdout, sector/size standardization leaves nearly the full prevalence increase, and annual prevalence varies sharply. Because final holdout expected values and residual magnitudes were not persisted, the analysis cannot distinguish real residual deterioration from expected-model benchmark transfer as finely as a frozen residual artifact would permit.

## Interpretation of AP

AP = 0.404 describes ranking performance among the 10,304 MSA-industry-year observations that satisfy exact temporal pairing, expected-label availability, and the locked complete-case predictor rules. It does not describe the 1,787 abstained candidate cells, all theoretical MSA-industry combinations, non-metropolitan areas, or cells without sufficient historical and regional data. Performance should therefore be presented together with 85.2% candidate coverage.

## Abstention Framework

Excluded cells should be called insufficient-data model abstentions, not negative predictions. Of the excluded cells, 620 retain the production gap-label inputs but lack predictor completeness; no classifier probability is generated. All 1,787 excluded rows retain observed startup activity plus sector and year, so a simpler sector-year benchmark is technically feasible for diagnostic research. It would define a different estimand and must not be substituted into production without a separately locked design and validation.

## Presentation Language

“Gap prevalence rose from 19.1% in development to 23.3% in the holdout; diagnostics show that sector and MSA-size composition explain little of the increase and that raw observed startup activity did not decline, leaving a mixed benchmark-relative temporal shift.”

“The model’s AP of 0.404 applies to the 85.2% of exact holdout candidate cells with sufficient target and predictor data; smaller, lower-startup, and population-unclassified cells are more likely to be insufficient-data abstentions.”

## Limitations and Implications

Development OOF and final holdout labels use related but not identical expected-model fits and threshold construction. Continuous holdout residual drift cannot be audited from committed artifacts without prohibited refitting. Complete-case contrasts are descriptive and may reflect overlapping missingness mechanisms. These limits should be stated in the final presentation and motivate, but do not implement, future dissertation work on abstention-aware or reduced-data models.
