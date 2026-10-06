"""Data quality and limitations page shell."""

import streamlit as st

from ..components import limitation_callout, render_footer, render_header
from ..constants import PAGE_DESCRIPTIONS
from ..data_access import cached_dataset, cached_metadata


def render() -> None:
    metadata = cached_metadata()
    coverage = cached_dataset("coverage")
    render_header("Data Quality & Limitations", PAGE_DESCRIPTIONS["Data Quality & Limitations"], metadata)
    st.subheader("Coverage")
    st.caption(f"Coverage artifact: {len(coverage):,} metropolitan areas. A5 status is comparison_eligible or thin.")
    for title, text in (
        ("Complete-case eligibility", "Model results apply to the complete-case samples documented in A6; eligibility is patterned and does not represent every MSA-sector-year."),
        ("MSA-size differences", "Holdout performance can vary across MSA-size groups; subgroup results are descriptive and do not guarantee equal reliability."),
        ("Sector variation", "Sector metrics with fewer than 30 positive events or no negative class are suppressed under A6 rules."),
        ("Missingness and suppression", "Source missingness and suppression are retained as nulls; unavailable values are not zero-filled."),
        ("Generalization", "The final 2021-2023 target period is one temporal holdout, not external validation or a live forecast."),
        ("Construct limitations", "Startup rates are a narrow entrepreneurship measure; the gap is relative to a fitted expectation and is not causal."),
    ):
        st.subheader(title)
        st.write(text)
    limitation_callout("Coverage status describes the A5 comparison screen, not model confidence or a quality rating.", warning=True)
    render_footer(metadata)
