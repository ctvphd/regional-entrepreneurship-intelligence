"""Shared display and application constants for the dashboard shell."""

APP_TITLE = "Regional Entrepreneurship Intelligence"
APP_SUBTITLE = (
    "Exploring MSA-industry entrepreneurial alignment and three-year "
    "future-gap risk."
)
PAGE_HEADLINES = {
    "Overview": "Where are startup gaps emerging, and can we spot patterns early?",
    "Explore Markets": "How is startup activity changing across places and industries?",
    "Model Insights": "How well does the model identify future gaps?",
    "Data & Confidence": "Where is the evidence strongest, and where should we be cautious?",
    "About the Analysis": "How was this analysis built?",
}
PAGE_DESCRIPTIONS = {
    "Overview": "See where startup activity keeps pace with local economic conditions and where later gaps appeared in the study. Results are historical, not live forecasts.",
    "Explore Markets": "Compare startup activity with the level expected from past, industry, and regional patterns. Review historical gaps and fixed three-year evaluation scores.",
    "Model Insights": "See how well the model identified later gaps during development and in a final period it had not seen.",
    "Data & Confidence": "Coverage differs across places and industries. Review what is well represented and where incomplete data calls for caution.",
    "About the Analysis": "Learn how the data, gap definition, predictive model, and validation process fit together.",
}
REQUIRED_DATASETS = (
    "msa_industry_year",
    "model_predictions",
    "model_summary",
    "calibration",
    "model_by_year",
    "model_by_sector",
    "model_by_msa_size",
    "coverage",
    "sources",
)
REQUIRED_ARTIFACTS = (
    "dashboard_metadata.json",
    "dashboard_filter_options.json",
    "dashboard_labels.json",
)
DATA_LAYER_REBUILD_COMMAND = (
    "uv run --offline python -m "
    "regional_entrepreneurship_intelligence.dashboard.run_data_layer"
)
