"""Shared visual semantics and Plotly styling for the dashboard."""

from __future__ import annotations

import plotly.graph_objects as go

OBSERVED = "#176B5B"
EXPECTED = "#5777A8"
LOGISTIC_PRIMARY = "#176B5B"
HGB_SENSITIVITY = "#C56A3B"
GAP = "#7A3E8E"
NON_GAP = "#176B5B"
DEVELOPMENT = "#64736E"
FINAL_HOLDOUT = "#C56A3B"
THIN_COVERAGE = "#A66E28"
SUFFICIENT_SAMPLE = "#176B5B"
INSUFFICIENT_SAMPLE = "#64736E"
REFERENCE = "#64736E"
GRID = "#E3E9E6"
COLORWAY = [LOGISTIC_PRIMARY, HGB_SENSITIVITY, EXPECTED, "#7A3E8E", "#64736E"]

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True, "scrollZoom": False}


def apply_dashboard_style(fig: go.Figure) -> go.Figure:
    """Apply common typography, surface, hover, and axis defaults in place."""
    fig.update_layout(
        template="plotly_white",
        font={"family": "Arial, sans-serif", "size": 13, "color": "#24312E"},
        colorway=COLORWAY,
        legend={"font": {"size": 12}, "itemclick": "toggle", "groupclick": "togglegroup"},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        hoverlabel={"bgcolor": "#FFFFFF", "bordercolor": "#AAB7B2", "font": {"size": 12, "color": "#24312E"}},
        autosize=True,
        hovermode="closest",
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=REFERENCE, title_font={"size": 12})
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=REFERENCE, title_font={"size": 12})
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
