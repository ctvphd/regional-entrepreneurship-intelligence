# Assignment 6 Limitations Register

- **Complete-case selection:** A6.4/A6.5 require five ACS controls in the paired comparison; omitted observations are patterned, including smaller MSAs and lower startup rates. Results apply to eligible complete cases unless a named wider-sample sensitivity says otherwise.
- **Metro coverage:** A5's screen flags 67 of 381 MSAs as thin; several large metros have incomplete sector coverage.
- **Industry resolution:** industries are represented at 2-digit NAICS, so within-sector heterogeneity is hidden.
- **Entrepreneurship measure:** firm startup rate is one narrow operationalization; establishment entry and startup job creation are distinct constructs and need separate denominator/target design.
- **Gap construct:** the outcome is a fold-local residual threshold relative to a selected expected-entrepreneurship model, not an absolute welfare or failure measure.
- **Predictive, not causal:** coefficients, importances, and lift do not identify effects of policy or economic conditions.
- **Growth contribution:** employment growth helps define context and the first-stage expectation but adds limited incremental classification signal after sector/startup history in current checks.
- **Period:** observations span 2010–2023 and include pandemic-era disruption; external periods may differ.
- **Final temporal holdout:** the locked logistic model achieved AP 0.404 versus 0.233 prevalence, ROC-AUC 0.692, Brier 0.164, and top-decile lift 1.99 on 10,304 eligible MSA-sector pairs in 2021–2023. This is evidence of useful ranking, not reliable individual classification or external validity.
- **Calibration and regime shift:** logistic Brier increased from 0.142 development OOF to 0.164 holdout. Calibration deciles show underprediction at the low end and overprediction in the upper deciles; no holdout recalibration was performed. Pandemic/post-pandemic target years also differ materially in prevalence.
- **Subgroup uncertainty:** performance varies across sectors and MSA-size groups; sector metrics are suppressed below 30 positive events. Even supported cells are descriptive and may be unstable.
- **Generalization:** the final holdout is one historical period and geographic results remain conditional on observed data and feature availability. New periods and populations require fresh validation.
- **Residual uncertainty:** temporal folds are finite and expanding, rare-sector scores are unstable, and the final complete-case sample excludes a patterned subset (14.8% of exact holdout candidate pairs).
