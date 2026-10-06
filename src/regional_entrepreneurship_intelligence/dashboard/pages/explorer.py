"""Regional & Industry Explorer shell; analytics are deferred to A7.5."""

import streamlit as st

from ..components import empty_state, limitation_callout, render_footer, render_header
from ..constants import PAGE_DESCRIPTIONS
from ..data_access import cached_filter_options, cached_metadata
from ..filters import render_explorer_filters


def render() -> None:
    metadata = cached_metadata()
    options = cached_filter_options()
    render_header("Regional & Industry Explorer", PAGE_DESCRIPTIONS["Regional & Industry Explorer"], metadata)
    with st.sidebar:
        selections = render_explorer_filters(options)
    st.subheader("Selection")
    st.write(
        f"Metro: {selections['msa'] or 'All'} | Sectors: "
        f"{len(selections['sectors']) or 'All'} | Descriptive year: "
        f"{selections['descriptive_year']} | Observed gap: "
        f"{selections['observed_gap_status'] if selections['observed_gap_status'] is not None else 'All'}"
    )
    st.caption("These controls are scoped to the Explorer; fixed development and holdout metrics do not change.")
    st.subheader("Selected-observation summary")
    empty_state("Metrics placeholder. Detailed filtering and summaries are added in A7.5.")
    st.subheader("Historical trends")
    empty_state("Trend placeholder. Descriptive year is not predictor or target year.")
    st.subheader("Eligible comparisons")
    empty_state("Ranking placeholder. A7.5 will define eligible rows and the displayed fields.")
    st.subheader("CSV export")
    st.caption("Filtered CSV download is prepared for A7.5; no rows are exported in this shell.")
    limitation_callout("Risk-category filtering is unavailable because A7.2 has no approved category rule.")
    render_footer(metadata)
