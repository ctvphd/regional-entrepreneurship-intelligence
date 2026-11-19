"""Generate A6.8D decision-calibration outputs from frozen holdout scores."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "rei-matplotlib-cache"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.models.decision_calibration import (
    evaluate_selection,
    evaluate_threshold,
    evaluate_top_fraction,
)


ROOT = Path(__file__).resolve().parents[3]
PREDICTIONS = ROOT / "reports" / "tables" / "a6_final_holdout_predictions.csv"
PERFORMANCE = ROOT / "reports" / "tables" / "a6_final_model_performance.csv"
SIZE_CUTPOINTS = ROOT / "reports" / "tables" / "a6_final_msa_size_cutpoints.csv"
SIZE_REFERENCE = ROOT / "reports" / "tables" / "a6_final_holdout_by_msa_size.csv"
PANEL = ROOT / "data" / "dashboard" / "dashboard_msa_industry_year.parquet"
DECISION_TABLE = ROOT / "reports" / "tables" / "a6_decision_rule_comparison.csv"
SECTOR_TABLE = ROOT / "reports" / "tables" / "a6_decision_sector_concentration.csv"
MSA_SIZE_TABLE = ROOT / "reports" / "tables" / "a6_decision_msa_size_concentration.csv"
MSA_TABLE = ROOT / "reports" / "tables" / "a6_decision_msa_concentration.csv"
FIGURE = ROOT / "reports" / "figures" / "a6_decision_precision_recall.png"
REPORT = ROOT / "reports" / "assignment6_decision_calibration.md"
FRACTIONS = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30)
RECOMMENDED_FRACTION = 0.10


def _load_frozen_inputs() -> tuple[pd.DataFrame, float, tuple[float, float]]:
    frame = pd.read_csv(PREDICTIONS, dtype={"cbsa_code": str, "sector_code": str})
    required = {
        "cbsa_code", "cbsa_name", "sector_code", "sector_title", "predictor_year",
        "target_year", "actual_gap", "predicted_probability_logistic",
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"Frozen holdout fields are missing: {missing}")
    keys = ["cbsa_code", "sector_code", "predictor_year", "target_year"]
    if frame.duplicated(keys).any() or len(frame) != 10_304:
        raise ValueError("Frozen holdout must contain 10,304 unique evaluation rows")
    if frame.cbsa_code.nunique() != 365 or not np.isclose(frame.actual_gap.mean(), 0.23253105590062112):
        raise ValueError("Frozen holdout MSA count or prevalence changed")

    performance = pd.read_csv(PERFORMANCE)
    logistic = performance[
        performance.dataset.eq("holdout") & performance.model.eq("logistic")
    ]
    if len(logistic) != 1:
        raise ValueError("Canonical holdout Logistic row is unavailable")
    logistic = logistic.iloc[0]
    if not np.isclose(logistic.AP, 0.40422477786600497):
        raise ValueError("Canonical holdout Logistic AP changed")
    threshold = float(logistic.classification_threshold)

    cutpoints = pd.read_csv(SIZE_CUTPOINTS).iloc[0]
    size_values = (
        float(cutpoints.msa_population_lower_tercile_cutpoint),
        float(cutpoints.msa_population_upper_tercile_cutpoint),
    )
    return frame, threshold, size_values


def _concentration_tables(
    ranked: pd.DataFrame,
    size_cutpoints: tuple[float, float],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    selected_n = int(ranked.selected.sum())
    sector = ranked.groupby(["sector_code", "sector_title"], as_index=False).agg(
        holdout_n=("actual_gap", "size"),
        holdout_gap_n=("actual_gap", "sum"),
        flagged_n=("selected", "sum"),
    )
    selected_sector_gaps = (
        ranked[ranked.selected]
        .groupby("sector_code").actual_gap.sum()
        .rename("flagged_gap_n")
    )
    sector = sector.merge(selected_sector_gaps, on="sector_code", how="left", validate="one_to_one")
    sector["flagged_gap_n"] = sector.flagged_gap_n.fillna(0).astype(int)
    sector["flagged_share"] = sector.flagged_n / selected_n
    sector["holdout_share"] = sector.holdout_n / len(ranked)
    sector["within_sector_flag_rate"] = sector.flagged_n / sector.holdout_n
    sector["representation_ratio"] = sector.flagged_share / sector.holdout_share
    sector["flagged_precision"] = sector.flagged_gap_n.div(sector.flagged_n).where(sector.flagged_n.gt(0))
    sector = sector.sort_values(["flagged_n", "sector_code"], ascending=[False, True])

    panel = pd.read_parquet(
        PANEL,
        columns=["cbsa_code", "sector_code", "year", "acs_population"],
    )
    panel["cbsa_code"] = panel.cbsa_code.astype(str)
    panel["sector_code"] = panel.sector_code.astype(str)
    enriched = ranked.merge(
        panel,
        left_on=["cbsa_code", "sector_code", "predictor_year"],
        right_on=["cbsa_code", "sector_code", "year"],
        how="left",
        validate="one_to_one",
    )
    if enriched.acs_population.isna().any():
        raise ValueError("Frozen holdout rows lack predictor-year population for size assignment")
    enriched["msa_size_group"] = pd.cut(
        enriched.acs_population,
        [-np.inf, *size_cutpoints, np.inf],
        labels=["small", "middle", "large"],
        include_lowest=True,
    )
    msa_size = enriched.groupby("msa_size_group", observed=True, as_index=False).agg(
        holdout_n=("actual_gap", "size"),
        holdout_gap_n=("actual_gap", "sum"),
        msa_n=("cbsa_code", "nunique"),
        flagged_n=("selected", "sum"),
    )
    selected_size_gaps = (
        enriched[enriched.selected]
        .groupby("msa_size_group", observed=True).actual_gap.sum()
        .rename("flagged_gap_n")
    )
    msa_size = msa_size.merge(selected_size_gaps, on="msa_size_group", how="left", validate="one_to_one")
    msa_size["flagged_share"] = msa_size.flagged_n / selected_n
    msa_size["holdout_share"] = msa_size.holdout_n / len(enriched)
    msa_size["within_group_flag_rate"] = msa_size.flagged_n / msa_size.holdout_n
    msa_size["representation_ratio"] = msa_size.flagged_share / msa_size.holdout_share
    msa_size["flagged_precision"] = msa_size.flagged_gap_n / msa_size.flagged_n

    reference = pd.read_csv(SIZE_REFERENCE)
    reference = reference[reference.model.eq("logistic")].set_index("msa_size_group")
    for row in msa_size.itertuples():
        expected = reference.loc[str(row.msa_size_group)]
        if int(expected.N) != row.holdout_n or not np.isclose(expected.prevalence, row.holdout_gap_n / row.holdout_n):
            raise ValueError("MSA-size assignment does not reconcile to the canonical subgroup artifact")

    msa = ranked.groupby(["cbsa_code", "cbsa_name"], as_index=False).agg(
        holdout_n=("actual_gap", "size"),
        holdout_gap_n=("actual_gap", "sum"),
        flagged_n=("selected", "sum"),
    )
    selected_msa_gaps = (
        ranked[ranked.selected].groupby("cbsa_code").actual_gap.sum().rename("flagged_gap_n")
    )
    msa = msa.merge(selected_msa_gaps, on="cbsa_code", how="left", validate="one_to_one")
    msa["flagged_gap_n"] = msa.flagged_gap_n.fillna(0).astype(int)
    msa["flagged_share"] = msa.flagged_n / selected_n
    msa["within_msa_flag_rate"] = msa.flagged_n / msa.holdout_n
    msa["flagged_precision"] = msa.flagged_gap_n.div(msa.flagged_n).where(msa.flagged_n.gt(0))
    msa = msa.sort_values(["flagged_n", "cbsa_code"], ascending=[False, True])
    return sector, msa_size, msa


def _write_figure(comparison: pd.DataFrame) -> None:
    top = comparison[comparison.rule.str.startswith("top_")].sort_values("selection_fraction")
    threshold = comparison[comparison.rule.eq("development_prevalence_threshold")].iloc[0]
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    x = top.selection_fraction * 100
    ax.plot(x, top.precision * 100, marker="o", color="#3F7CAC", label="Precision")
    ax.plot(x, top.recall * 100, marker="s", color="#B65C45", label="Recall")
    ax.scatter(
        [threshold.selection_fraction * 100],
        [threshold.precision * 100],
        marker="D", color="#3F7CAC", edgecolor="white", linewidth=0.8,
        label="Threshold precision",
    )
    ax.scatter(
        [threshold.selection_fraction * 100],
        [threshold.recall * 100],
        marker="D", color="#B65C45", edgecolor="white", linewidth=0.8,
        label="Threshold recall",
    )
    ax.axvline(10, color="#444444", linestyle="--", linewidth=1, alpha=0.7)
    ax.set(
        xlabel="Holdout cases selected (%)",
        ylabel="Metric (%)",
        title="Screening workload trades precision for gap coverage",
    )
    ax.set_xlim(0, 55)
    ax.set_ylim(0, 80)
    ax.grid(alpha=0.22)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=180)
    plt.close(fig)


def _write_report(
    comparison: pd.DataFrame,
    sector: pd.DataFrame,
    msa_size: pd.DataFrame,
    msa: pd.DataFrame,
    threshold: float,
    secondary: dict[str, float | int | str],
) -> None:
    recommended = comparison[comparison.rule.eq("top_10%")].iloc[0]
    threshold_row = comparison[comparison.rule.eq("development_prevalence_threshold")].iloc[0]
    selected_sectors = sector[sector.flagged_n.gt(0)]
    largest_sectors = ", ".join(
        f"{row.sector_code} ({row.flagged_share:.1%})" for row in sector.head(5).itertuples()
    )
    selected_msas = int((msa.flagged_n > 0).sum())
    top_ten_msa_share = float(msa.head(10).flagged_share.sum())
    size_lines = [
        f"- {row.msa_size_group}: {int(row.flagged_n):,} flags ({row.flagged_share:.1%} of flags versus {row.holdout_share:.1%} of holdout rows), {row.flagged_precision:.1%} precision."
        for row in msa_size.itertuples()
    ]
    decision_rows = []
    for row in comparison.itertuples():
        label = row.rule.replace("top_", "Top ").replace("%", "%").replace(
            "development_prevalence_threshold", "Development-prevalence threshold"
        )
        decision_rows.append(
            f"| {label} | {int(row.flagged_n):,} | {int(row.true_positive_n):,} | "
            f"{int(row.false_positive_n):,} | {row.precision:.1%} | {row.recall:.1%} | "
            f"{row.f1:.3f} | {row.lift:.2f}x | {row.false_positives_per_true_positive:.2f} |"
        )
    lines = [
        "# Assignment 6.8D: Decision Calibration and Business Rule",
        "",
        "## Decision Context",
        "",
        "A regional economic-development office cannot investigate every MSA-industry-year cell. The frozen Logistic score is used only to prioritize cases for deeper human review. It does not declare a market deficient, allocate funding, or recommend an intervention by itself.",
        "",
        "## Selection Rules Evaluated",
        "",
        "Top-fraction rules sort the frozen Logistic probabilities from highest to lowest and select the exact ceiling-sized workload. Probability ties at the boundary are resolved deterministically by MSA, sector, predictor year, and target year. This preserves an operationally exact case count and makes boundary handling reproducible.",
        "",
        "| Rule | Flagged | True gaps | False positives | Precision | Recall | F1 | Lift | FP per TP |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *decision_rows,
        "",
        "## Precision-Recall Tradeoff",
        "",
        f"The top 5% has the highest yield ({comparison.iloc[0].precision:.1%}) but captures only {comparison.iloc[0].recall:.1%} of realized gaps. Expanding through 30% steadily increases captured gaps to {comparison[comparison.rule.eq('top_30%')].iloc[0].recall:.1%}, while precision falls to {comparison[comparison.rule.eq('top_30%')].iloc[0].precision:.1%}. Each capacity point exchanges workload and yield for broader early-warning coverage; none is universally optimal without an office-specific staffing constraint.",
        "",
        "## False-Positive Burden",
        "",
        f"At the recommended top-10% rule, {int(recommended.false_positive_n):,} of {int(recommended.flagged_n):,} reviewed cases ({recommended.false_positive_share:.1%}) are not realized gaps, or {recommended.false_positives_per_true_positive:.2f} non-gap cases per realized gap. The primary burden falls on analysts, regional economic-development staff, partner institutions, and local business-support organizations through follow-up research and opportunity cost. Communities may also bear outreach burden. These cases are screening costs, not necessarily useless reviews.",
        "",
        "## False-Negative Cost",
        "",
        f"The top-10% queue leaves {int(recommended.false_negative_n):,} realized gaps outside the selected group ({1 - recommended.recall:.1%} of all gaps). A missed case may delay investigation of an emerging entrepreneurial shortfall, but this analysis does not establish that an intervention would have prevented or corrected it.",
        "",
        "## Development-Prevalence Threshold",
        "",
        f"The committed threshold is {threshold:.9f}. It flags {int(threshold_row.flagged_n):,} cases, including {int(threshold_row.true_positive_n):,} realized gaps and {int(threshold_row.false_positive_n):,} false positives. Precision is {threshold_row.precision:.1%}, recall {threshold_row.recall:.1%}, and lift {threshold_row.lift:.2f}x. The professor's approximate 5,173-case workload is confirmed. This rule captures many more gaps but asks staff to review half the holdout and produces {threshold_row.false_positives_per_true_positive:.2f} non-gap cases per realized gap.",
        "",
        "## Sector and MSA-Size Concentration",
        "",
        f"The global top decile contains {len(selected_sectors)} sectors. The largest shares are {largest_sectors}. Mining is overrepresented ({sector.loc[sector.sector_code.eq('21'), 'flagged_share'].iloc[0]:.1%} of flags versus {sector.loc[sector.sector_code.eq('21'), 'holdout_share'].iloc[0]:.1%} of rows), while Agriculture contributes {sector.loc[sector.sector_code.eq('11'), 'flagged_share'].iloc[0]:.1%} of flags. The queue is therefore concentrated, but not dominated only by the two highest-prevalence sectors.",
        "",
        *size_lines,
        "",
        f"Flags span {selected_msas} of 365 MSAs; the 10 MSAs with the largest flagged counts account for {top_ten_msa_share:.1%} of the queue. Concentration is diagnostic and is not itself evidence of unfairness or error.",
        "",
        "## Recommended Operating Rule",
        "",
        f"Use the top 10% of frozen Logistic scores as the primary priority-review queue: {int(recommended.flagged_n):,} cases, {int(recommended.true_positive_n):,} realized gaps, {int(recommended.false_positive_n):,} false positives, {recommended.precision:.1%} precision, {recommended.recall:.1%} recall, {recommended.lift:.2f}x lift, and {recommended.false_positives_per_true_positive:.2f} false positives per true positive. This is preferred to top 5% because it captures substantially more gaps, and to broader rules because it retains nearly double-baseline yield at a clear, capacity-based workload.",
        "",
        f"If capacity permits, the next 10% can form a secondary monitoring queue rather than an automatic action tier. That incremental block contains {int(secondary['flagged_n']):,} cases and {int(secondary['true_positive_n']):,} realized gaps ({float(secondary['precision']):.1%} yield), adding {float(secondary['recall']):.1%} of all realized gaps. This sensitivity does not change the primary global ranking.",
        "",
        "## Practical Interpretation",
        "",
        f"For every 100 top-decile cases reviewed, approximately {recommended.precision * 100:.0f} would be realized gaps and {(1 - recommended.precision) * 100:.0f} would not. The queue captures about {recommended.recall:.1%} of all realized gaps.",
        "",
        "## Presentation-Ready Sentence",
        "",
        f'“If an economic-development office reviewed only the 10% of MSA-industry cases ranked highest risk, approximately {recommended.precision:.0%} would be realized gaps, capturing {recommended.recall:.0%} of all gaps at {recommended.lift:.2f} times the overall prevalence.”',
        "",
        "## Limitations",
        "",
        "The operating rule is an ex post description of one three-year holdout, not a prospective impact evaluation. Precision may shift with future prevalence or data coverage. MSA-sector-year cells are not people, and complete-case coverage is weaker for some smaller metros. No monetary costs, intervention effects, causal claims, or probability recalibration are estimated. Human review should incorporate current local evidence before any action.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_decision_calibration() -> dict[str, object]:
    frame, threshold, size_cutpoints = _load_frozen_inputs()
    rows = []
    ranked_by_fraction: dict[float, pd.DataFrame] = {}
    for fraction in FRACTIONS:
        ranked, metrics = evaluate_top_fraction(frame, fraction)
        rows.append(metrics)
        ranked_by_fraction[fraction] = ranked
    rows.append(evaluate_threshold(frame, threshold))
    comparison = pd.DataFrame(rows)

    ranked = ranked_by_fraction[RECOMMENDED_FRACTION]
    sector, msa_size, msa = _concentration_tables(ranked, size_cutpoints)
    top_twenty = ranked_by_fraction[0.20]
    secondary_mask = top_twenty.selection_rank.gt(int(ranked.selected.sum())) & top_twenty.selected
    secondary = evaluate_selection(
        top_twenty,
        secondary_mask.to_numpy(dtype=bool),
        rule="next_10%_monitoring",
    )

    DECISION_TABLE.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(DECISION_TABLE, index=False, float_format="%.10g")
    sector.to_csv(SECTOR_TABLE, index=False, float_format="%.10g")
    msa_size.to_csv(MSA_SIZE_TABLE, index=False, float_format="%.10g")
    msa.to_csv(MSA_TABLE, index=False, float_format="%.10g")
    _write_figure(comparison)
    _write_report(comparison, sector, msa_size, msa, threshold, secondary)
    return {
        "rows": len(frame),
        "msas": int(frame.cbsa_code.nunique()),
        "prevalence": float(frame.actual_gap.mean()),
        "threshold": threshold,
        "decision_rules": comparison.to_dict(orient="records"),
        "secondary_monitoring": secondary,
        "selected_msas": int((msa.flagged_n > 0).sum()),
        "outputs": [
            str(DECISION_TABLE), str(SECTOR_TABLE), str(MSA_SIZE_TABLE), str(MSA_TABLE),
            str(FIGURE), str(REPORT),
        ],
    }


if __name__ == "__main__":
    print(json.dumps(run_decision_calibration(), indent=2))
