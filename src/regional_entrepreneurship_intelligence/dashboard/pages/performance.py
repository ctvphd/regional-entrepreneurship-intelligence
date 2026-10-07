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
from ..components import dataframe_csv_bytes, development_holdout_label, render_footer, render_header, render_metric_card, render_plotly_chart
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
from ..copy import METRIC_PRESENTATION


def _metric_card(column, label: str, value: str, help_text: str) -> None:
    card = METRIC_PRESENTATION.get(label)
    if card is None:
        card = {"headline": label, "technical": label, "plain": help_text}
    render_metric_card(column, card["headline"], value, card["technical"], card["plain"], help_text)


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

    st.subheader("What do the results tell us?")
    st.write(f"The model ranked later gap cases above a no-information comparison. Average Precision was {holdout_ap:.3f} versus a {holdout_prevalence:.3f} gap rate; ROC-AUC was {holdout_auc:.3f}.")
    st.write(f"Ranking results changed only slightly between development and the later evaluation period. Probability error increased: Brier moved from {dev_brier:.3f} to {holdout_brier:.3f} (lower is better).")
    st.write(f"The more flexible HistGradientBoosting check had AP {hgb_ap:.3f} in the later evaluation. The preselected logistic model remains primary; this comparison did not select it.")
    st.write(f"In the ten score groups, observed gap rates were above the average score in {under} groups and below it in {over}. The scores do not match observed rates perfectly.")


