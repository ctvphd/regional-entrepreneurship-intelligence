"""Reusable UI components for the Assignment 7 shell."""

from __future__ import annotations

from io import StringIO

import pandas as pd
import streamlit as st

from .constants import APP_TITLE, PAGE_DESCRIPTIONS, PAGE_HEADLINES
from .copy import COVERAGE_LABELS, GAP_PLAIN_LANGUAGE
from .glossary import GLOSSARY
from .visual_style import PLOTLY_CONFIG


def render_header(page_title: str, description: str, metadata: dict) -> None:
    st.title(APP_TITLE)
    st.header(PAGE_HEADLINES.get(page_title, page_title))
    st.write(description or PAGE_DESCRIPTIONS.get(page_title, ""))
    period = metadata.get("study_period", {}).get("descriptive", [2010, 2023])
    st.caption(f"{period[0]}–{period[1]}  ·  Metro area × industry × year  ·  Three-year evaluation horizon")
    st.caption("Primary model: Logistic regression  ·  HistGradientBoosting used as a sensitivity check")


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
    st.caption("Primary: Logistic regression  ·  Sensitivity check: HistGradientBoosting" if sensitivity == "hist_gradient_boosting" else "Primary model: Logistic regression")


def gap_explainer() -> None:
    st.info(f"**What this means:** {GAP_PLAIN_LANGUAGE}")
    with st.expander("Technical definition: entrepreneurial gap"):
        st.write(GLOSSARY["Gap"])
        st.code("Alignment = observed startup rate − expected startup rate", language=None)


def render_metric_card(column, headline: str, value: str, technical_label: str, explanation: str, help_text: str) -> None:
    with column:
        with st.container(border=True):
            st.metric(headline, value, help=help_text)
            st.caption(f"{technical_label} · {explanation}")


def render_plotly_chart(figure) -> None:
    st.plotly_chart(figure, width="stretch", theme="streamlit", config=PLOTLY_CONFIG)


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
    try:
        label = COVERAGE_LABELS[status]
    except KeyError as exc:
        raise ValueError(f"Unknown documented coverage status: {status}") from exc
    canonical = "comparison_eligible" if status == "comparison_eligible" else "thin"
    st.caption(f"{label} · A5 status: `{canonical}`")
    return label


def limitation_callout(message: str, *, warning: bool = False) -> None:
    (st.warning if warning else st.info)(message)


def empty_state(message: str) -> None:
    st.info(message)


def dataframe_csv_bytes(frame: pd.DataFrame) -> bytes:
    buffer = StringIO()
    frame.to_csv(buffer, index=False, lineterminator="\n")
    return buffer.getvalue().encode("utf-8")
