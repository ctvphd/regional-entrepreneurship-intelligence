"""Small, deterministic Explorer session-state helpers."""

from __future__ import annotations

from collections.abc import MutableMapping


FILTER_KEYS = (
    "selected_msa",
    "selected_sectors",
    "selected_year",
    "selected_risk_category",
    "selected_gap_status",
    "selected_has_prediction",
    "selected_top_n",
    "selected_prediction_split",
    "selected_prediction_year",
)


def default_filter_state(options: dict, prediction_years_by_split: dict | None = None) -> dict:
    years = options.get("year_options", [])
    prediction_years_by_split = prediction_years_by_split or {}
    holdout_years = prediction_years_by_split.get("final_holdout", [])
    return {
        "selected_msa": None,
        "selected_sectors": [],
        "selected_year": max(years) if years else None,
        "selected_risk_category": None,
        "selected_gap_status": None,
        "selected_has_prediction": False,
        "selected_top_n": 10,
        "selected_prediction_split": "final_holdout",
        "selected_prediction_year": max(holdout_years) if holdout_years else None,
    }


def initialize_filter_state(state: MutableMapping, options: dict, prediction_years_by_split: dict | None = None) -> None:
    prediction_years_by_split = prediction_years_by_split or {}
    defaults = default_filter_state(options, prediction_years_by_split)
    valid_msa = {row["value"] for row in options.get("msa_options", [])}
    valid_sectors = {row["value"] for row in options.get("sector_options", [])}
    valid_years = set(options.get("year_options", []))
    valid_gaps = set(options.get("observed_historical_gap_status_options", []))
    risk_options = set(options.get("risk_category_options", []))

    if state.get("selected_msa") not in valid_msa:
        state["selected_msa"] = defaults["selected_msa"]
    selected_sectors = state.get("selected_sectors", defaults["selected_sectors"])
    state["selected_sectors"] = [value for value in selected_sectors if value in valid_sectors]
    if state.get("selected_year") not in valid_years:
        state["selected_year"] = defaults["selected_year"]
    if state.get("selected_risk_category") not in risk_options:
        state["selected_risk_category"] = defaults["selected_risk_category"]
    if state.get("selected_gap_status") not in valid_gaps:
        state["selected_gap_status"] = defaults["selected_gap_status"]
    state["selected_has_prediction"] = bool(state.get("selected_has_prediction", False))
    if state.get("selected_top_n") not in (10, 25, 50):
        state["selected_top_n"] = defaults["selected_top_n"]
    valid_splits = {"final_holdout", "development_oof"} & set(prediction_years_by_split)
    if state.get("selected_prediction_split") not in valid_splits:
        state["selected_prediction_split"] = defaults["selected_prediction_split"]
    years_for_split = set(prediction_years_by_split.get(state["selected_prediction_split"], []))
    if state.get("selected_prediction_year") not in years_for_split:
        state["selected_prediction_year"] = max(years_for_split) if years_for_split else None


def reset_filter_state(state: MutableMapping, options: dict, prediction_years_by_split: dict | None = None) -> None:
    for key, value in default_filter_state(options, prediction_years_by_split).items():
        state[key] = value