def _render_metric_glossary() -> None:
    with st.expander("What do these metrics mean? (technical definitions)"):
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
    render_header("Model Insights", PAGE_DESCRIPTIONS["Model Insights"], metadata)
    holdout_n = int(predictions.loc[predictions.development_or_holdout == "final_holdout"].shape[0])
    st.caption(
        f"Fixed evaluation populations: {development_holdout_label('development_oof')} and "
        f"{development_holdout_label('final_holdout')}: {format_count(holdout_n)} "
        f"MSA-sector pairs | Predictor year t to target year t+{metadata['forecast_horizon_years']}"
    )
    st.info("The scores below describe past evaluation samples. They are not live forecasts, and Explorer filters do not change them.")

    st.subheader("How well did the model identify later gaps?")
    cards = (
        ("AP", format_score(metric_value(summary, "final_holdout", "logistic", "AP")), "Primary ranking metric; compare with the observed gap rate."),
        ("ROC_AUC", format_score(metric_value(summary, "final_holdout", "logistic", "ROC_AUC")), "0.500 is random ranking; higher is better."),
        ("Brier", format_score(metric_value(summary, "final_holdout", "logistic", "Brier")), "Average squared probability error; lower is better."),
        ("lift", format_lift(metric_value(summary, "final_holdout", "logistic", "top10_lift")), "Gap rate in the highest-scored 10% compared with the overall rate."),
    )
    cols = st.columns(4)
    for col, (label, value, help_text) in zip(cols, cards):
        _metric_card(col, label, value, help_text)
    with st.expander("Additional sample and threshold measures"):
        secondary = (
            ("prevalence", format_probability(metric_value(summary, "final_holdout", "logistic", "prevalence")), "Share of evaluated cases with an observed gap."),
            ("Recall", format_score(metric_value(summary, "final_holdout", "logistic", "recall")), "At the A6 frozen diagnostic threshold; not tuned here."),
            ("Precision", format_score(metric_value(summary, "final_holdout", "logistic", "precision")), "At the same A6 frozen diagnostic threshold."),
            ("F1", format_score(metric_value(summary, "final_holdout", "logistic", "f1")), "Threshold-specific harmonic mean of precision and recall."),
        )
        cols = st.columns(4)
        for col, (label, value, help_text) in zip(cols, secondary):
            _metric_card(col, label, value, help_text)

    _render_interpretation(summary, data["calibration"])

    st.subheader("Did performance hold up on later data?")
    st.caption("Compare model results during development with results from a later evaluation period.")
    render_plotly_chart(build_metric_comparison_chart(summary))
    ap_delta = metric_value(summary, "final_holdout", "logistic", "AP") - metric_value(summary, "development_oof", "logistic", "AP")
    auc_delta = metric_value(summary, "final_holdout", "logistic", "ROC_AUC") - metric_value(summary, "development_oof", "logistic", "ROC_AUC")
    brier_delta = metric_value(summary, "final_holdout", "logistic", "Brier") - metric_value(summary, "development_oof", "logistic", "Brier")
    st.caption(f"Final temporal holdout minus Development OOF: AP {ap_delta:+.3f}; ROC-AUC {auc_delta:+.3f}; Brier {brier_delta:+.3f} (positive means worse).")

    st.subheader("How did the primary model compare with a more flexible check?")
    st.markdown("**Primary model: Logistic regression**  \n**Sensitivity model: HistGradientBoosting**")
    st.caption("The prevalence benchmark anchors no-information ranking. In pooled Development OOF, the published fold-specific prevalence benchmark AP need not equal pooled natural prevalence; both source values are retained.")
    comparison_tabs = st.tabs(["Development OOF", "Final temporal holdout"])
    for tab, split in zip(comparison_tabs, ("development_oof", "final_holdout")):
        with tab:
            render_plotly_chart(build_performance_model_chart(summary, split))
    if "random_forest" not in set(summary.model.astype(str)):
        st.caption("Random Forest is not shown: there is no finalized Random Forest metric row in the A7.2 model summary.")

    with st.expander("Technical details: model and evaluation design"):
        st.write("Development OOF means out-of-fold predictions made during expanding-window validation. Final temporal holdout refers to target years reserved from model development and evaluated once. All scores are retrospective.")
        st.write("The primary model is logistic regression. HistGradientBoosting is a sensitivity comparison for nonlinear patterns; it does not replace the locked primary model.")

    curve_left, curve_right = st.columns(2)
    with curve_left:
        curve_split = st.radio(
            "Which study period should the charts show?",
            options=("final_holdout", "development_oof"),
            format_func=development_holdout_label,
            horizontal=True,
            key="performance_curve_split",
        )
    with curve_right:
        include_hgb = st.checkbox("Include the more flexible comparison model", value=False, key="performance_include_hgb", help="Technical name: HistGradientBoosting sensitivity model.")
    prevalence = metric_value(summary, curve_split, "logistic", "prevalence")

    st.subheader("Did higher scores find more actual gaps?")
    st.caption("The curves show ranking across score cutoffs. The reference line is the gap rate, not an accuracy target.")
    discrimination_tabs = st.tabs(["Precision-recall", "ROC"])
    with discrimination_tabs[0]:
        st.caption("AP summarizes minority-class ranking; the reference line is this population's prevalence, not an accuracy target.")
        render_plotly_chart(build_pr_curve(predictions, curve_split, include_sensitivity=include_hgb, prevalence=prevalence))
    with discrimination_tabs[1]:
        st.caption("ROC-AUC summarizes ranking across thresholds; the diagonal is random ranking. No operating threshold is selected here.")
        render_plotly_chart(build_roc_curve(predictions, curve_split, include_sensitivity=include_hgb))

    st.subheader("Did predicted probabilities match what happened?")
    st.caption("Compare each score group’s average predicted probability with its observed gap rate.")
    render_plotly_chart(build_reliability_chart(data["calibration"], curve_split, include_sensitivity=include_hgb))
    cal = data["calibration"].loc[(data["calibration"].dataset_split == curve_split) & (data["calibration"].model == "logistic")].sort_values("risk_bin")
    under = int((cal.observed_gap_prevalence > cal.mean_predicted_probability).sum())
    over = int((cal.observed_gap_prevalence < cal.mean_predicted_probability).sum())
    st.caption(f"Logistic {development_holdout_label(curve_split)} bins: observed prevalence is above the mean score in {under}/{len(cal)} bins (underprediction), and below it in {over}/{len(cal)} bins (overprediction). Bin-level summaries do not imply smooth calibration between bins.")

    st.subheader("Were gaps concentrated among the highest-scored cases?")
    st.caption("A lift above 1.00× means the selected group had a higher observed gap rate than the full evaluation sample.")
    render_plotly_chart(build_lift_comparison_chart(summary))
    risk_table = risk_concentration_table(summary)
    risk_display = risk_table.rename(columns={
        "Top-risk fraction": "Highest-scored share",
        "Selected N (ceiling rule)": "Cases selected",
        "Observed gap prevalence (lift x overall)": "Observed gap prevalence",
    }).copy()
    risk_display["Highest-scored share"] = risk_display["Highest-scored share"].map(lambda value: f"{value:.0%}")
    risk_display["Observed gap prevalence"] = risk_display["Observed gap prevalence"].map(format_probability)
    risk_display["Overall prevalence"] = risk_display["Overall prevalence"].map(format_probability)
    risk_display["Lift"] = risk_display["Lift"].map(format_lift)
    st.dataframe(
        risk_display,
        hide_index=True,
        width="stretch",
        column_config={
            "Highest-scored share": st.column_config.TextColumn(),
            "Observed gap prevalence": st.column_config.TextColumn(),
            "Overall prevalence": st.column_config.TextColumn(),
            "Lift": st.column_config.TextColumn(),
        },
    )
    st.download_button("Download full-precision lift table (CSV)", dataframe_csv_bytes(risk_table), "risk_concentration.csv", "text/csv")
    st.caption("Selected N follows the A6 ceiling-of-fraction rule. The table's observed prevalence is the frozen lift multiplied by frozen overall prevalence; metrics are not recomputed from row-level outcomes.")

    st.subheader("Subgroup diagnostics")
    diagnostic_tabs = st.tabs(["By target year", "By MSA size", "By sector"])
    with diagnostic_tabs[0]:
        st.caption("These results compare three later target years. Differences are descriptive and do not establish why results varied.")
        render_plotly_chart(build_performance_by_year_chart(data["model_by_year"]))
        logistic_years = data["model_by_year"].loc[(data["model_by_year"].dataset_split == "final_holdout") & (data["model_by_year"].model == "logistic")].sort_values("target_year")
        weak_ap = logistic_years.loc[logistic_years.AP.idxmin()]
        min_auc = logistic_years.loc[logistic_years.ROC_AUC.idxmin()]
        max_brier = logistic_years.loc[logistic_years.Brier.idxmax()]
        st.caption(f"Logistic AP was lowest for {int(weak_ap.predictor_year)}→{int(weak_ap.target_year)} ({weak_ap.AP:.3f}); ROC-AUC was lowest for {int(min_auc.predictor_year)}→{int(min_auc.target_year)} ({min_auc.ROC_AUC:.3f}); Brier was highest (worse) for {int(max_brier.predictor_year)}→{int(max_brier.target_year)} ({max_brier.Brier:.3f}).")
    with diagnostic_tabs[1]:
        st.caption("Metro-size groups were set using training data. Differences may reflect both model behavior and sample composition.")
        render_plotly_chart(build_msa_size_performance_chart(data["model_by_msa_size"]))
    with diagnostic_tabs[2]:
        st.caption("Some industry metrics are hidden when the sample is too small or lacks one outcome type. A blank is unavailable, not zero.")
        render_plotly_chart(build_sector_performance_chart(data["model_by_sector"]))
        sector_table = build_sector_performance_table(data["model_by_sector"])
        st.dataframe(
            sector_table, hide_index=True, width="stretch",
            column_config={
                "Prevalence": st.column_config.NumberColumn(format="0.0%"),
                "AP": st.column_config.NumberColumn(format="%.3f"),
                "ROC-AUC": st.column_config.NumberColumn(format="%.3f"),
            },
        )
        st.caption("The chart shows logistic results only for industries that meet the fixed sample-size rule. A sector’s role in the model does not guarantee strong within-sector performance.")

    st.warning("These results do not show cause and effect or guarantee performance in other settings. The final evaluation covers one later period; it is not a current forecast.")
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
