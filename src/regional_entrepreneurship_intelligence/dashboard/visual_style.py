"""Shared visual semantics and Plotly styling for the dashboard."""

from __future__ import annotations

import plotly.graph_objects as go

OBSERVED = "#347C6A"
EXPECTED = "#5777A8"
LOGISTIC_PRIMARY = OBSERVED
HGB_SENSITIVITY = "#C56A3B"
GAP = "#9465A4"
NON_GAP = "#176B5B"
DEVELOPMENT = "#7A8983"
FINAL_HOLDOUT = "#C56A3B"
THIN_COVERAGE = "#A66E28"
SUFFICIENT_SAMPLE = OBSERVED
INSUFFICIENT_SAMPLE = DEVELOPMENT
REFERENCE = DEVELOPMENT
GRID = "rgba(128, 145, 137, 0.28)"
COLORWAY = [LOGISTIC_PRIMARY, HGB_SENSITIVITY, EXPECTED, "#7A3E8E", "#64736E"]

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True, "scrollZoom": False}


def apply_dashboard_style(fig: go.Figure) -> go.Figure:
    """Apply common typography, surface, hover, and axis defaults in place."""
    fig.update_layout(
        font={"family": "sans-serif", "size": 13},
        colorway=COLORWAY,
        legend={"font": {"size": 12}, "itemclick": "toggle", "groupclick": "togglegroup"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel={"font": {"size": 12}},
        autosize=True,
        hovermode="closest",
    )
    fig.update_xaxes(zerolinecolor=REFERENCE, title_font={"size": 12})
    fig.update_yaxes(zerolinecolor=REFERENCE, title_font={"size": 12})
    return fig


def format_probability(value: float) -> str:
    return f"{float(value):.1%}"


def format_rate(value: float) -> str:
    return f"{float(value):.2f}%"


def format_growth(value: float) -> str:
    return f"{float(value):.1%}"


def format_alignment(value: float) -> str:
    return f"{float(value):+.2f} pp"


def format_score(value: float) -> str:
    return f"{float(value):.3f}"


def format_lift(value: float) -> str:
    return f"{float(value):.2f}×"


def format_count(value: int) -> str:
    return f"{int(value):,}"
