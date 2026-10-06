"""About, methods, and source-reference shell."""

import streamlit as st

from ..components import development_holdout_label, gap_explainer, model_badge, render_footer, render_header
from ..constants import PAGE_DESCRIPTIONS
from ..data_access import cached_dataset, cached_metadata


def render() -> None:
    metadata = cached_metadata()
    render_header("About the Analysis", PAGE_DESCRIPTIONS["About the Analysis"], metadata)
    st.subheader("Project overview")
    st.write("This research describes MSA-by-industry startup activity and evaluates whether frozen models rank later model-relative entrepreneurial gaps.")
    st.write("Research question: How does observed startup activity compare with expected activity, and which eligible MSA-sector observations had higher predicted future gap risk under the locked reference model?")
    st.subheader("Unit and period")
    study = metadata["study_period"]
    st.write(f"{metadata['unit_of_analysis']}; descriptive years {study['descriptive'][0]}-{study['descriptive'][1]}.")
    st.subheader("Expected activity and gap")
    gap_explainer()
    st.caption(metadata["target_definition"])
    st.subheader("Prediction horizon and model")
    st.write(f"Predictor year t to target year t+{metadata['forecast_horizon_years']}; final target years {study['holdout_target'][0]}-{study['holdout_target'][-1]}.")
    model_badge(metadata["primary_model"], metadata.get("sensitivity_model"))
    st.caption(f"Evaluation populations: {development_holdout_label('development_oof')} and {development_holdout_label('final_holdout')}. The temporal holdout is retrospective.")
    st.subheader("Robustness")
    st.write("Assignment 6 robustness and generalization analyses remain documented in the frozen research outputs; this shell does not recompute or reselect any sensitivity results.")
    st.subheader("Data sources")
    st.dataframe(cached_dataset("sources"), hide_index=True, use_container_width=True)
    st.subheader("Reproducibility")
    st.write(f"Dashboard data version {metadata['dashboard_data_version']}; A6 reference `{metadata['final_A6_commit']}`.")
    st.caption("No causal claim. Source lineage and field definitions are documented in the repository data dictionary and source-lineage documents.")
    render_footer(metadata)
