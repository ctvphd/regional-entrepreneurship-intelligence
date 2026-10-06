"""Fixed-study model performance and validation diagnostics."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..charts import (
    build_lift_comparison_chart,
    build_metric_comparison_chart,
    build_msa_size_performance_chart,
    build_performance_by_year_chart,
    build_performance_model_chart,
    build_pr_curve,
    build_reliability_chart,
    build_roc_curve,
    build_sector_performance_chart,
    format_count,
    format_lift,
    format_probability,
    format_score,
)
from ..components import development_holdout_label, render_footer, render_header
from ..constants import DATA_LAYER_REBUILD_COMMAND, PAGE_DESCRIPTIONS
from ..performance_data import (
    DISPLAY_MODELS,
    PerformanceDataError,
    build_risk_concentration_table as risk_concentration_table,
    build_sector_performance_table,
    load_performance_data,
    metric_value,
)
from ..glossary import GLOSSARY
from ..visual_style import PLOTLY_CONFIG


def _metric_card(column, label: str, value: str, help_text: str) -> None:
    with column:
        st.metric(label, value, help=help_text)


def _render_interpretation(summary: pd.DataFrame, calibration: pd.DataFrame) -> None:
    holdout_ap = metric_value(summary, "final_holdout", "logistic", "AP")
    holdout_prevalence = metric_value(summary, "final_holdout", "logistic", "prevalence")
    dev_ap = metric_value(summary, "development_oof", "logistic", "AP")
    holdout_auc = metric_value(summary, "final_holdout", "logistic", "ROC_AUC")
    dev_auc = metric_value(summary, "development_oof", "logistic", "ROC_AUC")
    holdout_brier = metric_value(summary, "final_holdout", "logistic", "Brier")
    dev_brier = metric_value(summary, "development_oof", "logistic", "Brier")
    hgb_ap = metric_value(summary, "final_holdout", "hist_gradient_boosting", "AP")
    logistic_bins = calibration.loc[
        (calibration.dataset_split == "final_holdout") & (calibration.model == "logistic")
    ]
    under = int((logistic_bins.observed_gap_prevalence > logistic_bins.mean_predicted_probability).sum())
    over = int((logistic_bins.observed_gap_prevalence < logistic_bins.mean_predicted_probability).sum())

    st.subheader("What the results say")
    st.write(
        f"The fixed logistic model ranked Final temporal holdout gaps above the no-information prevalence reference: "
        f"Average Precision was {holdout_ap:.3f} versus {holdout_prevalence:.3f} prevalence. "
        f"ROC-AUC was {holdout_auc:.3f} (random-ranking reference 0.500)."
    )
    st.write(
        f"Compared with Development OOF, Final temporal holdout AP was {dev_ap:.3f} to {holdout_ap:.3f} and ROC-AUC "
        f"was {dev_auc:.3f} to {holdout_auc:.3f}; Brier moved from {dev_brier:.3f} to "
        f"{holdout_brier:.3f}, where higher is worse. Ranking signal remained, while probability error increased."
    )
    st.write(
        f"HistGradientBoosting had Final temporal holdout AP {hgb_ap:.3f}; its difference from logistic is modest and "
        "does not overturn the pre-locked, more interpretable and stable logistic reference specification. It is sensitivity evidence, "
        "not a model-selection result."
    )
    st.write(
        f"In the ten frozen logistic Final temporal holdout calibration bins, observed prevalence was above the mean score "
        f"in {under} bins and below it in {over}; calibration varies across bins rather than following a "
        "perfect line. Lift and subgroup diagnostics below show concentration and heterogeneity, not causal effects."
    )


def _render_metric_glossary() -> None:
    with st.expander("Metric glossary and reading guide"):
        st.markdown(
            f"- **Prevalence:** {GLOSSARY['Prevalence']}\n"
            f"- **Average Precision (AP):** {GLOSSARY['AP']}\n"
            f"- **ROC-AUC:** {GLOSSARY['ROC-AUC']}\n"
            f"- **Brier score:** {GLOSSARY['Brier']}\n"
            "- **Recall:** share of positive cases captured at the A6 frozen diagnostic threshold.\n"
            "- **Precision:** share of selected cases that were positive at that same frozen threshold.\n"
            "- **F1:** harmonic mean of threshold-specific precision and recall.\n"
            f"- **Lift:** {GLOSSARY['Lift']}\n"
            f"- **Calibration:** {GLOSSARY['Calibration']} Points above the ideal line indicate underprediction in a bin; points below indicate overprediction.\n\n"
            "The diagnostic threshold and model were finalized in A6; this page has no control to tune either."
        )


def render() -> None:
    try:
        data = load_performance_data()
    except PerformanceDataError as exc:
        st.error("Model Performance data could not be loaded or does not meet its A7.2 contract.")
        st.caption(str(exc))
        st.code(DATA_LAYER_REBUILD_COMMAND, language="powershell")
        return

    metadata = data["metadata"]
    summary = data["model_summary"]
    predictions = data["predictions"]
    render_header("Model Performance", PAGE_DESCRIPTIONS["Model Performance"], metadata)
    holdout_n = int(predictions.loc[predictions.development_or_holdout == "final_holdout"].shape[0])
    st.caption(
        f"Fixed evaluation populations: {development_holdout_label('development_oof')} and "
        f"{development_holdout_label('final_holdout')}: {format_count(holdout_n)} "
        f"MSA-sector pairs | Predictor year t to target year t+{metadata['forecast_horizon_years']}"
    )
    st.info(
        "These fixed A6 metrics are not affected by Explorer selections. Holdout outcomes are retrospective "
        "evaluation labels, not live or current forecasts."
    )

    st.subheader("Final temporal holdout: logistic primary model")
    cards = (
        ("Average Precision", format_score(metric_value(summary, "final_holdout", "logistic", "AP")), "Primary ranking metric; compare with Final temporal holdout prevalence."),
        ("Gap prevalence", format_probability(metric_value(summary, "final_holdout", "logistic", "prevalence")), "No-information AP reference for this holdout population."),
        ("ROC-AUC", format_score(metric_value(summary, "final_holdout", "logistic", "ROC_AUC")), "0.500 is random discrimination; higher values rank better."),
        ("Brier score", format_score(metric_value(summary, "final_holdout", "logistic", "Brier")), "Mean squared probability error; lower is better."),
        ("Recall", format_score(metric_value(summary, "final_holdout", "logistic", "recall")), "At the A6 frozen diagnostic threshold; not tuned here."),
        ("Precision", format_score(metric_value(summary, "final_holdout", "logistic", "precision")), "At the same A6 frozen diagnostic threshold."),
        ("F1", format_score(metric_value(summary, "final_holdout", "logistic", "f1")), "Threshold-specific harmonic mean of precision and recall."),
        ("Top-decile lift", format_lift(metric_value(summary, "final_holdout", "logistic", "top10_lift")), "Gap prevalence in the top-ranked 10% relative to overall prevalence."),
    )
    for start in (0, 4):
        cols = st.columns(4)
        for col, (label, value, help_text) in zip(cols, cards[start:start + 4]):
            _metric_card(col, label, value, help_text)

    _render_interpretation(summary, data["calibration"])

    st.subheader("Development OOF vs final temporal holdout")
    st.caption("Fixed logistic metrics. Ranking metrics (AP and ROC-AUC): higher is better. Brier probability error: lower is better.")
    st.plotly_chart(build_metric_comparison_chart(summary), width="stretch", config=PLOTLY_CONFIG)
    ap_delta = metric_value(summary, "final_holdout", "logistic", "AP") - metric_value(summary, "development_oof", "logistic", "AP")
    auc_delta = metric_value(summary, "final_holdout", "logistic", "ROC_AUC") - metric_value(summary, "development_oof", "logistic", "ROC_AUC")
    brier_delta = metric_value(summary, "final_holdout", "logistic", "Brier") - metric_value(summary, "development_oof", "logistic", "Brier")
    st.caption(f"Final temporal holdout minus Development OOF: AP {ap_delta:+.3f}; ROC-AUC {auc_delta:+.3f}; Brier {brier_delta:+.3f} (positive means worse).")

    st.subheader("Final temporal holdout model comparison")
    st.markdown("**Primary model: Logistic regression**  \n**Sensitivity model: HistGradientBoosting**")
    st.caption("The prevalence benchmark anchors no-information ranking. In pooled Development OOF, the published fold-specific prevalence benchmark AP need not equal pooled natural prevalence; both source values are retained.")
    comparison_tabs = st.tabs(["Development OOF", "Final temporal holdout"])
    for tab, split in zip(comparison_tabs, ("development_oof", "final_holdout")):
        with tab:
            st.plotly_chart(build_performance_model_chart(summary, split), width="stretch", config=PLOTLY_CONFIG)
    if "random_forest" not in set(summary.model.astype(str)):
        st.caption("Random Forest is not shown: there is no finalized Random Forest metric row in the A7.2 model summary.")

    curve_left, curve_right = st.columns(2)
    with curve_left:
        curve_split = st.radio(
            "Evaluation population for PR/ROC/calibration curves",
            options=("final_holdout", "development_oof"),
            format_func=development_holdout_label,
            horizontal=True,
            key="performance_curve_split",
        )
    with curve_right:
        include_hgb = st.checkbox("Show HGB sensitivity curves", value=False, key="performance_include_hgb")
    prevalence = metric_value(summary, curve_split, "logistic", "prevalence")

    st.subheader("Precision-recall diagnostics")
    st.caption("AP is the primary metric for minority gap outcomes. The horizontal reference is prevalence, not an accuracy target.")
    discrimination_tabs = st.tabs(["Precision-recall", "ROC"])
    with discrimination_tabs[0]:
        st.caption("AP summarizes minority-class ranking; the reference line is this population's prevalence, not an accuracy target.")
        st.plotly_chart(build_pr_curve(predictions, curve_split, include_sensitivity=include_hgb, prevalence=prevalence), width="stretch", config=PLOTLY_CONFIG)
    with discrimination_tabs[1]:
        st.caption("ROC-AUC summarizes ranking across thresholds; the diagonal is random ranking. No operating threshold is selected here.")
        st.plotly_chart(build_roc_curve(predictions, curve_split, include_sensitivity=include_hgb), width="stretch", config=PLOTLY_CONFIG)

    st.subheader("Calibration")
    st.caption("Calibration asks whether bins assigned a probability near p experience gaps about p of the time. This uses finalized A6 bins; no recalibration is performed.")
    st.plotly_chart(build_reliability_chart(data["calibration"], curve_split, include_sensitivity=include_hgb), width="stretch", config=PLOTLY_CONFIG)
    cal = data["calibration"].loc[(data["calibration"].dataset_split == curve_split) & (data["calibration"].model == "logistic")].sort_values("risk_bin")
    under = int((cal.observed_gap_prevalence > cal.mean_predicted_probability).sum())
    over = int((cal.observed_gap_prevalence < cal.mean_predicted_probability).sum())
    st.caption(f"Logistic {development_holdout_label(curve_split)} bins: observed prevalence is above the mean score in {under}/{len(cal)} bins (underprediction), and below it in {over}/{len(cal)} bins (overprediction). Bin-level summaries do not imply smooth calibration between bins.")

    st.subheader("Lift and risk concentration")
    st.caption("Lift above 1.00x means the selected high-risk share contains observed gaps at a higher rate than the overall evaluated population.")
    st.plotly_chart(build_lift_comparison_chart(summary), width="stretch", config=PLOTLY_CONFIG)
    risk_table = risk_concentration_table(summary)
    st.dataframe(
        risk_table,
        hide_index=True,
        width="stretch",
        column_config={
            "Top-risk fraction": st.column_config.NumberColumn(format="0%"),
            "Observed gap prevalence (lift x overall)": st.column_config.NumberColumn("Observed gap prevalence (lift × overall)", format="0.0%"),
            "Overall prevalence": st.column_config.NumberColumn(format="0.0%"),
            "Lift": st.column_config.NumberColumn(format="0.00×"),
        },
    )
    st.caption("Selected N follows the A6 ceiling-of-fraction rule. The table's observed prevalence is the frozen lift multiplied by frozen overall prevalence; metrics are not recomputed from row-level outcomes.")

    st.subheader("Subgroup diagnostics")
    diagnostic_tabs = st.tabs(["By target year", "By MSA size", "By sector"])
    with diagnostic_tabs[0]:
        st.caption("Year-specific results are descriptive across the three final temporal holdout target years (2021–2023); variation does not establish pandemic causation.")
        st.plotly_chart(build_performance_by_year_chart(data["model_by_year"]), width="stretch", config=PLOTLY_CONFIG)
        logistic_years = data["model_by_year"].loc[(data["model_by_year"].dataset_split == "final_holdout") & (data["model_by_year"].model == "logistic")].sort_values("target_year")
        weak_ap = logistic_years.loc[logistic_years.AP.idxmin()]
        min_auc = logistic_years.loc[logistic_years.ROC_AUC.idxmin()]
        max_brier = logistic_years.loc[logistic_years.Brier.idxmax()]
        st.caption(f"Logistic AP was lowest for {int(weak_ap.predictor_year)}→{int(weak_ap.target_year)} ({weak_ap.AP:.3f}); ROC-AUC was lowest for {int(min_auc.predictor_year)}→{int(min_auc.target_year)} ({min_auc.ROC_AUC:.3f}); Brier was highest (worse) for {int(max_brier.predictor_year)}→{int(max_brier.target_year)} ({max_brier.Brier:.3f}).")
    with diagnostic_tabs[1]:
        st.caption("Groups use the finalized A6 training-defined size assignment. Differences reflect model behavior and potentially different sample composition.")
        st.plotly_chart(build_msa_size_performance_chart(data["model_by_msa_size"]), width="stretch", config=PLOTLY_CONFIG)
    with diagnostic_tabs[2]:
        st.caption("A6 suppresses sector AP/ROC-AUC below 30 positive outcomes or without a negative class; blank metrics remain unavailable.")
        st.plotly_chart(build_sector_performance_chart(data["model_by_sector"]), width="stretch", config=PLOTLY_CONFIG)
        sector_table = build_sector_performance_table(data["model_by_sector"])
        st.dataframe(
            sector_table, hide_index=True, width="stretch",
            column_config={
                "Prevalence": st.column_config.NumberColumn(format="0.0%"),
                "AP": st.column_config.NumberColumn(format="%.3f"),
                "ROC-AUC": st.column_config.NumberColumn(format="%.3f"),
            },
        )
        st.caption("Sector identity was important in A6 but does not imply equally strong within-sector predictive performance. The chart shows logistic AP for sectors meeting the frozen sufficiency rule.")

    st.warning("These metrics do not establish causality, universal performance, perfect classification, or current live forecasting. The final temporal holdout is one evaluation period.")
    _render_metric_glossary()
    with st.expander("Technical details and lineage"):
        st.write(
            "Fixed metric cards and comparisons are copied from dashboard_model_summary. Year, size, sector, and calibration values use their corresponding finalized A7.2 artifacts. PR/ROC point arrays are a deterministic evaluation-only transform of the frozen prediction probabilities and actual labels for the selected split; no model is fit, no probabilities are changed, and no threshold is optimized."
        )
        st.write(
            f"Model set available in the frozen summary: {', '.join(DISPLAY_MODELS[m] for m in DISPLAY_MODELS if m in set(summary.model.astype(str)))}. "
            "Logistic remains the primary/reference model; HistGradientBoosting is a sensitivity comparison."
        )
    render_footer(metadata)
