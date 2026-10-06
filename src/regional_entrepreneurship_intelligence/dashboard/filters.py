"""Explorer-only controls backed by A7.2 filter options."""

from __future__ import annotations

import streamlit as st

from .state import initialize_filter_state, reset_filter_state


def render_explorer_filters(options: dict) -> dict:
    # These controls scope Explorer placeholders only; fixed performance and
    # holdout metrics always remain the finalized A6 populations.
    initialize_filter_state(st.session_state, options)
    st.subheader("Explorer filters")
    if st.button("Reset filters", key="reset_explorer_filters"):
        reset_filter_state(st.session_state, options)

    msa_rows = options.get("msa_options", [])
    msa_labels = {row["value"]: row["label"] for row in msa_rows}
    msa_values = [row["value"] for row in msa_rows]
    msa = st.selectbox(
        "Metropolitan area",
        options=[None, *msa_values],
        format_func=lambda value: "All metropolitan areas" if value is None else msa_labels[value],
        key="selected_msa",
        help="Search by metro name. This selection applies to the Explorer only.",
    )

    sector_rows = options.get("sector_options", [])
    sector_labels = {row["value"]: row["label"] for row in sector_rows}
    sectors = st.multiselect(
        "NAICS sector",
        options=[row["value"] for row in sector_rows],
        format_func=lambda value: f"{value} - {sector_labels[value]}",
        key="selected_sectors",
        help="Leave empty to include all available sectors in the Explorer.",
    )

    years = options.get("year_options", [])
    year = st.selectbox(
        "Descriptive year",
        options=years,
        key="selected_year",
        help="Panel year; distinct from predictor year and later target year.",
        disabled=not years,
    )

    # A7.2 intentionally contains no approved risk-category cutpoints.
    risk_options = options.get("risk_category_options", [])
    st.selectbox(
        "Risk category",
        options=[None, *risk_options],
        format_func=lambda value: "All categories" if value is None else str(value),
        key="selected_risk_category",
        disabled=not risk_options,
        help=options.get("risk_category_note", "No risk categories are approved."),
    )

    gap_values = options.get("observed_historical_gap_status_options", [])
    gap = st.selectbox(
        "Observed historical gap status",
        options=[None, *gap_values],
        format_func=lambda value: "All statuses" if value is None else ("Observed gap" if value == 1 else "No observed gap"),
        key="selected_gap_status",
        help="Historical OOF target-year status, not a current prediction.",
    )
    return {
        "msa": msa,
        "sectors": list(sectors),
        "descriptive_year": year,
        "risk_category": None,
        "observed_gap_status": gap,
    }
