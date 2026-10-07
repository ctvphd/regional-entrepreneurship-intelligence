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
from ..components import gap_explainer, render_footer, render_header, render_metric_card, render_plotly_chart
from ..constants import DATA_LAYER_REBUILD_COMMAND, PAGE_DESCRIPTIONS
from ..overview_data import HOLDOUT_TABLE_LABEL, TOP_N_OPTIONS, OverviewDataError, get_metric, load_overview_data
from ..glossary import GLOSSARY
from ..copy import METRIC_PRESENTATION, MODEL_DETAILS, SELECTION_LIMITATION


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

    render_header("Overview", PAGE_DESCRIPTIONS["Overview"], metadata)
    st.subheader("What did the model find?")
    st.caption(f"Later outcomes from {holdout_period[0]}–{holdout_period[-1]} · Historical analysis, not a live forecast")
    primary_metrics = (
        ("Average Precision", format_score(get_metric(summary, "final_holdout", "logistic", "AP")), "Compared with the observed gap rate; higher means stronger ranking."),
        ("Top 10% lift", format_lift(get_metric(summary, "final_holdout", "logistic", "top10_lift")), "Observed gap prevalence in the highest-scored tenth, relative to the full sample."),
        ("Evaluation coverage", f"{format_count(msa_count)} metros · {format_count(sector_count)} industries", f"{format_count(holdout_n)} eligible metro-industry cases in the final evaluation."),
    )
    columns = st.columns(3)
    for column, (label, value, help_text) in zip(columns, primary_metrics):
        with column:
            st.metric(label, value, help=help_text)
    st.subheader("Three things to know")
    ap_delta = get_metric(summary, "final_holdout", "logistic", "AP") - get_metric(summary, "development_oof", "logistic", "AP")
    auc_delta = get_metric(summary, "final_holdout", "logistic", "ROC_AUC") - get_metric(summary, "development_oof", "logistic", "ROC_AUC")
    st.markdown(
        f"- **Ranking:** AP was {get_metric(summary, 'final_holdout', 'logistic', 'AP'):.3f} versus a "
        f"{get_metric(summary, 'final_holdout', 'logistic', 'prevalence'):.3f} gap rate; ROC-AUC changed {auc_delta:+.3f} from development.\n"
        f"- **Concentration:** the top-scored tenth had {format_lift(get_metric(summary, 'final_holdout', 'logistic', 'top10_lift'))} "
        "the overall gap prevalence in this retrospective evaluation.\n"
        f"- **Comparison:** the flexible HGB check changed AP by {get_metric(summary, 'final_holdout', 'hist_gradient_boosting', 'AP') - get_metric(summary, 'final_holdout', 'logistic', 'AP'):+.3f}; "
        "logistic remains the prespecified primary model."
    )
    st.caption("Next: Explore Markets to compare a specific metro and industry.")

    st.subheader("Did results hold up in later data?")
    st.markdown("**Primary model: Logistic regression**")
    hgb_ap_change = get_metric(summary, "final_holdout", "hist_gradient_boosting", "AP") - get_metric(summary, "final_holdout", "logistic", "AP")
    hgb_roc_change = get_metric(summary, "final_holdout", "hist_gradient_boosting", "ROC_AUC") - get_metric(summary, "final_holdout", "logistic", "ROC_AUC")
    st.write(
        f"HistGradientBoosting, a more flexible comparison model, scored {hgb_ap_change:.3f} higher on AP and "
        f"{hgb_roc_change:.3f} higher on ROC-AUC in the final evaluation. The difference is modest. "
        f"{MODEL_DETAILS['primary']} This comparison did not select the primary model."
    )

    st.subheader("Did the results hold up in the final evaluation?")
    st.caption("Compare model ranking across development and later data. The Brier score measures probability error; lower is better.")
    render_plotly_chart(build_model_comparison_chart(summary))
    st.caption(comparison_takeaway(summary))

    st.subheader("Were gaps more common among the highest-scored cases?")
    st.caption("The highest-scored 10% is compared with the overall gap rate. A value of 1.00× means the rates were equal.")
    render_plotly_chart(build_lift_chart(summary))
    st.caption(lift_takeaway(summary))

    with st.expander("Probability quality"):
        st.caption("Each point compares a group’s average predicted probability with the share that later had a gap.")
        render_plotly_chart(build_calibration_chart(data["calibration"]))
        st.caption(calibration_takeaway(data["calibration"]))

    st.subheader("Which cases received the highest scores?")
    st.warning(
        f"These records come from the {holdout_period[0]}–{holdout_period[-1]} evaluation. "
        "The gap status happened later and is shown only for retrospective checking; these are not live forecasts."
    )
    top_n = st.selectbox("Show highest-ranked cases", options=TOP_N_OPTIONS, index=0, key="overview_top_n")
    table = build_top_risk_table(predictions, top_n=top_n, labels=data["labels"])
    table["Coverage status"] = table["Coverage status"].map({
        "comparison_eligible": "Good comparison coverage",
        "thin": "Limited data coverage",
    }).fillna("Not available")
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
            "Coverage status": st.column_config.TextColumn(
                help="Plain-language display of the unchanged A5 status values comparison_eligible and thin. Coverage is not prediction confidence."
            ),
        },
    )

    st.subheader("What does a gap mean?")
    gap_explainer()
    st.write("Expected startup activity is an estimate based on past startup activity and regional and industry conditions. It describes a comparison point, not an ideal level.")
    with st.expander("Technical details: expected rate and gap label"):
        st.write("Alignment is observed startup rate minus expected startup rate. The A6 gap label uses a threshold fixed from development data; the model then estimates the probability of that label at t+3.")
        st.write(f"{GLOSSARY['Expected rate']} {GLOSSARY['Alignment']}")
    with st.expander("Illustrative interpretation"):
        st.write(
            "If observed startup activity is below its expected benchmark, alignment is negative; it counts as an A6 gap only when it reaches the frozen development-only p20 cutoff. The later t+3 prediction is a probability for the evaluation design, not a causal or guaranteed outcome."
        )
    _render_workflow()

    st.subheader("What can these results support?")
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
    st.subheader("Where should you use more caution?")
    eligible_label = "Good comparison coverage"
    limited_label = "Limited data coverage"
    st.warning(
        SELECTION_LIMITATION + " "
        "Industries are grouped into broad two-digit sectors, and startup rates do not capture every form of entrepreneurship. "
        "Results vary across years and metro-size groups; equal reliability across places is not established. "
        f"The A5 descriptive screen covers {format_count(len(data['coverage']))} CBSAs "
        f"({format_count(coverage_counts.get('comparison_eligible', 0))} {eligible_label}; "
        f"{format_count(coverage_counts.get('thin', 0))} {limited_label}). Coverage is not model confidence."
    )
    st.markdown("[Review data coverage and limitations](/quality)")

    sources = _source_names(data["sources"])
    if sources:
        st.caption("Source systems represented in A7.2: " + " | ".join(sources))
    with st.expander("Technical details and metric definitions"):
        st.write(f"Evaluation sample: {HOLDOUT_TABLE_LABEL}; target years {holdout_period[0]}–{holdout_period[-1]}, using predictor information from three years earlier.")
        st.markdown("- **Average Precision:** " + GLOSSARY["AP"] + "\n- **ROC-AUC:** " + GLOSSARY["ROC-AUC"] + "\n- **Brier score:** " + GLOSSARY["Brier"] + "\n- **Lift:** " + GLOSSARY["Lift"] + "\n- **Calibration:** " + GLOSSARY["Calibration"])
        st.write(MODEL_DETAILS["sensitivity"])
    st.markdown("[How the analysis was built](/about)")
    render_footer(metadata)
