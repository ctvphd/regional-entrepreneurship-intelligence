"""Shared user-facing copy for plain-language dashboard presentation."""

METRIC_PRESENTATION = {
    "AP": {
        "headline": "Find future gaps",
        "technical": "Average Precision (AP)",
        "plain": "Higher means more observed gaps rise near the top of the ranking.",
    },
    "prevalence": {
        "headline": "Gap rate in this sample",
        "technical": "Observed prevalence",
        "plain": "The share of evaluated cases that had a gap.",
    },
    "ROC_AUC": {
        "headline": "Rank higher-risk cases",
        "technical": "ROC-AUC",
        "plain": "Higher means gap cases tend to rank above non-gap cases.",
    },
    "Brier": {
        "headline": "Probability error",
        "technical": "Brier score",
        "plain": "Lower means predicted probabilities were closer to outcomes.",
    },
    "lift": {
        "headline": "Gaps in the top 10%",
        "technical": "Top-decile lift",
        "plain": "How the highest-scored 10% compares with the overall gap rate.",
    },
}

GAP_PLAIN_LANGUAGE = (
    "Startup activity is compared with what the model expected for that place and industry. "
    "A gap is a model-relative label, not a judgment about a community."
)

MODEL_DETAILS = {
    "primary": "Logistic regression is the main model because it is easier to interpret and was locked before the final-period evaluation.",
    "sensitivity": "HistGradientBoosting checks whether allowing more complex, nonlinear patterns materially changes the results. It did not select the primary model.",
}

SELECTION_LIMITATION = (
    "Some places are represented better than others. Smaller metros and places with lower startup "
    "activity were more likely to have incomplete data, so results may be less reliable in those settings."
)

COVERAGE_LABELS = {
    "comparison_eligible": "Good comparison coverage",
    "thin": "Limited data coverage",
}
