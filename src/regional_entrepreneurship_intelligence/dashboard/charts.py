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


def build_observed_expected_chart(panel: pd.DataFrame) -> go.Figure:
    rows = panel.sort_values("year")
    if rows.empty or rows["startup_rate"].notna().sum() == 0:
        raise ValueError("No observed startup-rate values are available for this selection")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rows["year"], y=rows["startup_rate"], mode="lines+markers",
        name="Observed startup rate", line={"color": PRIMARY, "width": 2.5},
        marker={"symbol": "circle", "size": 7},
        customdata=rows[["expected_startup_rate", "observed_historical_gap_status"]],
        hovertemplate=("Year %{x}<br>Observed: %{y:.2f}%<br>Expected: %{customdata[0]:.2f}%"
                       "<br>Historical A6 gap: %{customdata[1]}<extra></extra>"),
        connectgaps=False,
    ))
    if rows["expected_startup_rate"].notna().any():
        fig.add_trace(go.Scatter(
            x=rows["year"], y=rows["expected_startup_rate"], mode="lines+markers",
            name="Expected startup rate (A6 Model A)",
            line={"color": HOLDOUT, "width": 2.2, "dash": "dash"},
            marker={"symbol": "diamond-open", "size": 7},
            hovertemplate="Year %{x}<br>Expected: %{y:.2f}%<extra></extra>",
            connectgaps=False,
        ))
    gaps = rows.loc[(rows["observed_historical_gap_status"] == 1) & rows["startup_rate"].notna()]
    if not gaps.empty:
        fig.add_trace(go.Scatter(
            x=gaps["year"], y=gaps["startup_rate"], mode="markers",
            name="A6 gap observed (historical)",
            marker={"color": "#7A3E8E", "symbol": "x", "size": 12, "line": {"width": 2}},
            hovertemplate="Year %{x}<br>Observed startup rate: %{y:.2f}%<br>A6 gap observed<extra></extra>",
        ))
    fig.update_layout(
        title="Observed and expected startup activity",
        template="plotly_white", height=370,
        margin={"l": 55, "r": 25, "t": 75, "b": 50},
        legend={"orientation": "h", "y": -0.24, "x": 0}, font={"size": 13},
        xaxis={"title": "Descriptive calendar year", "dtick": 1, "showgrid": False},
        yaxis={"title": "Startup rate (percent units)", "ticksuffix": "%", "gridcolor": GRID},
    )
    return fig


