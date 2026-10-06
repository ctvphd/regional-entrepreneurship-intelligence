"""Fixed A6 performance page shell; charts are deferred to A7.6."""

import streamlit as st

from ..components import development_holdout_label, render_footer, render_header
from ..constants import PAGE_DESCRIPTIONS
from ..data_access import cached_metadata


def render() -> None:
    metadata = cached_metadata()
    render_header("Model Performance", PAGE_DESCRIPTIONS["Model Performance"], metadata)
    st.subheader("Development vs. final temporal holdout")
    st.caption(f"Splits: {development_holdout_label('development_oof')} and {development_holdout_label('final_holdout')}.")
    st.info("Fixed A6 comparison placeholder. Explorer filters do not affect these metrics.")
    for title in ("Model comparison", "Precision-recall and ROC", "Calibration", "Lift", "Temporal stability"):
        st.subheader(title)
        st.info(f"{title} visualization placeholder. Detailed diagnostics are added in A7.6.")
    render_footer(metadata)
