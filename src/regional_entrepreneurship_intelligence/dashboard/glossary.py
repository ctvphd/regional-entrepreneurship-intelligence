"""Canonical plain-language metric and construct descriptions."""

GLOSSARY = {
    "AP": "Average Precision (AP) summarizes how many actual gap cases appear near the top of the model's ranking across recall levels. Compare it with the observed gap rate; AP is not accuracy.",
    "ROC-AUC": "ROC-AUC measures how often a gap case ranks above a non-gap case across thresholds. 0.500 is random ranking; higher is better.",
    "Brier": "Brier score is the average squared difference between predicted probability and outcome. Lower is better; it is not accuracy.",
    "Lift": "Lift compares the gap rate in a highest-scored group with the overall gap rate. 1.00× equals the overall rate.",
    "Prevalence": "Prevalence is the share of cases with an observed gap in the stated evaluation sample. It is the no-information reference for Average Precision.",
    "Calibration": "Calibration asks whether groups given similar predicted probabilities experienced gaps at about those rates. It does not change the frozen scores.",
    "Gap": "An entrepreneurial gap is a model-relative label applied when observed startup activity is unusually low compared with an A6 expected benchmark. It is not causal.",
    "Alignment": "Alignment is observed minus expected startup rate, expressed in percentage points. It is not a causal effect.",
    "Expected rate": "Expected startup rate is the finalized A6 Model A benchmark for an available validation row. Missing expected values are not extrapolated.",
}
