"""Executive Overview of the frozen A6 results, sourced only from A7.2 artifacts."""

import streamlit as st

from ..charts import (
    build_calibration_chart,
    build_lift_chart,
    build_model_comparison_chart,
    build_top_risk_table,
    calibration_takeaway,
    comparison_takeaway,
    format_count,
    format_lift,
    format_probability,
    format_score,
    lift_takeaway,
)
from ..components import gap_explainer, render_footer, render_header
from ..constants import DATA_LAYER_REBUILD_COMMAND, PAGE_DESCRIPTIONS
from ..overview_data import HOLDOUT_TABLE_LABEL, TOP_N_OPTIONS, OverviewDataError, get_metric, load_overview_data
from ..glossary import GLOSSARY
from ..visual_style import PLOTLY_CONFIG


def _render_kpi(label: str, value: str, help_text: str) -> None:
    with st.container(border=True):
        st.metric(label, value, help=help_text)


def _render_workflow() -> None:
    steps = (
        ("1", "Historical conditions"),
        ("2", "Expected startup activity"),
        ("3", "Observed alignment"),
        ("4", "Development-defined gap"),
        ("5", "Three-year probability"),
    )
    columns = st.columns(len(steps))
    for column, (number, title) in zip(columns, steps):
        with column:
            st.markdown(f"**{number}. {title}**")


def _source_names(sources) -> list[str]:
    source_map = (
        ("Census Business Dynamics Statistics (BDS)", "Census BDS"),
        ("BLS Quarterly Census of Employment and Wages (QCEW)", "BLS QCEW"),
        ("American Community Survey (ACS)", "Census ACS"),
        ("Census County Business Patterns (CBP)", "Census CBP"),
    )
    available = set(sources["source_name"].astype(str))
    return [label for source, label in source_map if source in available]


