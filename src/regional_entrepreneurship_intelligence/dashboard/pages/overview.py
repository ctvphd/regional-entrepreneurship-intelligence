"""Executive Overview shell; substantive analysis is deferred to A7.4."""

import streamlit as st

from ..components import gap_explainer, render_footer, render_header
from ..constants import PAGE_DESCRIPTIONS
from ..data_access import cached_metadata


def render() -> None:
    metadata = cached_metadata()
    render_header("Executive Overview", PAGE_DESCRIPTIONS["Executive Overview"], metadata)
    st.subheader("Research question")
    st.write("How does observed startup activity compare with expected activity, and which eligible MSA-sector observations had higher predicted future gap risk under the locked reference model?")
    st.subheader("At-a-glance results")
    st.caption("KPI placeholders: finalized holdout summaries will be presented in A7.4.")
    st.subheader("Main results")
    st.info("Main-results visualization placeholder.")
    st.subheader("Eligible comparisons")
    st.info("Qualified ranking placeholder. Holdout outcomes are retrospective, not current prospective advice.")
    st.subheader("What is an entrepreneurial gap?")
    gap_explainer()
    st.caption("Detailed visualizations are added in A7.4.")
    render_footer(metadata)
