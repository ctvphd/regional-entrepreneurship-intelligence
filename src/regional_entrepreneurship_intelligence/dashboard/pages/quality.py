"""Data quality, coverage, and limitations for the frozen study artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from ..components import limitation_callout, render_footer, render_header
from ..constants import PAGE_DESCRIPTIONS
from ..data_access import cached_dataset, cached_metadata
from ..loader import ROOT
from ..visual_style import (
    PLOTLY_CONFIG, SUFFICIENT_SAMPLE, THIN_COVERAGE, INSUFFICIENT_SAMPLE,
    apply_dashboard_style,
)

REPORTS = ROOT / "reports" / "tables"


@st.cache_data(show_spinner=False)
def _read_report(name: str) -> pd.DataFrame:
    allowed = {"a6_sample_selection_audit.csv", "a6_gap_complete_case_selection.csv", "a6_geographic_generalization.csv"}
    if name not in allowed:
        raise ValueError(f"Unknown finalized quality report: {name}")
    return pd.read_csv(REPORTS / name)


def _render_coverage(coverage: pd.DataFrame, metadata: dict) -> None:
    comparison = coverage["comparison_eligible_flag"].fillna(False).astype(bool)
    model = coverage["model_eligible_flag"].fillna(False).astype(bool)
    year_span = metadata["study_period"]["descriptive"]
    cols = st.columns(4)
    cols[0].metric("Metropolitan areas", f"{len(coverage):,}")
    cols[1].metric("A5 comparison eligible", f"{int(comparison.sum()):,}", f"{comparison.mean():.1%} of covered MSAs")
    cols[2].metric("Thin A5 coverage", f"{int((~comparison).sum()):,}", "Below the descriptive coverage screen")
    cols[3].metric("MSAs with A6 OOF rows", f"{int(model.sum()):,}", "Observed participation, not reliability")

    st.caption(
        f"A7.2 coverage across {year_span[0]}–{year_span[1]}. The A5 comparison screen requires at least "
        "100 MSA-sector-year observations, 5 sectors, and 10 years. It is a descriptive completeness rule, "
        "not a model-quality score or causal inclusion criterion."
    )
    st.plotly_chart(
        apply_dashboard_style(px.histogram(coverage.assign(coverage_status=coverage.coverage_status.map({
                     "comparison_eligible": "Comparison eligible", "thin": "Thin coverage",
                 })), x="observation_count", nbins=24, color="coverage_status",
                     labels={"observation_count": "Observed MSA-sector-year rows", "coverage_status": "A5 coverage"},
                     title="Observed panel coverage by metropolitan area",
                     color_discrete_map={"Comparison eligible": SUFFICIENT_SAMPLE, "Thin coverage": THIN_COVERAGE})
        .update_layout(height=330, margin={"l": 35, "r": 20, "t": 60, "b": 45})),
        width="stretch", config=PLOTLY_CONFIG,
    )
    st.dataframe(
        coverage.sort_values(["comparison_eligible_flag", "observation_count"], ascending=[True, True]),
        hide_index=True, width="stretch", height=420,
        column_config={
            "cbsa_code": st.column_config.TextColumn("CBSA code"),
            "msa_name": st.column_config.TextColumn("Metropolitan area"),
            "observation_count": st.column_config.NumberColumn("Panel rows", format="%,d"),
            "sector_count": st.column_config.NumberColumn("Sectors", format="%d"),
            "year_count": st.column_config.NumberColumn("Years", format="%d"),
            "first_year": st.column_config.NumberColumn("First year", format="%d"),
            "last_year": st.column_config.NumberColumn("Last year", format="%d"),
            "comparison_eligible_flag": st.column_config.CheckboxColumn("A5 eligible"),
            "model_eligible_flag": st.column_config.CheckboxColumn("A6 OOF present"),
            "a6_oof_row_count": st.column_config.NumberColumn("A6 OOF rows", format="%,d"),
            "coverage_status": st.column_config.TextColumn("Coverage status"),
            "coverage_note": st.column_config.TextColumn("Coverage note"),
        },
    )
    st.caption("Use the table headers to sort; its built-in search and download controls retain all A7.2 coverage fields.")


def _render_selection() -> None:
    selection = _read_report("a6_sample_selection_audit.csv")
    complete = _read_report("a6_gap_complete_case_selection.csv")
    key = complete.loc[(complete["group_type"] == "all") & (complete["split_role"] == "validation")]
    st.write(
        "A6 uses complete cases; this changes who is represented. In the pooled development sample, "
        "the finalized audit reports 13,633 included and 720 excluded pairs for population, while "
        "included and excluded average populations were about 807k and 406k. These are audit values, "
        "not reconstructed from the dashboard panel."
    )
    if not key.empty:
        st.dataframe(
            key[["fold", "eligible_exact_pairs", "complete_case_pairs", "excluded_pairs", "inclusion_rate"]],
            hide_index=True, width="stretch",
            column_config={"inclusion_rate": st.column_config.NumberColumn("Complete-case share", format="%.1%%")},
        )
    st.caption("The rows above are fold-level validation counts from the frozen A6 complete-case audit. They are not added together here because folds can represent overlapping expanding training sets.")
    st.dataframe(
        selection.rename(columns={
            "variable": "Audited measure", "included_n": "Included N", "excluded_n": "Excluded N",
            "included_mean_or_share": "Included mean / share", "excluded_mean_or_share": "Excluded mean / share",
            "standardized_difference": "Standardized difference",
        }), hide_index=True, width="stretch",
        column_config={
            "Included mean / share": st.column_config.NumberColumn(format="%.3f"),
            "Excluded mean / share": st.column_config.NumberColumn(format="%.3f"),
            "Standardized difference": st.column_config.NumberColumn(format="%.3f"),
        },
    )
    st.caption("Population is persons, household income is nominal dollars, unemployment is in the source's percent/rate units, and growth/sector shares are stored as fractions. Startup rate retains the source-defined rate unit. Sector-share rows have no standardized difference in the source audit; blank means not reported, not zero.")


def _render_sector_coverage(sectors: pd.DataFrame) -> None:
    holdout = sectors.loc[(sectors["dataset_split"] == "final_holdout") & (sectors["model"] == "logistic")].copy()
    holdout["Sample sufficiency"] = holdout["sufficient_sample_flag"].map({True: "Sufficient", False: "Suppressed by A6 rule"})
    st.plotly_chart(
        apply_dashboard_style(px.bar(holdout.sort_values("sample_n"), x="sample_n", y="sector_name", orientation="h", color="Sample sufficiency",
               custom_data=["positive_n", "prevalence"], labels={"sample_n": "Final-holdout pairs", "sector_name": "Sector"},
               title="Final temporal holdout support by sector",
               color_discrete_map={"Sufficient": SUFFICIENT_SAMPLE, "Suppressed by A6 rule": INSUFFICIENT_SAMPLE})
        .update_traces(hovertemplate="%{y}<br>Pairs: %{x:,}<br>Positive events: %{customdata[0]:,}<br>Prevalence: %{customdata[1]:.1%}<extra></extra>")
        .update_layout(height=620, margin={"l": 250, "r": 25, "t": 65, "b": 50})),
        width="stretch", config=PLOTLY_CONFIG,
    )
    st.dataframe(
        holdout[["sector_code", "sector_name", "sample_n", "positive_n", "prevalence", "sufficient_sample_flag", "AP", "ROC_AUC"]]
        .sort_values("sector_name"), hide_index=True, width="stretch",
        column_config={
            "sample_n": st.column_config.NumberColumn("Pairs", format="%,d"),
            "positive_n": st.column_config.NumberColumn("Positive events", format="%,d"),
            "prevalence": st.column_config.NumberColumn("Gap prevalence", format="%.1%%"),
            "sufficient_sample_flag": st.column_config.CheckboxColumn("A6 metric eligible"),
            "AP": st.column_config.NumberColumn("AP", format="%.3f"),
            "ROC_AUC": st.column_config.NumberColumn("ROC-AUC", format="%.3f"),
        },
    )
    st.caption("A6 suppresses sector AP/ROC-AUC if there are fewer than 30 positive events or no negative class. Blank metric values are intentionally unavailable, never zero.")


def _render_generalization(msa_size: pd.DataFrame) -> None:
    st.subheader("MSA-size variation")
    st.caption("Training-defined population thirds; fixed final-holdout values. Descriptive differences do not establish equal performance or explain why groups differ.")
    st.dataframe(
        msa_size.loc[msa_size["dataset_split"] == "final_holdout"].rename(columns={
            "msa_size_group": "MSA size group", "msa_count": "Metropolitan areas",
            "sample_n": "Prediction pairs", "prevalence": "Gap prevalence",
            "model": "Model", "dataset_split": "Evaluation population",
            "ROC_AUC": "ROC-AUC", "Brier": "Brier score", "top10_lift": "Top-decile lift",
        }).sort_values(["MSA size group", "Model"]),
        hide_index=True, width="stretch",
        column_config={
            "Prediction pairs": st.column_config.NumberColumn(format="%,d"),
            "Metropolitan areas": st.column_config.NumberColumn(format="%,d"),
            "Gap prevalence": st.column_config.NumberColumn(format="%.1%%"),
            "AP": st.column_config.NumberColumn("AP", format="%.3f"),
            "ROC-AUC": st.column_config.NumberColumn(format="%.3f"),
            "Brier score": st.column_config.NumberColumn(format="%.3f"),
            "Top-decile lift": st.column_config.NumberColumn(format="%.2f"),
        },
    )

    geographic = _read_report("a6_geographic_generalization.csv")
    rows = geographic.loc[(geographic["split"] == "pooled_geographic_oof") & (geographic["model"] == "logistic")]
    if not rows.empty:
        row = rows.iloc[0]
        st.subheader("Unseen-MSA test")
        st.write(
            f"In A6's held-out-geography development test, logistic AP was {row['pr_auc']:.3f} and ROC-AUC "
            f"{row['roc_auc']:.3f} across {int(row['n']):,} pairs from {int(row['msa_n']):,} MSAs. "
            "This is separate from the ordinary temporal holdout and is not external validation; it is a fixed, "
            "development-only split reported in the A6 geographic-generalization artifact."
        )


def render() -> None:
    metadata = cached_metadata()
    coverage = cached_dataset("coverage")
    sectors = cached_dataset("model_by_sector")
    msa_size = cached_dataset("model_by_msa_size")
    sources = cached_dataset("sources")
    render_header("Data Quality & Limitations", PAGE_DESCRIPTIONS["Data Quality & Limitations"], metadata)

    _render_coverage(coverage, metadata)
    st.subheader("Sector support and metric suppression")
    _render_sector_coverage(sectors)

    st.subheader("Complete-case selection")
    _render_selection()

    _render_generalization(msa_size)

    st.subheader("Missingness, nulls, and suppression")
    st.write(
        "Source missingness, source suppression, and incomplete geographic coverage are distinct conditions. "
        "Unavailable numeric values remain null; the dashboard does not replace them with zero or impute them. "
        "A blank metric can mean the source did not publish it or A6's stated sufficiency rule suppressed it. "
        "The A7.2 field dictionary and lineage audit identify field-level meanings and source flags."
    )

    st.subheader("What the model-relative gap does and does not mean")
    st.write(
        "Startup rate is one narrow measure of entrepreneurship, not a complete account of business formation, "
        "innovation, or welfare. The gap is relative to a fitted expected-startup benchmark and its frozen "
        "fold-local threshold; it is not an observed absolute deficit, causal effect, or policy treatment effect. "
        "A model score is retrospective ranking evidence for eligible MSA-sector pairs, not a current forecast "
        "or a recommendation about any community."
    )
    limitation_callout("Coverage and subgroup tables describe data support and evaluation samples; they are not quality grades, causal evidence, or guarantees for an individual MSA.", warning=True)

    st.subheader("Sources used")
    st.dataframe(sources, hide_index=True, width="stretch", height=300)
    st.caption("Source names, agencies, dataset roles, years, geography, industry level, and notes are copied from the finalized A7.2 source catalog.")

    with st.expander("Lineage and reproducibility"):
        st.markdown(
            "- Dashboard values come from validated A7.2 Parquet/JSON artifacts; this page does not read SQLite or raw source files.\n"
            "- Complete-case and unseen-MSA summaries come from finalized A6 reporting tables; no models or targets are reconstructed.\n"
            "- Field-level lineage: `reports/tables/a7_dashboard_lineage_audit.csv` and `docs/ASSIGNMENT7_SOURCE_LINEAGE.md`.\n"
            "- Coverage rule: `docs/ASSIGNMENT7_COVERAGE_POLICY.md`; null and time-role contracts: `docs/ASSIGNMENT7_DATA_CONTRACTS.md`."
        )
    render_footer(metadata)
