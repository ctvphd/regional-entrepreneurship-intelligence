"""Reusable UI components for the Assignment 7 shell."""

from __future__ import annotations

from io import StringIO

import pandas as pd
import streamlit as st

from .constants import APP_SUBTITLE, APP_TITLE
from .glossary import GLOSSARY


def render_header(page_title: str, description: str, metadata: dict) -> None:
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
    st.header(page_title)
    st.write(description)
    period = metadata.get("study_period", {}).get("descriptive", [2010, 2023])
    unit = metadata.get("unit_of_analysis", "CBSA x 2-digit NAICS sector x year")
    st.caption(f"Study period: {period[0]}-{period[1]} | Unit: {unit}")
    model_badge(metadata.get("primary_model", "logistic"), metadata.get("sensitivity_model"))


def render_footer(metadata: dict) -> None:
    st.divider()
    period = metadata.get("study_period", {}).get("descriptive", [2010, 2023])
    st.caption(
        f"Regional Entrepreneurship Intelligence | Data period {period[0]}-{period[1]} | Research use only. "
        "Results are model-relative and non-causal. Rebuildable from the "
        f"versioned A7.2 data layer (v{metadata.get('dashboard_data_version', 'unknown')})."
    )


def model_badge(primary: str, sensitivity: str | None = None) -> None:
    if primary != "logistic":
        raise ValueError(f"Unapproved primary model: {primary}")
    st.caption("Primary model: Logistic regression")
    if sensitivity == "hist_gradient_boosting":
        st.caption("Sensitivity model: HistGradientBoosting")


def gap_explainer() -> None:
    st.info(GLOSSARY["Gap"] + " It is not proof of ecosystem failure or a causal finding.")


def development_holdout_label(split: str) -> str:
    labels = {
        "development_oof": "Development OOF",
        "final_holdout": "Final temporal holdout",
    }
    try:
        return labels[split]
    except KeyError as exc:
        raise ValueError(f"Unknown evaluation split: {split}") from exc


def coverage_badge(status: str) -> str:
    labels = {
        "comparison_eligible": "Comparison eligible (A5 descriptive screen passed)",
        "thin": "Thin coverage (A5 descriptive screen not passed)",
    }
    try:
        label = labels[status]
    except KeyError as exc:
        raise ValueError(f"Unknown documented coverage status: {status}") from exc
    st.caption(f"Coverage: {label}")
    return label


def limitation_callout(message: str, *, warning: bool = False) -> None:
    (st.warning if warning else st.info)(message)


def empty_state(message: str) -> None:
    st.info(message)


def dataframe_csv_bytes(frame: pd.DataFrame) -> bytes:
    buffer = StringIO()
    frame.to_csv(buffer, index=False, lineterminator="\n")
    return buffer.getvalue().encode("utf-8")
