"""Interactive historical and retrospective MSA-industry Explorer."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from regional_entrepreneurship_intelligence.dashboard.charts import (
    build_alignment_history_chart,
    build_employment_growth_chart,
    build_gap_timeline,
    build_observed_expected_chart,
    build_prediction_history_chart,
)
from regional_entrepreneurship_intelligence.dashboard.components import (
    coverage_badge,
    dataframe_csv_bytes,
    empty_state,
    limitation_callout,
    render_footer,
    render_header,
    render_plotly_chart,
)
from regional_entrepreneurship_intelligence.dashboard.constants import PAGE_DESCRIPTIONS
from regional_entrepreneurship_intelligence.dashboard.data_access import (
    cached_dataset,
    cached_filter_options,
    cached_labels,
    cached_metadata,
)
from regional_entrepreneurship_intelligence.dashboard.explorer_data import (
    ExplorerDataError,
    alignment_interpretation,
    attach_prediction_records,
    build_top_risk_ranking,
    filter_explorer_data,
    filter_predictions,
    filtered_csv_frame,
    selection_summary,
    validate_explorer_inputs,
)
from regional_entrepreneurship_intelligence.dashboard.filters import render_explorer_filters
from regional_entrepreneurship_intelligence.dashboard.state import initialize_filter_state
from regional_entrepreneurship_intelligence.dashboard.glossary import GLOSSARY
from regional_entrepreneurship_intelligence.dashboard.visual_style import format_alignment, format_growth, format_rate
from regional_entrepreneurship_intelligence.dashboard.copy import COVERAGE_LABELS


def _rate(value) -> str:
    return "N/A" if pd.isna(value) else format_rate(float(value))


def _growth(value) -> str:
    return "N/A" if pd.isna(value) else format_growth(float(value))


def _alignment(value) -> str:
    return "N/A" if pd.isna(value) else format_alignment(float(value))


def _status(value, labels: dict) -> str:
    if pd.isna(value):
        return "Unavailable"
    return {0: "No gap observed", 1: "Gap observed"}.get(int(value), labels.get(str(int(value)), "Unavailable"))


def _render_metrics(row: pd.Series | None, labels: dict, *, has_specific_selection: bool = False) -> None:
    st.subheader("Is startup activity keeping pace?")
    if row is None:
        message = (
            "No observation matches this MSA-sector, descriptive year, and active gap/prediction filters. Historical values are shown separately when available."
            if has_specific_selection else
            "Select one MSA and one sector to see observation-level metrics. No values are averaged across different places or industries."
        )
        empty_state(message)
        return
    first = st.columns(4)
    metrics = (
        ("Observed startup activity", _rate(row["startup_rate"]), "Source-defined firm startup rate, in percent units."),
        ("Expected startup activity", _rate(row["expected_startup_rate"]), GLOSSARY["Expected rate"]),
        ("Above / below expectation", _alignment(row["alignment_residual"]), GLOSSARY["Alignment"]),
        ("Gap observed in past", _status(row["observed_historical_gap_status"], labels.get("gap_status", {})), "Historical A6 label; not a future prediction."),
    )
    for column, (label, value, help_text) in zip(first, metrics):
        with column:
            st.metric(label, value, help=help_text)
    second = st.columns(3)
    probability = row.get("logistic_probability")
    prediction_value = "N/A" if pd.isna(probability) else f"{float(probability):.1%}"
    prediction_help = "Frozen logistic score for this row's predictor year; actual target is retrospective, not a current forecast."
    split = row.get("development_or_holdout")
    if not pd.isna(split):
        prediction_help += f" Evaluation split: {split}."
    more = (
        ("Future gap risk (three years later)", prediction_value, prediction_help),
        ("Local employment growth", _growth(row["employment_growth"]), "Annual change in local industry employment; separate from startup activity."),
        ("Data coverage", COVERAGE_LABELS.get(str(row["coverage_status"]), "Not available"), "A5 historical coverage status; not prediction confidence. The source category remains available in the coverage section."),
    )
    for column, (label, value, help_text) in zip(second, more):
        with column:
            st.metric(label, value, help=help_text)
    st.caption(alignment_interpretation(row["alignment_residual"], row["observed_historical_gap_status"]))
    if pd.isna(row["expected_startup_rate"]):
        st.caption("Expected startup activity is unavailable for this MSA-sector-year; the dashboard does not extrapolate it.")
    if pd.isna(row["observed_historical_gap_status"]):
        st.caption("Historical A6 gap status is unavailable because this year is outside the fold-validation target records.")
    if pd.isna(probability):
        st.caption("No frozen A6 evaluation prediction is available for this MSA-sector predictor year.")
    suppression = row["has_suppression"]
    if not pd.isna(suppression) and bool(suppression):
        note = row.get("source_quality_notes")
        suffix = "" if pd.isna(note) or not str(note).strip() else f" Source note: {note}"
        st.caption("One or more source measures are flagged for suppression or incomplete support." + suffix)


def _render_availability(history: pd.DataFrame, selected_rows: pd.DataFrame, prediction_history: pd.DataFrame) -> None:
    st.subheader("Data availability")
    if history.empty:
        empty_state("No panel rows match this MSA-sector and active gap/prediction filters.")
        return
    years = sorted(history["year"].astype(int).unique())
    expected_years = int(history["expected_startup_rate"].notna().sum())
    gap_years = int(history["observed_historical_gap_status"].notna().sum())
    st.write(
        f"{len(years)} observed years ({years[0]}-{years[-1]}); "
        f"{len(selected_rows):,} row(s) match the selected descriptive year and filters; "
        f"expected startup is available in {expected_years} year(s); "
        f"A6 historical gap status is available in {gap_years} year(s); "
        f"{len(prediction_history):,} prediction record(s) in the selected evaluation split."
    )


def render() -> None:
    metadata = cached_metadata()
    options = cached_filter_options()
    labels = cached_labels()
    panel = cached_dataset("msa_industry_year")
    predictions = cached_dataset("model_predictions")
    coverage = cached_dataset("coverage")
    try:
        validate_explorer_inputs(panel, predictions, metadata["forecast_horizon_years"])
    except (ExplorerDataError, KeyError, ValueError) as exc:
        st.error("Explorer data could not be loaded or does not meet its A7.2 contract.")
        st.caption(str(exc))
        return

    prediction_years_by_split = {
        split: sorted(predictions.loc[predictions["development_or_holdout"] == split, "predictor_year"].astype(int).unique())
        for split in ("final_holdout", "development_oof")
    }
    initialize_filter_state(st.session_state, options, prediction_years_by_split)
    render_header("Explore Markets", PAGE_DESCRIPTIONS["Explore Markets"], metadata)
    with st.sidebar:
        selections = render_explorer_filters(options, prediction_years_by_split)

    msa = selections["msa"]
    sectors = selections["sectors"]
    selected_year = int(selections["descriptive_year"])
    gap_status = selections["observed_gap_status"]
    base_filters = {
        "msa": msa,
        "sectors": sectors,
        "gap_status": gap_status,
        "has_prediction": selections["has_prediction"],
        "predictions": predictions,
    }
    selected_rows = filter_explorer_data(panel, year=selected_year, **base_filters)
    joined_panel = attach_prediction_records(panel, predictions)
    joined_historical = filter_explorer_data(joined_panel, **base_filters)
    joined_selected = filter_explorer_data(joined_panel, year=selected_year, **base_filters)

    st.subheader("Your selected market")
    st.write(selection_summary(selected_rows, msa=msa, sectors=sectors, year=selected_year))
    st.caption("The descriptive year is the year of observed startup activity. Prediction records separately identify predictor year t and target year t+3.")
    st.caption("Explorer controls do not alter fixed Model Performance or Executive Overview results.")
    if selected_rows.empty:
        empty_state("No MSA-sector observations match this selection. Try another year, sector, or gap status.")

    has_specific_selection = msa is not None and len(sectors) == 1
    selected_row = None
    if has_specific_selection and len(joined_selected) == 1:
        selected_row = joined_selected.iloc[0]
    _render_metrics(selected_row, labels, has_specific_selection=has_specific_selection)

    if has_specific_selection:
        history = joined_historical.loc[
            (joined_historical["cbsa_code"].astype(str) == str(msa))
            & (joined_historical["sector_code"].astype(str) == str(sectors[0]))
        ].sort_values("year")
        split = st.session_state["selected_prediction_split"]
        prediction_history = filter_predictions(
            predictions, split=split, predictor_year=None, msa=msa, sectors=sectors
        )
        msa_name = str(history["msa_name"].iloc[0]) if not history.empty else "selected MSA"
        sector_name = str(history["sector_name"].iloc[0]) if not history.empty else "selected sector"
        st.subheader("How does startup activity compare with expectations?")
        if history["expected_startup_rate"].notna().any():
            render_plotly_chart(build_observed_expected_chart(history))
            usable = history.loc[history["startup_rate"].notna() & history["expected_startup_rate"].notna()]
            above = int((usable["startup_rate"] >= usable["expected_startup_rate"]).sum())
            st.caption(f"Observed startup activity was at or above its A6 expectation in {above} of {len(usable)} available comparison year(s) for {msa_name}, {sector_name}.")
        else:
            empty_state("Expected startup activity is unavailable for this MSA-sector history; only observed activity can be inspected.")
        if history["startup_rate"].notna().any():
            startup_values = history["startup_rate"].dropna()
            st.caption(f"Median observed startup rate: {float(startup_values.median()):.2f}% across {len(startup_values)} available year(s); the observed series remains visible in the comparison above.")
            if history["employment_growth"].notna().any():
                render_plotly_chart(build_employment_growth_chart(history))
                valid_growth = history["employment_growth"].dropna()
                positive = int((valid_growth > 0).sum())
                st.caption(f"Employment growth was positive in {positive} of {len(valid_growth)} available year(s); this descriptive association does not establish causation.")
            else:
                empty_state("Employment-growth values are unavailable for this selection.")
        else:
            empty_state("Observed startup-rate values are unavailable for the selected MSA-sector history.")

        st.subheader("When did activity fall below expectations?")
        if history["alignment_residual"].notna().any():
            render_plotly_chart(build_alignment_history_chart(history))
            residuals = history["alignment_residual"].dropna()
            above = int((residuals >= 0).sum())
            st.caption(f"Observed startup activity was at or above expectation in {above} of {len(residuals)} A6 validation year(s); negative alignment means below expectation.")
        else:
            empty_state("A6 alignment values are unavailable for this MSA-sector history; no residuals are reconstructed in the Explorer.")
        if history["observed_historical_gap_status"].notna().any():
            render_plotly_chart(build_gap_timeline(history))
            n_gaps = int((history["observed_historical_gap_status"] == 1).sum())
            n_status = int(history["observed_historical_gap_status"].notna().sum())
            st.caption(f"A6 gaps were observed in {n_gaps} of {n_status} available fold-validation target year(s). These historical labels are not future probabilities.")
        else:
            empty_state("No A6 fold-validation historical gap-status records are available for this MSA-sector selection.")

        st.subheader("What did the model estimate for later years?")
        if not prediction_history.empty:
            split_label = "Final temporal holdout" if split == "final_holdout" else "Development OOF"
            st.caption(f"{split_label}; logistic is the primary model. Each score uses predictor-year information to estimate a gap at t+3. Actual outcomes shown in hover detail are retrospective.")
            render_plotly_chart(build_prediction_history_chart(prediction_history))
        else:
            empty_state("No prediction records exist for this MSA-sector in the selected evaluation split.")
    else:
        st.subheader("Market trends")
        empty_state("Select exactly one MSA and one sector to view time-series charts. Broader selections remain available in the filtered observations and risk ranking below.")
        history = pd.DataFrame()
        prediction_history = pd.DataFrame()

    if has_specific_selection:
        _render_availability(history, joined_selected, prediction_history)
    else:
        st.subheader("Data availability")
        if selected_rows.empty:
            empty_state("No observations are available under the current filters.")
        else:
            st.write(
                f"{selected_rows['msa_name'].nunique():,} MSA(s), {selected_rows['sector_code'].nunique():,} sector(s), "
                f"{selected_rows['year'].nunique():,} selected year; expected startup available for "
                f"{int(selected_rows['expected_startup_rate'].notna().sum()):,} row(s), and finalized evaluation prediction available for "
                f"{int(joined_selected['logistic_probability'].notna().sum()):,} exact-key prediction record(s)."
            )

    st.subheader("How complete is the historical data?")
    if msa is not None:
        coverage_rows = coverage.loc[coverage["cbsa_code"].astype(str) == str(msa)]
        coverage_row = coverage_rows.iloc[0] if not coverage_rows.empty else None
    else:
        coverage_scope = filter_explorer_data(panel, msa=msa, sectors=sectors)
        scoped_msas = set(coverage_scope["cbsa_code"].astype(str).unique())
        coverage_rows = coverage.loc[coverage["cbsa_code"].astype(str).isin(scoped_msas)]
        coverage_row = None

    if msa is not None and coverage_row is not None:
        coverage_badge(str(coverage_row["coverage_status"]))
        st.caption(
            f"A5 descriptive coverage: {int(coverage_row['observation_count']):,} panel rows, "
            f"{int(coverage_row['sector_count']):,} sectors, {int(coverage_row['year_count']):,} years. "
            "This status is not a model-confidence rating."
        )
        if coverage_row["coverage_status"] == "thin":
            limitation_callout("Historical data coverage is limited for this metro. It remains in the Explorer, but comparisons call for more caution.", warning=True)
    elif not coverage_rows.empty:
        counts = coverage_rows.groupby("coverage_status")["cbsa_code"].nunique().to_dict()
        st.write(f"Among the selected places, {counts.get('comparison_eligible', 0):,} have good comparison coverage and {counts.get('thin', 0):,} have limited data coverage.")
        with st.expander("Technical details: A5 coverage categories"):
            st.write("The stored values remain `comparison_eligible` and `thin`. `comparison_eligible` requires at least 100 panel rows, 5 sectors, and 10 years; this is a descriptive completeness screen, not a model-confidence score.")
        if counts.get("thin", 0):
            limitation_callout("Places with limited data coverage remain in the Explorer and may have less complete historical context.", warning=True)
    else:
        empty_state("Coverage context is unavailable because the current selection has no panel observations.")

    st.subheader("Which cases had the highest future-gap scores?")
    st.caption("These are fixed historical evaluation scores, not live forecasts. Select one evaluation period at a time.")
    rank_controls = st.columns(3)
    split = st.session_state["selected_prediction_split"]
    with rank_controls[0]:
        split = st.selectbox(
            "Evaluation period",
            options=[value for value in ("final_holdout", "development_oof") if prediction_years_by_split.get(value)],
            format_func=lambda value: "Later evaluation period" if value == "final_holdout" else "Development test folds",
            key="selected_prediction_split",
            help="Technical labels: Final temporal holdout and Development OOF. Each score remains tied to its original study period.",
        )
    split_years = prediction_years_by_split.get(split, [])
    with rank_controls[1]:
        predictor_year = st.selectbox(
            "Prediction year (t)", options=split_years,
            key="selected_prediction_year", disabled=not split_years,
            help="The displayed target year is exactly three years after this predictor year.",
        )
    with rank_controls[2]:
        top_n = st.selectbox("Show top-ranked pairs", options=[10, 25, 50], key="selected_top_n")
    if split_years:
        horizon = int(metadata["forecast_horizon_years"])
        st.caption(f"Prediction timing: a score using information from {predictor_year} estimates a gap at {int(predictor_year) + horizon} (t+{horizon}).")
        ranking = build_top_risk_ranking(
            predictions, split=split, predictor_year=int(predictor_year), top_n=int(top_n),
            msa=msa, sectors=sectors, labels=labels,
        )
        if ranking.empty:
            empty_state("No finalized prediction is available for this MSA-sector, evaluation split, and predictor year.")
        else:
            st.dataframe(
                ranking, hide_index=True, width="stretch",
                column_config={
                    "Predicted gap probability (logistic)": st.column_config.NumberColumn(
                        format=".1%", help="Frozen A6 primary logistic score for the explicit target year; retrospective evaluation record."
                    ),
                },
            )
    else:
        ranking = pd.DataFrame()
        empty_state("No finalized predictions are available for the selected evaluation split.")

    st.subheader("Matching market and industry records")
    st.caption(f"Showing up to 100 of {len(joined_selected):,} matching rows; the CSV includes every match. Missing values remain blank.")
    display_columns = [
        "msa_name", "sector_name", "year", "startup_rate", "expected_startup_rate",
        "alignment_residual", "observed_historical_gap_status", "coverage_status",
        "logistic_probability", "development_or_holdout", "prediction_predictor_year", "target_year",
    ]
    display = joined_selected.loc[:, [col for col in display_columns if col in joined_selected.columns]].head(100).copy()
    if "observed_historical_gap_status" in display:
        display["observed_historical_gap_status"] = display["observed_historical_gap_status"].map(
            {0: "No gap observed", 1: "Gap observed"}
        ).fillna("Unavailable")
    display = display.rename(columns={
        "msa_name": "MSA", "sector_name": "Industry sector", "year": "Descriptive year",
        "startup_rate": "Observed startup rate (%)", "expected_startup_rate": "Expected startup rate (%)",
        "alignment_residual": "Alignment (percentage points)",
        "observed_historical_gap_status": "Historical observed A6 gap",
        "coverage_status": "A5 coverage status", "logistic_probability": "Logistic probability at t+3",
        "development_or_holdout": "Prediction evaluation split", "prediction_predictor_year": "Prediction year (t)",
        "target_year": "Prediction target year",
    })
    if display.empty:
        empty_state("There are no filtered rows to display or download.")
    else:
        st.dataframe(
            display, hide_index=True, width="stretch",
            column_config={"Logistic probability at t+3": st.column_config.NumberColumn(format=".1%")},
        )

    export = filtered_csv_frame(
        joined_selected, dashboard_version=str(metadata["dashboard_data_version"]),
        primary_model=str(metadata["primary_model"]),
    )
    filename = f"regional_entrepreneurship_explorer_{selected_year}_{date.today().isoformat()}.csv"
    csv_columns = st.columns([1, 2])
    with csv_columns[0]:
        st.download_button(
            "Download filtered CSV", data=dataframe_csv_bytes(export), file_name=filename,
            mime="text/csv", disabled=export.empty, key="explorer_csv_download",
        )
    with csv_columns[1]:
        st.caption("CSV contains only the selected A7.2 panel rows and exact-key attached prediction fields. Actual target gap is labeled retrospective; no raw or staging data is exported.")

    st.subheader("What to keep in mind")
    limitation_callout(
        "Startup, expected-rate, alignment, historical gap, and prediction fields have different time roles and may be unavailable for some years. "
        "Nulls are not zero and are not extrapolated. Startup activity is a narrower entrepreneurship measure; the A6 gap is model-relative, not causal, "
        "and the retrospective scores are not current forecasts."
    )
    render_footer(metadata)
