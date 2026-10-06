"""Plotly figures and display-format helpers for the Executive Overview."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .overview_data import HOLDOUT_TABLE_LABEL, TOP_N_OPTIONS, get_metric

PRIMARY = "#176B5B"
HOLDOUT = "#C56A3B"
REFERENCE = "#64736E"
GRID = "#E3E9E6"


def format_probability(value: float) -> str:
    return f"{float(value):.1%}"


def format_score(value: float) -> str:
    return f"{float(value):.3f}"


def format_lift(value: float) -> str:
    return f"{float(value):.2f}\u00d7"


def format_count(value: int) -> str:
    return f"{int(value):,}"


def build_model_comparison_chart(summary: pd.DataFrame) -> go.Figure:
    splits = (("development_oof", "Development OOF", PRIMARY), ("final_holdout", "Final temporal holdout", HOLDOUT))
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Ranking: higher is better", "Probability error: lower is better"),
        horizontal_spacing=0.16,
    )
    ranking_metrics = (("AP", "Average Precision"), ("ROC_AUC", "ROC-AUC"))
    for split, label, color in splits:
        fig.add_trace(
            go.Bar(
                name=label,
                x=[title for _, title in ranking_metrics],
                y=[get_metric(summary, split, "logistic", metric) for metric, _ in ranking_metrics],
                marker_color=color,
                text=[format_score(get_metric(summary, split, "logistic", metric)) for metric, _ in ranking_metrics],
                textposition="outside",
                hovertemplate="%{x}<br>%{y:.3f}<extra>%{fullData.name}</extra>",
            ),
            row=1,
            col=1,
        )
        brier = get_metric(summary, split, "logistic", "Brier")
        fig.add_trace(
            go.Bar(
                name=label,
                x=["Brier score"],
                y=[brier],
                marker_color=color,
                text=[format_score(brier)],
                textposition="outside",
                showlegend=False,
                hovertemplate="Brier score %{y:.3f}<extra>%{fullData.name}</extra>",
            ),
            row=1,
            col=2,
        )
    fig.update_layout(
        title="Logistic model: development OOF and final holdout",
        template="plotly_white",
        barmode="group",
        height=390,
        margin={"l": 30, "r": 20, "t": 90, "b": 45},
        legend={"orientation": "h", "y": 1.14, "x": 0},
        font={"size": 13},
    )
    fig.update_yaxes(title_text="Metric value (0-1)", range=[0, 1], gridcolor=GRID, row=1, col=1)
    fig.update_yaxes(title_text="Brier score (lower is better)", range=[0, 1], gridcolor=GRID, row=1, col=2)
    fig.update_xaxes(showgrid=False)
    return fig


def build_lift_chart(summary: pd.DataFrame) -> go.Figure:
    metrics = ("top10_lift", "top20_lift", "top25_lift")
    labels = ("Top 10%", "Top 20%", "Top 25%")
    values = [get_metric(summary, "final_holdout", "logistic", metric) for metric in metrics]
    fig = go.Figure(
        go.Bar(
            x=list(labels),
            y=values,
            marker_color=[HOLDOUT, PRIMARY, "#7D8D87"],
            text=[format_lift(value) for value in values],
            textposition="outside",
            customdata=[[metric] for metric in metrics],
            hovertemplate="%{x} of cases<br>Observed gap prevalence: %{y:.2f}x overall<extra></extra>",
        )
    )
    fig.add_hline(y=1.0, line_dash="dash", line_color=REFERENCE, annotation_text="Overall holdout rate (1.00x)", annotation_position="bottom right")
    fig.update_layout(
        title="Gap concentration among the highest-ranked holdout cases",
        template="plotly_white",
        height=350,
        margin={"l": 35, "r": 35, "t": 72, "b": 48},
        showlegend=False,
        font={"size": 13},
        yaxis={"title": "Observed gap prevalence / overall prevalence (lift)", "rangemode": "tozero", "gridcolor": GRID},
        xaxis={"title": "Cases ranked by frozen logistic probability", "showgrid": False},
    )
    return fig


def build_calibration_chart(calibration: pd.DataFrame) -> go.Figure:
    bins = calibration.loc[
        (calibration["dataset_split"] == "final_holdout") & (calibration["model"] == "logistic")
    ].sort_values("risk_bin")
    if bins.empty:
        raise ValueError("dashboard_calibration.parquet: no final-holdout logistic bins")
    maximum = max(
        float(bins["mean_predicted_probability"].max()),
        float(bins["observed_gap_prevalence"].max()),
    )
    axis_max = min(1.0, max(0.1, (int(maximum * 20) + 1) / 20))
    custom = bins[["risk_bin", "n"]].to_numpy()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, axis_max],
            y=[0, axis_max],
            mode="lines",
            name="Perfect calibration reference",
            line={"color": REFERENCE, "dash": "dot", "width": 1.5},
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=bins["mean_predicted_probability"],
            y=bins["observed_gap_prevalence"],
            customdata=custom,
            mode="lines+markers",
            name="Observed holdout prevalence by score bin",
            line={"color": PRIMARY, "width": 2.5},
            marker={"color": HOLDOUT, "size": 9},
            hovertemplate=(
                "Risk bin %{customdata[0]}<br>Mean predicted: %{x:.1%}"
                "<br>Observed prevalence: %{y:.1%}<br>N=%{customdata[1]:,}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title="Final holdout calibration by frozen logistic score bin",
        template="plotly_white",
        height=390,
        margin={"l": 50, "r": 25, "t": 70, "b": 55},
        legend={"orientation": "h", "y": -0.24, "x": 0},
        font={"size": 13},
        xaxis={"title": "Mean predicted probability", "range": [0, axis_max], "tickformat": ".0%", "gridcolor": GRID},
        yaxis={"title": "Observed gap prevalence", "range": [0, axis_max], "tickformat": ".0%", "gridcolor": GRID, "scaleanchor": "x", "scaleratio": 1},
    )
    return fig


def build_top_risk_table(predictions: pd.DataFrame, top_n: int = 10, labels: dict | None = None) -> pd.DataFrame:
    if top_n not in TOP_N_OPTIONS:
        raise ValueError(f"top_n must be one of {TOP_N_OPTIONS}")
    holdout = predictions.loc[predictions["development_or_holdout"] == "final_holdout"].copy()
    if holdout.empty:
        raise ValueError(f"dashboard_model_predictions.parquet: no rows for {HOLDOUT_TABLE_LABEL}")
    if labels is None:
        gap_labels = {"0": "No observed gap", "1": "Observed gap"}
    else:
        gap_labels = labels.get("gap_status", {})
    holdout = holdout.sort_values(
        ["logistic_probability", "cbsa_code", "sector_code", "predictor_year"],
        ascending=[False, True, True, True],
        kind="mergesort",
    ).head(top_n)
    gap_values = holdout["actual_gap"].astype(int).astype(str)
    return pd.DataFrame(
        {
            "MSA": holdout["msa_name"].astype(str),
            "Industry sector": holdout["sector_name"].astype(str),
            "Predictor year (t)": holdout["predictor_year"].astype(int),
            "Target year (t+3)": holdout["target_year"].astype(int),
            "Predicted probability of gap": holdout["logistic_probability"].astype(float),
            "Observed target-year gap (retrospective)": gap_values.map(gap_labels).fillna("Unavailable").to_numpy(),
            "Coverage status": holdout["coverage_status"].astype(str),
        }
    ).reset_index(drop=True)


def comparison_takeaway(summary: pd.DataFrame) -> str:
    ap_change = get_metric(summary, "final_holdout", "logistic", "AP") - get_metric(summary, "development_oof", "logistic", "AP")
    roc_change = get_metric(summary, "final_holdout", "logistic", "ROC_AUC") - get_metric(summary, "development_oof", "logistic", "ROC_AUC")
    brier_change = get_metric(summary, "final_holdout", "logistic", "Brier") - get_metric(summary, "development_oof", "logistic", "Brier")
    return (
        f"Holdout AP changed {ap_change:+.3f} and ROC-AUC {roc_change:+.3f} versus development OOF; "
        f"Brier changed {brier_change:+.3f} (a positive change is worse)."
    )


def lift_takeaway(summary: pd.DataFrame) -> str:
    prevalence = get_metric(summary, "final_holdout", "logistic", "prevalence")
    lift = get_metric(summary, "final_holdout", "logistic", "top10_lift")
    return (
        f"The highest-ranked 10% had {format_lift(lift)} the overall holdout gap prevalence "
        f"({format_probability(prevalence)}); this is retrospective concentration, not a causal effect."
    )


def calibration_takeaway(calibration: pd.DataFrame) -> str:
    bins = calibration.loc[
        (calibration["dataset_split"] == "final_holdout") & (calibration["model"] == "logistic")
    ].sort_values("risk_bin")
    if bins.empty:
        raise ValueError("dashboard_calibration.parquet: no final-holdout logistic bins")
    first = float(bins.iloc[0]["observed_gap_prevalence"])
    last = float(bins.iloc[-1]["observed_gap_prevalence"])
    return (
        f"Observed holdout gap prevalence rose from {format_probability(first)} in the lowest score bin "
        f"to {format_probability(last)} in the highest; these bins are retrospective diagnostics, not recalibration."
    )