def build_startup_trend_chart(panel: pd.DataFrame) -> go.Figure:
    rows = panel.sort_values("year")
    if rows.empty or rows["startup_rate"].notna().sum() == 0:
        raise ValueError("No observed startup-rate values are available for this selection")
    fig = go.Figure(go.Scatter(
        x=rows["year"], y=rows["startup_rate"], mode="lines+markers",
        name="Observed firm startup rate", line={"color": PRIMARY, "width": 2.5},
        marker={"symbol": "circle", "size": 7}, connectgaps=False,
        hovertemplate="Year %{x}<br>Startup rate: %{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        title="Historical startup-rate trend", template="plotly_white", height=320,
        margin={"l": 55, "r": 25, "t": 70, "b": 45}, showlegend=False,
        xaxis={"title": "Descriptive calendar year", "dtick": 1, "showgrid": False},
        yaxis={"title": "Startup rate (percent units)", "ticksuffix": "%", "gridcolor": GRID},
    )
    return fig


def build_employment_growth_chart(panel: pd.DataFrame) -> go.Figure:
    rows = panel.sort_values("year")
    if rows.empty or rows["employment_growth"].notna().sum() == 0:
        raise ValueError("No employment-growth values are available for this selection")
    fig = go.Figure(go.Scatter(
        x=rows["year"], y=rows["employment_growth"], mode="lines+markers",
        name="QCEW employment growth", line={"color": HOLDOUT, "width": 2.5, "dash": "dash"},
        marker={"symbol": "diamond", "size": 7}, connectgaps=False,
        hovertemplate="Year %{x}<br>Employment growth: %{y:.1%}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=REFERENCE, line_dash="dot", annotation_text="No annual change")
    fig.update_layout(
        title="Historical employment-growth trend", template="plotly_white", height=320,
        margin={"l": 55, "r": 25, "t": 70, "b": 45}, showlegend=False,
        xaxis={"title": "Descriptive calendar year", "dtick": 1, "showgrid": False},
        yaxis={"title": "Employment growth", "tickformat": ".0%", "gridcolor": GRID},
    )
    return fig


def build_alignment_history_chart(panel: pd.DataFrame) -> go.Figure:
    rows = panel.sort_values("year")
    if rows.empty or rows["alignment_residual"].notna().sum() == 0:
        raise ValueError("Alignment is unavailable for this selection")
    fig = go.Figure(go.Scatter(
        x=rows["year"], y=rows["alignment_residual"], mode="lines+markers",
        name="Observed minus expected", line={"color": PRIMARY, "width": 2.2},
        marker={"symbol": "circle", "size": 7}, connectgaps=False,
        customdata=rows["observed_historical_gap_status"],
        hovertemplate=("Year %{x}<br>Alignment: %{y:.2f} percentage points"
                       "<br>A6 gap status: %{customdata}<extra></extra>"),
    ))
    gaps = rows.loc[(rows["observed_historical_gap_status"] == 1) & rows["alignment_residual"].notna()]
    if not gaps.empty:
        fig.add_trace(go.Scatter(
            x=gaps["year"], y=gaps["alignment_residual"], mode="markers",
            name="A6 gap observed (historical)",
            marker={"color": "#7A3E8E", "symbol": "x", "size": 12, "line": {"width": 2}},
            hovertemplate="Year %{x}<br>Alignment: %{y:.2f} percentage points<br>A6 gap observed<extra></extra>",
        ))
    fig.add_hline(y=0, line_color=REFERENCE, line_dash="dot", annotation_text="Observed = expected")
    fig.update_layout(
        title="Historical entrepreneurial alignment", template="plotly_white", height=340,
        margin={"l": 55, "r": 25, "t": 75, "b": 45},
        legend={"orientation": "h", "y": -0.24, "x": 0},
        xaxis={"title": "Descriptive target year", "dtick": 1, "showgrid": False},
        yaxis={"title": "Observed minus expected (percentage points)", "gridcolor": GRID},
    )
    return fig


def build_gap_timeline(panel: pd.DataFrame) -> go.Figure:
    rows = panel.loc[panel["observed_historical_gap_status"].notna()].sort_values("year").copy()
    if rows.empty:
        raise ValueError("No A6 fold-validation gap-status records are available for this selection")
    rows["status_label"] = rows["observed_historical_gap_status"].astype(int).map({0: "No gap observed", 1: "Gap observed"})
    fig = go.Figure()
    for status, label, symbol, color in ((0, "No gap observed", "circle", PRIMARY), (1, "Gap observed", "x", "#7A3E8E")):
        group = rows.loc[rows["observed_historical_gap_status"].astype(int) == status]
        if group.empty:
            continue
        fig.add_trace(go.Scatter(
            x=group["year"], y=group["status_label"], mode="markers+text",
            name=label, text=["No gap" if status == 0 else "Gap"] * len(group),
            textposition="top center", marker={"symbol": symbol, "color": color, "size": 11},
            customdata=group["gap_label_predictor_year"],
            hovertemplate=("Target year %{x}<br>%{y}<br>Associated predictor year: %{customdata}"
                           "<br>Development OOF historical label<extra></extra>"),
        ))
    fig.update_layout(
        title="Historical A6 gap-status timeline (development OOF labels)",
        template="plotly_white", height=260,
        margin={"l": 40, "r": 20, "t": 70, "b": 45},
        xaxis={"title": "Target / descriptive year", "dtick": 1, "showgrid": False},
        yaxis={"title": "Observed status", "categoryorder": "array", "categoryarray": ["No gap observed", "Gap observed"]},
        legend={"orientation": "h", "y": -0.28, "x": 0},
    )
    return fig


def build_prediction_history_chart(predictions: pd.DataFrame) -> go.Figure:
    rows = predictions.sort_values("predictor_year")
    if rows.empty:
        raise ValueError("No retrospective prediction records are available for this selection")
    split = str(rows["development_or_holdout"].iloc[0])
    if rows["development_or_holdout"].nunique() != 1:
        raise ValueError("Prediction history must display exactly one evaluation split")
    label = "Final temporal holdout" if split == "final_holdout" else "Development OOF"
    fig = go.Figure(go.Scatter(
        x=rows["predictor_year"], y=rows["logistic_probability"], mode="lines+markers",
        name=f"Logistic primary - {label}", line={"color": HOLDOUT if split == "final_holdout" else PRIMARY, "width": 2.5},
        marker={"symbol": "circle", "size": 8},
        customdata=rows[["target_year", "actual_gap"]],
        hovertemplate=("Predictor year %{x} to target year %{customdata[0]}"
                       "<br>Logistic probability: %{y:.1%}"
                       "<br>Actual future gap (retrospective): %{customdata[1]}<extra></extra>"),
    ))
    fig.update_layout(
        title=f"Retrospective logistic prediction history - {label}", template="plotly_white", height=320,
        margin={"l": 55, "r": 25, "t": 70, "b": 50}, showlegend=False,
        xaxis={"title": "Predictor year (t)", "dtick": 1, "showgrid": False},
        yaxis={"title": "Predicted probability of gap at t+3", "tickformat": ".0%", "range": [0, 1], "gridcolor": GRID},
    )
    return fig
