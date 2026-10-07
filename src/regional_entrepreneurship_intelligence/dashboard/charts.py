"""Plotly figures and display-format helpers for the Executive Overview."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics import precision_recall_curve, roc_curve

from .overview_data import HOLDOUT_TABLE_LABEL, TOP_N_OPTIONS, get_metric
from .performance_data import DISPLAY_MODELS, build_risk_concentration_table, metric_value
from .visual_style import (
    DEVELOPMENT, EXPECTED, FINAL_HOLDOUT, GAP, GRID, HGB_SENSITIVITY,
    LOGISTIC_PRIMARY, NON_GAP, OBSERVED, REFERENCE, apply_dashboard_style,
    format_count, format_lift, format_probability, format_score,
)

PRIMARY = LOGISTIC_PRIMARY
HOLDOUT = HGB_SENSITIVITY


def build_model_comparison_chart(summary: pd.DataFrame) -> go.Figure:
    splits = (("development_oof", "Development OOF", DEVELOPMENT), ("final_holdout", "Final temporal holdout", FINAL_HOLDOUT))
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
        title="Did the primary model identify future gaps in both study periods?",
        barmode="group",
        height=390,
        margin={"l": 30, "r": 20, "t": 90, "b": 45},
        legend={"orientation": "h", "y": 1.14, "x": 0},
        font={"size": 13},
    )
    fig.update_yaxes(title_text="Metric value (0-1)", range=[0, 1], gridcolor=GRID, row=1, col=1)
    fig.update_yaxes(title_text="Brier score (lower is better)", range=[0, 1], gridcolor=GRID, row=1, col=2)
    fig.update_xaxes(showgrid=False)
    return apply_dashboard_style(fig)


def build_metric_comparison_chart(summary: pd.DataFrame) -> go.Figure:
    """Descriptive logistic-only comparison with metric direction kept separate."""
    return build_model_comparison_chart(summary)


def build_lift_chart(summary: pd.DataFrame) -> go.Figure:
    metrics = ("top10_lift", "top20_lift", "top25_lift")
    labels = ("Top 10%", "Top 20%", "Top 25%")
    values = [get_metric(summary, "final_holdout", "logistic", metric) for metric in metrics]
    fig = go.Figure(
        go.Bar(
            x=list(labels),
            y=values,
            marker_color=[HOLDOUT, PRIMARY, REFERENCE],
            text=[format_lift(value) for value in values],
            textposition="outside",
            customdata=[[metric] for metric in metrics],
            hovertemplate="%{x} of cases<br>Observed gap prevalence: %{y:.2f}x overall<extra></extra>",
        )
    )
    fig.add_hline(y=1.0, line_dash="dash", line_color=REFERENCE, annotation_text="Overall holdout rate (1.00x)", annotation_position="bottom right")
    fig.update_layout(
        title="Were gaps more common among the highest-scored cases?",
        height=350,
        margin={"l": 35, "r": 35, "t": 72, "b": 48},
        showlegend=False,
        font={"size": 13},
        yaxis={"title": "Observed gap prevalence / overall prevalence (lift)", "rangemode": "tozero", "gridcolor": GRID},
        xaxis={"title": "Cases ranked by frozen logistic probability", "showgrid": False},
    )
    return apply_dashboard_style(fig)


def build_calibration_chart(calibration: pd.DataFrame) -> go.Figure:
    bins = calibration.loc[
        (calibration["dataset_split"] == "final_holdout") & (calibration["model"] == "logistic")
    ].sort_values("risk_bin")
    if bins.empty:
        raise ValueError("dashboard_calibration.parquet: no final-holdout logistic bins")
    values = pd.concat(
        [bins["mean_predicted_probability"], bins["observed_gap_prevalence"]],
        ignore_index=True,
    ).dropna().astype(float)
    observed_min, observed_max = float(values.min()), float(values.max())
    padding = max((observed_max - observed_min) * 0.08, 0.01)
    axis_min = max(0.0, observed_min - padding)
    axis_max = min(1.0, observed_max + padding)
    custom = bins[["risk_bin", "n"]].to_numpy()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[axis_min, axis_max],
            y=[axis_min, axis_max],
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
            marker={"color": LOGISTIC_PRIMARY, "size": 9},
            hovertemplate=(
                "Risk bin %{customdata[0]}<br>Mean predicted: %{x:.1%}"
                "<br>Observed prevalence: %{y:.1%}<br>N=%{customdata[1]:,}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title="Did predicted probabilities match later gap rates?",
        height=390,
        margin={"l": 50, "r": 25, "t": 70, "b": 55},
        legend={"orientation": "h", "y": -0.24, "x": 0},
        font={"size": 13},
        xaxis={"title": "Mean predicted probability", "range": [axis_min, axis_max], "tickformat": ".0%", "gridcolor": GRID, "constrain": "domain"},
        yaxis={"title": "Observed gap prevalence", "range": [axis_min, axis_max], "tickformat": ".0%", "gridcolor": GRID},
    )
    return apply_dashboard_style(fig)


def _metric_direction_chart(summary: pd.DataFrame, split: str, models: tuple[str, ...]) -> go.Figure:
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=("Average Precision (higher)", "ROC-AUC (higher)", "Brier score (lower)"),
        horizontal_spacing=0.12,
    )
    metrics = (("AP", "AP"), ("ROC_AUC", "ROC-AUC"), ("Brier", "Brier"))
    colors = {"prevalence_benchmark": REFERENCE, "logistic": PRIMARY, "hist_gradient_boosting": HOLDOUT, "random_forest": "#5777A8"}
    symbols = {"prevalence_benchmark": "circle", "logistic": "diamond", "hist_gradient_boosting": "square", "random_forest": "triangle-up"}
    for model in models:
        label = DISPLAY_MODELS[model]
        for col, (metric, axis_label) in enumerate(metrics, start=1):
            value = metric_value(summary, split, model, metric)
            fig.add_trace(
                go.Bar(
                    x=[label], y=[value], name=label, legendgroup=model, showlegend=col == 1,
                    marker_color=colors[model],
                    marker_pattern_shape="/" if model == "hist_gradient_boosting" else "",
                    text=[f"{value:.3f}"], textposition="outside",
                    hovertemplate=f"{axis_label}: %{{y:.3f}}<extra>{label}</extra>",
                ), row=1, col=col,
            )
    fig.update_layout(
        title=f"How did the models compare? · {('Development OOF' if split == 'development_oof' else 'Final temporal holdout')}",
        barmode="group", height=390,
        margin={"l": 35, "r": 20, "t": 105, "b": 120},
        legend={"orientation": "h", "y": 1.18, "x": 0}, font={"size": 12},
    )
    for col in range(1, 4):
        fig.update_yaxes(title_text="Score (0-1)", range=[0, 1], gridcolor=GRID, row=1, col=col)
        fig.update_xaxes(showgrid=False, tickangle=-20, row=1, col=col)
    return apply_dashboard_style(fig)


def build_performance_model_chart(summary: pd.DataFrame, split: str = "final_holdout") -> go.Figure:
    if split not in {"development_oof", "final_holdout"}:
        raise ValueError(f"Unknown model-comparison split: {split}")
    models = tuple(model for model in ("prevalence_benchmark", "logistic", "hist_gradient_boosting", "random_forest")
                   if ((summary.dataset_split == split) & (summary.model == model)).any())
    if not {"prevalence_benchmark", "logistic", "hist_gradient_boosting"}.issubset(models):
        raise ValueError("dashboard_model_summary.parquet: finalized comparison models are incomplete")
    return _metric_direction_chart(summary, split, models)


def build_pr_curve(predictions: pd.DataFrame, split: str, *, include_sensitivity: bool = False, prevalence: float | None = None) -> go.Figure:
    rows = predictions.loc[predictions.development_or_holdout == split]
    if rows.empty:
        raise ValueError(f"dashboard_model_predictions.parquet: no rows for {split}")
    models = (("logistic_probability", "Logistic regression (primary)", PRIMARY, "solid"),)
    if include_sensitivity:
        models += (("hgb_probability", "HistGradientBoosting (sensitivity)", HOLDOUT, "dash"),)
    fig = go.Figure()
    for field, label, color, dash in models:
        precision, recall, _ = precision_recall_curve(rows.actual_gap.astype(int), rows[field].astype(float))
        fig.add_trace(go.Scatter(
            x=recall, y=precision, mode="lines", name=label,
            line={"color": color, "dash": dash, "width": 2.5},
            hovertemplate="Recall: %{x:.1%}<br>Precision: %{y:.1%}<extra>%{fullData.name}</extra>",
        ))
    if prevalence is not None:
        fig.add_hline(y=prevalence, line_dash="dot", line_color=REFERENCE,
                      annotation_text=f"No-information prevalence ({prevalence:.1%})", annotation_position="bottom right")
    fig.update_layout(
        title=f"How many later gaps did higher scores capture? · {('Development OOF' if split == 'development_oof' else 'Final temporal holdout')}",
        height=390, margin={"l": 55, "r": 30, "t": 75, "b": 55},
        legend={"orientation": "h", "y": -0.25, "x": 0}, font={"size": 13},
        xaxis={"title": "Recall", "range": [0, 1], "tickformat": ".0%", "gridcolor": GRID},
        yaxis={"title": "Precision", "range": [0, 1], "tickformat": ".0%", "gridcolor": GRID},
    )
    return apply_dashboard_style(fig)


def build_roc_curve(predictions: pd.DataFrame, split: str, *, include_sensitivity: bool = False) -> go.Figure:
    rows = predictions.loc[predictions.development_or_holdout == split]
    if rows.empty:
        raise ValueError(f"dashboard_model_predictions.parquet: no rows for {split}")
    models = (("logistic_probability", "Logistic regression (primary)", PRIMARY, "solid"),)
    if include_sensitivity:
        models += (("hgb_probability", "HistGradientBoosting (sensitivity)", HOLDOUT, "dash"),)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Random-ranking reference",
                             line={"color": REFERENCE, "dash": "dot", "width": 1.5}, hoverinfo="skip"))
    for field, label, color, dash in models:
        false_positive, true_positive, _ = roc_curve(rows.actual_gap.astype(int), rows[field].astype(float))
        fig.add_trace(go.Scatter(
            x=false_positive, y=true_positive, mode="lines", name=label,
            line={"color": color, "dash": dash, "width": 2.5},
            hovertemplate="False-positive rate: %{x:.1%}<br>True-positive rate: %{y:.1%}<extra>%{fullData.name}</extra>",
        ))
    fig.update_layout(
        title=f"How well were gap cases ranked above non-gap cases? · {('Development OOF' if split == 'development_oof' else 'Final temporal holdout')}",
        height=390, margin={"l": 55, "r": 30, "t": 75, "b": 55},
        legend={"orientation": "h", "y": -0.25, "x": 0}, font={"size": 13},
        xaxis={"title": "False-positive rate", "range": [0, 1], "tickformat": ".0%", "gridcolor": GRID},
        yaxis={"title": "True-positive rate", "range": [0, 1], "tickformat": ".0%", "gridcolor": GRID},
    )
    return apply_dashboard_style(fig)


def build_reliability_chart(calibration: pd.DataFrame, split: str, *, include_sensitivity: bool = False) -> go.Figure:
    models = (("logistic", "Logistic regression (primary)", PRIMARY, "circle", "solid"),)
    if include_sensitivity:
        models += (("hist_gradient_boosting", "HistGradientBoosting (sensitivity)", HOLDOUT, "diamond", "dash"),)
    selected = calibration.loc[calibration.dataset_split == split]
    if selected.empty:
        raise ValueError(f"dashboard_calibration.parquet: no bins for {split}")
    plotted_models = tuple(model for model, *_ in models)
    plotted = selected.loc[selected.model.isin(plotted_models)]
    values = pd.concat(
        [plotted.mean_predicted_probability, plotted.observed_gap_prevalence],
        ignore_index=True,
    ).dropna().astype(float)
    if values.empty:
        raise ValueError(f"dashboard_calibration.parquet: no usable bins for {split}")
    observed_min, observed_max = float(values.min()), float(values.max())
    padding = max((observed_max - observed_min) * 0.08, 0.01)
    axis_min = max(0.0, observed_min - padding)
    axis_max = min(1.0, observed_max + padding)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[axis_min, axis_max], y=[axis_min, axis_max], mode="lines", name="Ideal calibration",
                             line={"color": REFERENCE, "dash": "dot"}, hoverinfo="skip"))
    for model, label, color, symbol, dash in models:
        bins = selected.loc[selected.model == model].sort_values("risk_bin")
        fig.add_trace(go.Scatter(
            x=bins.mean_predicted_probability, y=bins.observed_gap_prevalence,
            customdata=bins[["risk_bin", "n"]], mode="lines+markers", name=label,
            line={"color": color, "dash": dash, "width": 2.3}, marker={"symbol": symbol, "size": 8},
            hovertemplate="Risk bin %{customdata[0]}<br>Mean predicted: %{x:.1%}<br>Observed: %{y:.1%}<br>N=%{customdata[1]:,}<extra>%{fullData.name}</extra>",
        ))
    title_split = "Development OOF" if split == "development_oof" else "Final temporal holdout"
    fig.update_layout(
        title=f"Did predicted probabilities match observed rates? · {title_split}", height=390,
        margin={"l": 55, "r": 25, "t": 75, "b": 65}, legend={"orientation": "h", "y": -0.25, "x": 0}, font={"size": 13},
        xaxis={"title": "Mean predicted probability", "range": [axis_min, axis_max], "tickformat": ".0%", "gridcolor": GRID, "constrain": "domain"},
        yaxis={"title": "Observed gap prevalence", "range": [axis_min, axis_max], "tickformat": ".0%", "gridcolor": GRID},
    )
    return apply_dashboard_style(fig)


def build_lift_comparison_chart(summary: pd.DataFrame) -> go.Figure:
    fractions = (("Top 10%", "top10_lift"), ("Top 20%", "top20_lift"), ("Top 25%", "top25_lift"))
    models = ("logistic", "hist_gradient_boosting")
    fig = go.Figure()
    colors = {"logistic": PRIMARY, "hist_gradient_boosting": HOLDOUT}
    symbols = {"logistic": "diamond", "hist_gradient_boosting": "square"}
    for model in models:
        values = [metric_value(summary, "final_holdout", model, metric) for _, metric in fractions]
        fig.add_trace(go.Bar(
            x=[name for name, _ in fractions], y=values, name=DISPLAY_MODELS[model],
            marker_color=colors[model], marker_pattern_shape="/" if model == "hist_gradient_boosting" else "",
            text=[f"{value:.2f}×" for value in values], textposition="outside",
            customdata=[[symbols[model]] for _ in values],
            hovertemplate="%{x}<br>Lift: %{y:.2f}× overall prevalence<extra>%{fullData.name}</extra>",
        ))
    fig.add_hline(y=1, line_color=REFERENCE, line_dash="dot", annotation_text="Overall rate (1.00×)")
    fig.update_layout(title="Which model concentrated more gaps in the highest-scored groups?",
                      barmode="group", height=370, margin={"l": 45, "r": 25, "t": 75, "b": 50},
                      legend={"orientation": "h", "y": 1.12, "x": 0}, font={"size": 13},
                      xaxis={"title": "Highest-scored share", "showgrid": False},
                      yaxis={"title": "Observed prevalence / overall prevalence (lift)", "rangemode": "tozero", "gridcolor": GRID})
    return apply_dashboard_style(fig)


def build_performance_by_year_chart(by_year: pd.DataFrame) -> go.Figure:
    rows = by_year.loc[by_year.dataset_split == "final_holdout"].sort_values(["predictor_year", "model"])
    fig = make_subplots(rows=1, cols=3, subplot_titles=("AP (higher)", "ROC-AUC (higher)", "Brier (lower)"), horizontal_spacing=0.12)
    colors = {"logistic": PRIMARY, "hist_gradient_boosting": HOLDOUT}
    markers = {"logistic": "diamond", "hist_gradient_boosting": "square"}
    for model in ("logistic", "hist_gradient_boosting"):
        model_rows = rows.loc[rows.model == model]
        for col, metric in enumerate(("AP", "ROC_AUC", "Brier"), start=1):
            fig.add_trace(go.Scatter(
                x=model_rows.target_year, y=model_rows[metric], mode="lines+markers",
                name=DISPLAY_MODELS[model], legendgroup=model, showlegend=col == 1,
                line={"color": colors[model], "dash": "solid" if model == "logistic" else "dash"},
                marker={"symbol": markers[model], "size": 9},
                customdata=model_rows[["predictor_year", "sample_n", "prevalence"]],
                hovertemplate="Predictor %{customdata[0]} → target %{x}<br>%{y:.3f}<br>N=%{customdata[1]:,}<br>Prevalence %{customdata[2]:.1%}<extra>%{fullData.name}</extra>",
            ), row=1, col=col)
    fig.update_layout(title="Did results differ across target years?", height=400,
                      margin={"l": 45, "r": 20, "t": 100, "b": 55},
                      legend={"orientation": "h", "y": 1.16, "x": 0}, font={"size": 12})
    for col in range(1, 4):
        fig.update_yaxes(title_text="Metric (0-1)", range=[0, 1], gridcolor=GRID, row=1, col=col)
        fig.update_xaxes(title_text="Target year", dtick=1, showgrid=False, row=1, col=col)
    return apply_dashboard_style(fig)


def build_msa_size_performance_chart(by_size: pd.DataFrame) -> go.Figure:
    rows = by_size.loc[by_size.dataset_split == "final_holdout"].copy()
    rows["msa_size_group"] = pd.Categorical(rows.msa_size_group, categories=("small", "middle", "large"), ordered=True)
    rows = rows.sort_values("msa_size_group")
    fig = make_subplots(rows=1, cols=3, subplot_titles=("AP (higher)", "ROC-AUC (higher)", "Top-decile lift (higher)"), horizontal_spacing=0.12)
    colors = {"logistic": PRIMARY, "hist_gradient_boosting": HOLDOUT}
    for model in ("logistic", "hist_gradient_boosting"):
        model_rows = rows.loc[rows.model == model]
        for col, metric in enumerate(("AP", "ROC_AUC", "top10_lift"), start=1):
            fig.add_trace(go.Bar(
                x=model_rows.msa_size_group.astype(str), y=model_rows[metric], name=DISPLAY_MODELS[model],
                legendgroup=model, showlegend=col == 1, marker_color=colors[model],
                marker_pattern_shape="/" if model == "hist_gradient_boosting" else "",
                customdata=model_rows[["sample_n", "msa_count", "prevalence"]],
                hovertemplate="%{x} MSA size<br>Value: %{y:.3f}<br>Prediction pairs: %{customdata[0]:,}<br>MSAs: %{customdata[1]:,}<br>Prevalence: %{customdata[2]:.1%}<extra>%{fullData.name}</extra>",
            ), row=1, col=col)
    fig.update_layout(title="Did model performance differ by metro size?",
                      barmode="group", height=410, margin={"l": 40, "r": 20, "t": 105, "b": 50},
                      legend={"orientation": "h", "y": 1.15, "x": 0}, font={"size": 12})
    for col in range(1, 4):
        fig.update_yaxes(title_text="Metric value", rangemode="tozero", gridcolor=GRID, row=1, col=col)
        fig.update_xaxes(title_text="Training-defined MSA-size group", showgrid=False, row=1, col=col)
    return apply_dashboard_style(fig)


def build_sector_performance_chart(by_sector: pd.DataFrame) -> go.Figure:
    rows = by_sector.loc[
        (by_sector.dataset_split == "final_holdout")
        & (by_sector.model == "logistic")
        & by_sector.sufficient_sample_flag.astype(bool)
    ].sort_values(["AP", "sector_name"], ascending=[True, True])
    if rows.empty:
        raise ValueError("dashboard_model_by_sector.parquet: no sufficient-sample logistic sectors")
    fig = go.Figure(go.Bar(
        x=rows.AP, y=rows.sector_name, orientation="h", name="Logistic regression (primary)",
        marker_color=PRIMARY,
        customdata=rows[["sample_n", "positive_n", "prevalence", "ROC_AUC"]],
        hovertemplate="%{y}<br>Average Precision: %{x:.3f}<br>N=%{customdata[0]:,}<br>Positive outcomes=%{customdata[1]:,}<br>Prevalence=%{customdata[2]:.1%}<br>ROC-AUC=%{customdata[3]:.3f}<extra></extra>",
    ))
    fig.update_layout(title="How well did the model identify gaps in each supported industry?",
                      height=590, margin={"l": 285, "r": 30, "t": 75, "b": 55}, showlegend=False, font={"size": 12},
                      xaxis={"title": "Average Precision (higher is better)", "rangemode": "tozero", "gridcolor": GRID},
                      yaxis={"title": "Final-holdout sector", "showgrid": False})
    return apply_dashboard_style(fig)


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
        f"Final temporal holdout AP changed {ap_change:+.3f} and ROC-AUC {roc_change:+.3f} versus Development OOF; "
        f"Brier changed {brier_change:+.3f} (a positive change is worse)."
    )


def lift_takeaway(summary: pd.DataFrame) -> str:
    prevalence = get_metric(summary, "final_holdout", "logistic", "prevalence")
    lift = get_metric(summary, "final_holdout", "logistic", "top10_lift")
    return (
        f"The highest-ranked 10% had {format_lift(lift)} the overall Final temporal holdout gap prevalence "
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
        f"Observed Final temporal holdout gap prevalence rose from {format_probability(first)} in the lowest score bin "
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
        customdata=rows[["msa_name", "sector_name", "expected_startup_rate", "observed_historical_gap_status"]].assign(
            observed_historical_gap_status=lambda data: data.observed_historical_gap_status.map({0: "No gap observed", 1: "Gap observed"}).fillna("Unavailable")
        ),
        hovertemplate=("Year %{x}<br>Observed startup rate: %{y:.2f}%<br>Expected startup rate: %{customdata[2]:.2f}%"
                       "<br>MSA: %{customdata[0]}<br>Sector: %{customdata[1]}"
                       "<br>Historical A6 status: %{customdata[3]}<extra></extra>"),
        connectgaps=False,
    ))
    if rows["expected_startup_rate"].notna().any():
        fig.add_trace(go.Scatter(
            x=rows["year"], y=rows["expected_startup_rate"], mode="lines+markers",
            name="Expected startup rate (A6 Model A)",
            line={"color": EXPECTED, "width": 2.2, "dash": "dash"},
            marker={"symbol": "diamond-open", "size": 7},
            customdata=rows[["msa_name", "sector_name"]],
            hovertemplate="Year %{x}<br>Expected startup rate: %{y:.2f}%<br>MSA: %{customdata[0]}<br>Sector: %{customdata[1]}<extra></extra>",
            connectgaps=False,
        ))
    gaps = rows.loc[(rows["observed_historical_gap_status"] == 1) & rows["startup_rate"].notna()]
    if not gaps.empty:
        fig.add_trace(go.Scatter(
            x=gaps["year"], y=gaps["startup_rate"], mode="markers",
            name="A6 gap observed (historical)",
            customdata=gaps[["msa_name", "sector_name"]],
            marker={"color": GAP, "symbol": "x", "size": 12, "line": {"width": 2}},
            hovertemplate="Year %{x}<br>Observed startup rate: %{y:.2f}%<br>MSA: %{customdata[0]}<br>Sector: %{customdata[1]}<br>Gap observed<extra></extra>",
        ))
    fig.update_layout(
        title="Is startup activity above or below expectation?",
        height=370,
        margin={"l": 55, "r": 25, "t": 75, "b": 50},
        legend={"orientation": "h", "y": -0.24, "x": 0}, font={"size": 13},
        xaxis={"title": "Descriptive calendar year", "dtick": 1, "showgrid": False},
        yaxis={"title": "Startup rate (percent units)", "ticksuffix": "%", "gridcolor": GRID},
    )
    return apply_dashboard_style(fig)


def build_startup_trend_chart(panel: pd.DataFrame) -> go.Figure:
    rows = panel.sort_values("year")
    if rows.empty or rows["startup_rate"].notna().sum() == 0:
        raise ValueError("No observed startup-rate values are available for this selection")
    fig = go.Figure(go.Scatter(
        x=rows["year"], y=rows["startup_rate"], mode="lines+markers",
        name="Observed firm startup rate", line={"color": PRIMARY, "width": 2.5},
        marker={"symbol": "circle", "size": 7}, connectgaps=False,
        customdata=rows[["msa_name", "sector_name"]],
        hovertemplate="Year %{x}<br>Startup rate: %{y:.2f}%<br>MSA: %{customdata[0]}<br>Sector: %{customdata[1]}<extra></extra>",
    ))
    fig.update_layout(
        title="How has startup activity changed over time?", height=320,
        margin={"l": 55, "r": 25, "t": 70, "b": 45}, showlegend=False,
        xaxis={"title": "Descriptive calendar year", "dtick": 1, "showgrid": False},
        yaxis={"title": "Startup rate (percent units)", "ticksuffix": "%", "gridcolor": GRID},
    )
    return apply_dashboard_style(fig)


def build_employment_growth_chart(panel: pd.DataFrame) -> go.Figure:
    rows = panel.sort_values("year")
    if rows.empty or rows["employment_growth"].notna().sum() == 0:
        raise ValueError("No employment-growth values are available for this selection")
    fig = go.Figure(go.Scatter(
        x=rows["year"], y=rows["employment_growth"], mode="lines+markers",
        name="QCEW employment growth", line={"color": EXPECTED, "width": 2.5, "dash": "dash"},
        marker={"symbol": "diamond", "size": 7}, connectgaps=False,
        customdata=rows[["msa_name", "sector_name"]],
        hovertemplate="Year %{x}<br>Employment growth: %{y:.1%}<br>MSA: %{customdata[0]}<br>Sector: %{customdata[1]}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=REFERENCE, line_dash="dot", annotation_text="No annual change")
    fig.update_layout(
        title="How has local industry employment changed?", height=320,
        margin={"l": 55, "r": 25, "t": 70, "b": 45}, showlegend=False,
        xaxis={"title": "Descriptive calendar year", "dtick": 1, "showgrid": False},
        yaxis={"title": "Employment growth", "tickformat": ".0%", "gridcolor": GRID},
    )
    return apply_dashboard_style(fig)


def build_alignment_history_chart(panel: pd.DataFrame) -> go.Figure:
    rows = panel.sort_values("year")
    if rows.empty or rows["alignment_residual"].notna().sum() == 0:
        raise ValueError("Alignment is unavailable for this selection")
    fig = go.Figure(go.Scatter(
        x=rows["year"], y=rows["alignment_residual"], mode="lines+markers",
        name="Observed minus expected", line={"color": PRIMARY, "width": 2.2},
        marker={"symbol": "circle", "size": 7}, connectgaps=False,
        customdata=rows[["msa_name", "sector_name", "observed_historical_gap_status"]].assign(
            observed_historical_gap_status=lambda data: data.observed_historical_gap_status.map({0: "No gap observed", 1: "Gap observed"}).fillna("Unavailable")
        ),
        hovertemplate=("Year %{x}<br>Alignment: %{y:.2f} percentage points"
                       "<br>MSA: %{customdata[0]}<br>Sector: %{customdata[1]}"
                       "<br>Historical A6 status: %{customdata[2]}<extra></extra>"),
    ))
    gaps = rows.loc[(rows["observed_historical_gap_status"] == 1) & rows["alignment_residual"].notna()]
    if not gaps.empty:
        fig.add_trace(go.Scatter(
            x=gaps["year"], y=gaps["alignment_residual"], mode="markers",
            name="A6 gap observed (historical)",
            marker={"color": GAP, "symbol": "x", "size": 12, "line": {"width": 2}},
            customdata=gaps[["msa_name", "sector_name"]],
            hovertemplate="Year %{x}<br>Alignment: %{y:.2f} percentage points<br>MSA: %{customdata[0]}<br>Sector: %{customdata[1]}<br>Gap observed<extra></extra>",
        ))
    fig.add_hline(y=0, line_color=REFERENCE, line_dash="dot", annotation_text="Observed = expected")
    fig.update_layout(
        title="When did startup activity fall behind expectations?", height=340,
        margin={"l": 55, "r": 25, "t": 75, "b": 45},
        legend={"orientation": "h", "y": -0.24, "x": 0},
        xaxis={"title": "Descriptive target year", "dtick": 1, "showgrid": False},
        yaxis={"title": "Observed minus expected (percentage points)", "gridcolor": GRID},
    )
    return apply_dashboard_style(fig)


def build_gap_timeline(panel: pd.DataFrame) -> go.Figure:
    rows = panel.loc[panel["observed_historical_gap_status"].notna()].sort_values("year").copy()
    if rows.empty:
        raise ValueError("No A6 fold-validation gap-status records are available for this selection")
    rows["status_label"] = rows["observed_historical_gap_status"].astype(int).map({0: "No gap observed", 1: "Gap observed"})
    fig = go.Figure()
    for status, label, symbol, color in ((0, "No gap observed", "circle", NON_GAP), (1, "Gap observed", "x", GAP)):
        group = rows.loc[rows["observed_historical_gap_status"].astype(int) == status]
        if group.empty:
            continue
        fig.add_trace(go.Scatter(
            x=group["year"], y=group["status_label"], mode="markers+text",
            name=label, text=["No gap" if status == 0 else "Gap"] * len(group),
            textposition="top center", marker={"symbol": symbol, "color": color, "size": 11},
            customdata=group[["msa_name", "sector_name", "gap_label_predictor_year"]],
            hovertemplate=("Target year %{x}<br>%{y}<br>MSA: %{customdata[0]}<br>Sector: %{customdata[1]}"
                           "<br>Associated predictor year: %{customdata[2]}"
                           "<br>Development OOF historical label<extra></extra>"),
        ))
    fig.update_layout(
        title="When was a gap observed in the historical study?",
        height=260,
        margin={"l": 40, "r": 20, "t": 70, "b": 45},
        xaxis={"title": "Target / descriptive year", "dtick": 1, "showgrid": False},
        yaxis={"title": "Observed status", "categoryorder": "array", "categoryarray": ["No gap observed", "Gap observed"]},
        legend={"orientation": "h", "y": -0.28, "x": 0},
    )
    return apply_dashboard_style(fig)


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
        name=f"Logistic regression (primary) - {label}",
        line={"color": PRIMARY, "width": 2.5, "dash": "solid" if split == "final_holdout" else "dash"},
        marker={"symbol": "circle", "size": 8},
        customdata=rows[["target_year", "actual_gap", "msa_name", "sector_name"]].assign(
            actual_gap=lambda data: data.actual_gap.map({0: "No gap observed", 1: "Gap observed"}).fillna("Unavailable")
        ),
        hovertemplate=("Predictor year %{x} to target year %{customdata[0]}"
                       "<br>Logistic probability: %{y:.1%}"
                       "<br>MSA: %{customdata[2]}<br>Sector: %{customdata[3]}"
                       "<br>Actual target gap (retrospective): %{customdata[1]}<extra></extra>"),
    ))
    fig.update_layout(
        title=f"What did the model estimate for later years? · {label}", height=320,
        margin={"l": 55, "r": 25, "t": 70, "b": 50}, showlegend=False,
        xaxis={"title": "Predictor year (t)", "dtick": 1, "showgrid": False},
        yaxis={"title": "Predicted probability of gap at t+3", "tickformat": ".0%", "range": [0, 1], "gridcolor": GRID},
    )
    return apply_dashboard_style(fig)
