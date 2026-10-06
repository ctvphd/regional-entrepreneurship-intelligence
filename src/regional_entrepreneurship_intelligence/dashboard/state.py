"""Small, deterministic Explorer session-state helpers."""

from __future__ import annotations

from collections.abc import MutableMapping


FILTER_KEYS = (
    "selected_msa",
    "selected_sectors",
    "selected_year",
    "selected_risk_category",
    "selected_gap_status",
)


def default_filter_state(options: dict) -> dict:
    years = options.get("year_options", [])
    return {
        "selected_msa": None,
        "selected_sectors": [],
        "selected_year": max(years) if years else None,
        "selected_risk_category": None,
        "selected_gap_status": None,
    }


def initialize_filter_state(state: MutableMapping, options: dict) -> None:
    defaults = default_filter_state(options)
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


def reset_filter_state(state: MutableMapping, options: dict) -> None:
    for key, value in default_filter_state(options).items():
        state[key] = value
