"""Canonical plain-language metric and construct descriptions."""

GLOSSARY = {
    "AP": "Average Precision summarizes precision across recall levels; compare it with outcome prevalence for this population. It is not accuracy.",
    "ROC-AUC": "ROC-AUC measures ranking across thresholds; 0.500 is random ranking and higher indicates stronger discrimination.",
    "Brier": "Brier score is mean squared probability error; lower is better. It is not accuracy.",
    "Lift": "Lift is the positive-outcome prevalence in a highest-scored share divided by overall prevalence; 1.00x equals the overall rate.",
    "Prevalence": "Prevalence is the observed positive-outcome share in the stated evaluation population and is the no-information AP reference.",
    "Calibration": "Calibration compares predicted probability with observed frequency within score bins; it does not change the frozen model scores.",
    "Gap": "An entrepreneurial gap is a model-relative label for unusually low observed startup activity versus an A6 expected benchmark; it is not causal.",
    "Alignment": "Alignment is observed minus expected startup rate, expressed in percentage points; it is not itself a causal effect.",
    "Expected rate": "Expected startup rate is the finalized A6 Model A benchmark for the available fold-validation row; unavailable values are not extrapolated.",
}