def render() -> None:
    try:
        data = load_overview_data()
    except OverviewDataError as exc:
        st.error("Executive Overview data could not be loaded or does not meet its A7.2 contract.")
        st.caption(str(exc))
        st.code(DATA_LAYER_REBUILD_COMMAND, language="powershell")
        return

    metadata = data["metadata"]
    summary = data["model_summary"]
    predictions = data["predictions"]
    holdout = predictions.loc[predictions["development_or_holdout"] == "final_holdout"]
    holdout_n = int(holdout.shape[0])
    msa_count = int(holdout["cbsa_code"].nunique())
    sector_count = int(holdout["sector_code"].nunique())
    holdout_period = metadata["study_period"]["holdout_target"]

    render_header("Executive Overview", PAGE_DESCRIPTIONS["Executive Overview"], metadata)
    st.subheader("Research question")
    st.write(
        "How accurately can historical industry growth, prior entrepreneurial activity, "
        "labor-market conditions, and regional economic characteristics predict future "
        "entrepreneurial gaps within MSA-industry combinations?"
    )
    st.caption(
        f"Fixed evaluation population: {HOLDOUT_TABLE_LABEL} | Target years "
        f"{holdout_period[0]}-{holdout_period[-1]} | Predictor year t to t+{metadata['forecast_horizon_years']}"
    )

    st.subheader("Final temporal holdout results")
    kpi_rows = (
        (
            ("Average Precision", format_score(get_metric(summary, "final_holdout", "logistic", "AP")),
             GLOSSARY["AP"]),
            ("Gap prevalence", format_probability(get_metric(summary, "final_holdout", "logistic", "prevalence")),
             GLOSSARY["Prevalence"]),
            ("ROC-AUC", format_score(get_metric(summary, "final_holdout", "logistic", "ROC_AUC")),
             GLOSSARY["ROC-AUC"]),
            ("Top 10% lift", format_lift(get_metric(summary, "final_holdout", "logistic", "top10_lift")),
             GLOSSARY["Lift"]),
        ),
        (
            ("Brier score", format_score(get_metric(summary, "final_holdout", "logistic", "Brier")),
             GLOSSARY["Brier"]),
            ("Holdout observations", format_count(holdout_n), "Eligible MSA-sector prediction pairs in the final temporal holdout."),
            ("MSAs represented", format_count(msa_count), "Distinct metropolitan areas in the final prediction sample."),
            ("Sectors represented", format_count(sector_count), "Distinct analytical 2-digit NAICS sector codes in the final prediction sample."),
        ),
    )
    for row in kpi_rows:
        columns = st.columns(4)
        for column, (label, value, help_text) in zip(columns, row):
            with column:
                _render_kpi(label, value, help_text)

    st.subheader("Model hierarchy")
    st.markdown("**Primary model: Logistic regression**")
    hgb_ap_change = get_metric(summary, "final_holdout", "hist_gradient_boosting", "AP") - get_metric(summary, "final_holdout", "logistic", "AP")
    hgb_roc_change = get_metric(summary, "final_holdout", "hist_gradient_boosting", "ROC_AUC") - get_metric(summary, "final_holdout", "logistic", "ROC_AUC")
    st.write(
        f"HistGradientBoosting is a sensitivity model. On the Final temporal holdout its AP and ROC-AUC "
        f"were higher by {hgb_ap_change:.3f} and {hgb_roc_change:.3f}, respectively; the modest "
        "difference does not change the pre-locked, more interpretable logistic reference. "
        "This post-lock sensitivity comparison was not used to select the primary model."
    )

    st.subheader("Development and holdout")
    st.caption("Average Precision and ROC-AUC are ranking metrics (higher is better); Brier is probability error (lower is better).")
    st.plotly_chart(build_model_comparison_chart(summary), width="stretch", config=PLOTLY_CONFIG)
    st.caption(comparison_takeaway(summary))

    st.subheader("Where higher scores concentrated observed gaps")
    st.caption("Lift compares realized gap prevalence in the top-ranked share with overall Final temporal holdout prevalence; 1.00× is the overall rate.")
    st.plotly_chart(build_lift_chart(summary), width="stretch", config=PLOTLY_CONFIG)
    st.caption(lift_takeaway(summary))

    st.subheader("Calibration by score bin")
    st.caption("Each point compares the frozen logistic mean score with the later observed gap prevalence in an equal-count holdout bin. No recalibration is applied.")
    st.plotly_chart(build_calibration_chart(data["calibration"]), width="stretch", config=PLOTLY_CONFIG)
    st.caption(calibration_takeaway(data["calibration"]))

    st.subheader("Highest-ranked holdout cases")
    st.warning(
        f"{HOLDOUT_TABLE_LABEL}. Actual gap status is the later realized target outcome, "
        "shown only for retrospective evaluation; these are not live or current forecasts."
    )
    top_n = st.selectbox("Show highest-ranked cases", options=TOP_N_OPTIONS, index=0, key="overview_top_n")
    table = build_top_risk_table(predictions, top_n=top_n, labels=data["labels"])
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Predicted probability of gap": st.column_config.NumberColumn(
                "Predicted probability of gap (t+3)",
                format=".1%",
                help="Frozen primary logistic probability for the target year shown; retrospective holdout score.",
            ),
        },
    )

    st.subheader("How the entrepreneurial-gap measure works")
    gap_explainer()
    st.write(
        "Observed startup activity is the historical firm-startup rate. Expected startup activity is an A6 Model A benchmark based on prior startup activity, employment growth, regional controls, industry, and year. Alignment compares observed activity with that benchmark."
    )
    st.write(
        "A gap label marks unusually low alignment using a threshold fixed from development residuals only. The logistic model then estimates the probability of that label at t+3. A gap is model-relative, not proof of ecosystem failure."
    )
    with st.expander("Illustrative interpretation"):
        st.write(
            "If observed startup activity is below its expected benchmark, alignment is negative; it counts as an A6 gap only when it reaches the frozen development-only p20 cutoff. The later t+3 prediction is a probability for the evaluation design, not a causal or guaranteed outcome."
        )
    _render_workflow()

    st.subheader("What this means")
    left, right = st.columns(2)
    with left:
        st.markdown("**Can support**")
        st.write("- Rank eligible MSA-industry pairs by predicted future-gap probability.\n- Identify where realized gaps concentrated among historically high-scored holdout cases.\n- Support prioritization for further investigation.")
    with right:
        st.markdown("**Cannot do**")
        st.write("- Establish why a gap occurred or estimate a causal policy effect.\n- Guarantee that a gap will occur in a place or sector.\n- Prescribe funding or policy automatically.")

    st.info(
        "Holdout credibility: the model and target design were locked before holdout outcomes were evaluated; "
        "2021-2023 target outcomes were reserved from development and evaluated once. This is one temporal "
        "holdout, not proof of universal or external generalization."
    )

    coverage_counts = data["coverage"]["coverage_status"].value_counts().to_dict()
    st.subheader("Coverage and limitations")
    st.warning(
        "Model results use a patterned complete-case sample; earlier A6 audits found excluded observations "
        "disproportionately smaller and lower-startup. Industries are aggregated to 2-digit NAICS, and startup "
        "rates are narrower than entrepreneurship broadly. Holdout quality varies across years and MSA-size "
        "groups; equal reliability across places is not established. "
        f"The A5 descriptive screen covers {format_count(len(data['coverage']))} CBSAs "
        f"({format_count(coverage_counts.get('comparison_eligible', 0))} comparison-eligible; "
        f"{format_count(coverage_counts.get('thin', 0))} thin). These coverage labels are not model-confidence ratings."
    )
    st.markdown("[Review Data Quality & Limitations](/quality)")

    sources = _source_names(data["sources"])
    if sources:
        st.caption("Source systems represented in A7.2: " + " | ".join(sources))
    st.markdown("[Methods & Sources](/about)")
    render_footer(metadata)
