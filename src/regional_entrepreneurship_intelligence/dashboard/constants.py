"""Shared display and application constants for the dashboard shell."""

APP_TITLE = "Regional Entrepreneurship Intelligence"
APP_SUBTITLE = (
    "Exploring MSA-industry entrepreneurial alignment and three-year "
    "future-gap risk."
)
PAGE_DESCRIPTIONS = {
    "Executive Overview": "Research scope and high-level results.",
    "Regional & Industry Explorer": "Explore historical MSA-sector observations.",
    "Model Performance": "Review fixed development and holdout diagnostics.",
    "Data Quality & Limitations": "Understand coverage, selection, and study limits.",
    "About / Methods / Sources": "Study methods, data provenance, and reproducibility.",
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
