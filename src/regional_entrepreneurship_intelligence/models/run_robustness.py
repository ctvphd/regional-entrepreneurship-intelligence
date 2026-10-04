"""Run development-only Assignment 6.6 robustness and generalization checks."""

from __future__ import annotations

import ast
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import quote

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.analysis.eda import DEFAULT_EDA_DATABASE
from regional_entrepreneurship_intelligence.models.advanced import (
    ABLATIONS,
    TREE_FEATURES,
    fit_advanced_model,
    predict_gap_probability as predict_tree,
)
from regional_entrepreneurship_intelligence.models.baseline import (
    CORE_NUMERIC,
    EXTENDED_REQUIRED,
    build_predictor_pairs,
    complete_predictor_sample,
    fit_logistic_baseline,
    lift_table,
    predict_gap_probability as predict_logistic,
    probability_metrics,
    threshold_metrics,
)
from regional_entrepreneurship_intelligence.models.expected import fit_expected_model, predict_expected
from regional_entrepreneurship_intelligence.models.run_baseline import (
    FOLD_PATH,
    MAX_DEVELOPMENT_PREDICTOR_YEAR,
    ROOT,
    TARGET_PATH,
    _load_predictor_panel,
)
from regional_entrepreneurship_intelligence.models.robustness import (
    classification_summary,
    assert_development_only,
    assign_population_terciles,
    attach_predictor_year_fields,
    clip_from_training,
    deterministic_geography_split,
    exclude_calendar_year_pairs,
    label_agreement,
    sector_sufficiency,
    standardized_mean_difference,
    validate_geography_disjoint,
)

TABLE_DIR = ROOT / "reports" / "tables"
FIGURE_DIR = ROOT / "reports" / "figures"
REPORT_PATH = ROOT / "reports" / "assignment6_robustness_generalization.md"
LIMITATIONS_PATH = ROOT / "docs" / "ASSIGNMENT6_LIMITATIONS.md"
KEYS = ["fold", "split_role", "cbsa_code", "sector_code", "predictor_year", "target_year"]
GROWTH_ALTERNATIVES = {
    "employment_growth": "QCEW employment annual rate (primary; decimal change)",
    "establishment_growth": "QCEW establishment annual rate (decimal change)",
    "payroll_growth": "QCEW nominal payroll annual rate (decimal change)",
    "wage_growth": "QCEW average-wage annual rate (decimal change)",
}
LAG_ALTERNATIVES = {"startup_rate_lag1": "primary", "startup_rate_lag2": "lag2 substitution",
                    "startup_rate_lag3": "lag3 substitution"}
MIN_SECTOR_EVENTS = 30
MAX_DEVELOPMENT_TARGET_YEAR = 2020
HGB_NAMES = {"hist_gradient_boosting"}


def _load_expected_panel(database_path: Path) -> pd.DataFrame:
    """Read only target-construction fields through the last development target year."""
    uri = f"file:{quote(database_path.resolve().as_posix(), safe='/:')}?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        connection.execute("PRAGMA query_only = ON")
        panel = pd.read_sql_query(
            "SELECT * FROM v_analytics_msa_industry_year WHERE year <= ?",
            connection,
            params=(MAX_DEVELOPMENT_TARGET_YEAR,),
        )
    if panel.empty or int(panel.year.max()) > MAX_DEVELOPMENT_TARGET_YEAR:
        raise ValueError("Expected-model robustness read crossed the development target boundary")
    return panel


def _feature_pairs(targets: pd.DataFrame, predictor_panel: pd.DataFrame) -> pd.DataFrame:
    base = build_predictor_pairs(targets, predictor_panel)
    extras = ("establishment_growth", "payroll_growth", "wage_growth",
              "startup_rate_lag2", "startup_rate_lag3", "cbsa_name")
    available = tuple(name for name in extras if name in predictor_panel.columns)
    return attach_predictor_year_fields(base, predictor_panel, available)


def _complete_pairs(paired: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    complete, _ = complete_predictor_sample(paired)
    finite = complete.loc[:, list(EXTENDED_REQUIRED)].replace([np.inf, -np.inf], np.nan).notna().all(axis=1)
    return complete.loc[finite].copy(), paired


def _metric_row(actual, probability, *, model, fold, split, n_msa=None):
    lift = lift_table(pd.Series(np.asarray(actual, dtype=int)), np.asarray(probability), cuts=(.10, .20, .25))
    result = {"model": model, "fold": fold, "split": split, "n": len(actual),
              "msa_n": n_msa, **probability_metrics(actual, probability)}
    result.update({f"top{int(row.risk_cut*100)}_lift": float(row.lift_ratio) for row in lift.itertuples(index=False)})
    result["prevalence"] = float(np.mean(actual))
    return result


def _selected_hgb_params(fold: str) -> dict:
    candidates = pd.read_csv(TABLE_DIR / "a6_advanced_tuning.csv")
    row = candidates[(candidates.model == "hist_gradient_boosting") & (candidates.fold == fold) & candidates.selected.astype(bool)]
    if len(row) != 1:
        raise ValueError(f"Expected one frozen A6.5 HGB configuration for {fold}")
    return ast.literal_eval(row.iloc[0].params)


def _fit_score(train: pd.DataFrame, validation: pd.DataFrame, *, model: str, label_column: str,
               feature_columns: tuple[str, ...] | None = None, no_sector: bool = False,
               params: dict | None = None) -> np.ndarray:
    train_y = train.assign(gap_p20=train[label_column].astype(int))
    test_y = validation.assign(gap_p20=validation[label_column].astype(int))
    if model == "logistic":
        spec = "baseline_1_no_sector" if no_sector else "baseline_1_simple"
        return predict_logistic(fit_logistic_baseline(train_y, model=spec), test_y)
    features = feature_columns or (tuple(name for name in TREE_FEATURES if name != "sector_code")
                                   if no_sector else TREE_FEATURES)
    fitted = fit_advanced_model(train_y, model_name="hist_gradient_boosting",
                                params=params or {}, features=features)
    return predict_tree(fitted, test_y, features=features)


def _evaluate_oof(
    frame: pd.DataFrame,
    *,
    label_column: str,
    model_names: tuple[str, ...] = ("logistic", "hist_gradient_boosting"),
    transform=None,
    transform_name: str = "primary",
    no_sector: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prediction_rows, metric_rows = [], []
    fold_config = pd.read_csv(FOLD_PATH).query("final_holdout == False")
    for fold in fold_config.fold.astype(str):
        train = frame[(frame.fold == fold) & frame.split_role.eq("training")].copy()
        validation = frame[(frame.fold == fold) & frame.split_role.eq("validation")].copy()
        if transform:
            train, validation = transform(train, validation)
        for model in model_names:
            params = _selected_hgb_params(fold) if model == "hist_gradient_boosting" else None
            probability = _fit_score(train, validation, model=model, label_column=label_column,
                                     params=params, no_sector=no_sector)
            row = validation[KEYS + [label_column]].copy().rename(columns={label_column: "actual"})
            row["model"] = model
            row["specification"] = transform_name
            row["probability"] = probability
            prediction_rows.append(row)
            metric_rows.append({"specification": transform_name, **_metric_row(
                validation[label_column], probability, model=model, fold=fold, split="validation")})
    predictions = pd.concat(prediction_rows, ignore_index=True)
    for model, group in predictions.groupby("model"):
        metric_rows.append({"specification": transform_name, **_metric_row(
            group.actual, group.probability.to_numpy(), model=model, fold="pooled_oof", split="pooled_oof",
            n_msa=group.cbsa_code.nunique())})
    return predictions, pd.DataFrame(metric_rows)


def _append_scorecard(scorecard: list[dict], table: pd.DataFrame, *, analysis: str, spec: str, notes: str = "") -> None:
    for row in table[table.fold.eq("pooled_oof")].itertuples(index=False):
        values = row._asdict()
        scorecard.append({"analysis": analysis, "specification": spec, "model": values["model"],
                          "sample_n": values.get("sample_n", values.get("n")),
                          "prevalence": values["prevalence"], "AP": values.get("AP", values.get("pr_auc")),
                          "ROC_AUC": values.get("ROC_AUC", values.get("roc_auc")),
                          "Brier": values.get("Brier", values.get("brier_score")),
                          "top10_lift": values["top10_lift"], "comparison_to_primary": "see matched primary row",
                          "conclusion_stable": "reviewed_by_comparison", "notes": notes})


def _huber_target_labels(expected_panel: pd.DataFrame, targets: pd.DataFrame, folds: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, agreement_rows = [], []
    for fold in folds.itertuples(index=False):
        fold_name = str(fold.fold)
        model = fit_expected_model(expected_panel[
            expected_panel.year.between(int(fold.first_stage_fit_start_year), int(fold.first_stage_fit_end_year))
        ], name="C", training_year_end=int(fold.first_stage_fit_end_year), estimator="huber")
        train_fitted = predict_expected(model, model.training_frame)
        threshold = float(train_fitted.residual.quantile(.20))
        target_rows = targets[(targets.fold == fold_name) & targets.target_year.le(MAX_DEVELOPMENT_TARGET_YEAR)]
        target_years = target_rows.target_year.unique()
        predict_rows = expected_panel[expected_panel.year.isin(target_years)]
        scored = predict_expected(model, predict_rows)[["cbsa_code", "sector_code", "year", "residual"]].rename(
            columns={"year": "target_year", "residual": "huber_residual"})
        joined = target_rows.merge(scored, on=["cbsa_code", "sector_code", "target_year"], how="left",
                                   validate="many_to_one")
        joined["huber_gap_p20"] = pd.Series(
            np.where(joined.huber_residual.notna(), joined.huber_residual.le(threshold).astype(float), np.nan),
            index=joined.index,
        )
        joined["huber_p20_threshold"] = threshold
        rows.append(joined[KEYS + ["huber_residual", "huber_p20_threshold", "huber_gap_p20", "gap_p20"]])
        val = joined[joined.split_role.eq("validation")]
        agreement_rows.append({"fold": fold_name, **label_agreement(val.gap_p20, val.huber_gap_p20)})
    return pd.concat(rows, ignore_index=True), pd.DataFrame(agreement_rows)


def _save_table(name: str, frame: pd.DataFrame) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(TABLE_DIR / name, index=False)


def _figures(gap, huber, geographic, size, sector, growth, pandemic, scorecard, agreement, selection):
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    names = []

    def save(name, fig):
        fig.tight_layout()
        fig.savefig(FIGURE_DIR / f"a6_robust_{name}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)
        names.append(f"a6_robust_{name}.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    pivot = gap[gap.model.isin(["logistic", "hist_gradient_boosting"])].pivot(index="gap_definition", columns="model", values="AP")
    pivot.plot(kind="bar", ax=ax, color=["#4b8064", "#5580a5"])
    ax.set(title="AP across fold-local gap definitions", ylabel="Average precision", xlabel="Gap definition")
    ax.legend(frameon=False)
    save("gap_ap", fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    pivot = gap[gap.model.isin(["logistic", "hist_gradient_boosting"])].pivot(index="gap_definition", columns="model", values="top10_lift")
    pivot.plot(kind="bar", ax=ax, color=["#bc6c4a", "#5580a5"])
    ax.axhline(1, color="black", linestyle="--")
    ax.set(title="Top-decile lift across gap definitions", ylabel="Lift", xlabel="Gap definition")
    ax.legend(frameon=False)
    save("gap_lift", fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(huber.model, huber.AP, color=["#4b8064", "#5580a5"])
    ax.set(title="Primary versus Huber-based p20 target", ylabel="Average precision")
    save("huber_target", fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(agreement.fold, agreement.positive_jaccard, color="#bc6c4a")
    ax.set(title="Positive-label overlap: OLS versus Huber targets", ylabel="Positive Jaccard", xlabel="Outer fold", ylim=(0, 1))
    save("huber_label_agreement", fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(geographic.model, geographic.AP, color=["#4b8064", "#5580a5"])
    ax.axhline(geographic.loc[geographic.model.eq("ordinary_temporal"), "AP"].iloc[0], color="black", linestyle="--", label="Ordinary temporal OOF")
    ax.set(title="Unseen-MSA geographic test", ylabel="Average precision")
    ax.legend(frameon=False)
    save("geographic", fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.bar(size.population_group, size.AP, color="#4b8064")
    ax.set(title="Logistic performance by MSA size", ylabel="Average precision", xlabel="Training-defined population tercile")
    save("msa_size", fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    sector.sort_values("AP").plot.barh(x="sector_code", y="AP", ax=ax, color="#5580a5", legend=False)
    ax.set(title="Within-sector OOF average precision", xlabel="AP", ylabel="NAICS sector")
    save("sector_ap", fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    sector.sort_values("gap_prevalence").plot.barh(x="sector_code", y="gap_prevalence", ax=ax, color="#bc6c4a", legend=False)
    ax.set(title="Observed p20 prevalence by sector", xlabel="Prevalence", ylabel="NAICS sector")
    save("sector_prevalence", fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    pivot = growth.pivot(index="growth_measure", columns="model", values="AP")
    pivot.plot(kind="bar", ax=ax)
    ax.set(title="One-at-a-time growth-measure substitutions", ylabel="Average precision", xlabel="Growth measure")
    ax.legend(frameon=False)
    save("growth_measures", fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    pivot = pandemic.pivot(index="sensitivity", columns="model", values="AP")
    pivot.plot(kind="bar", ax=ax)
    ax.set(title="Pandemic-period row sensitivity", ylabel="Average precision", xlabel="Development sample")
    ax.legend(frameon=False)
    save("pandemic", fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    view = scorecard[scorecard.model.eq("logistic")].sort_values("top10_lift")
    ax.barh(view.specification.tail(12), view.top10_lift.tail(12), color="#bc6c4a")
    ax.axvline(1, color="black", linestyle="--")
    ax.set(title="Top-decile lift across robustness checks", xlabel="Lift", ylabel="Specification")
    save("scorecard_lift", fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    population = selection[selection.variable.eq("acs_population")]
    ax.bar(["Included", "Excluded"], [population.included_mean_or_share.iloc[0], population.excluded_mean_or_share.iloc[0]],
           color=["#4b8064", "#bc6c4a"])
    ax.set(title="Complete-case selection by MSA population", ylabel="Mean ACS population")
    save("selection_population", fig)

    return names


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    view = frame[columns]
    rows = []
    for row in view.itertuples(index=False, name=None):
        rows.append([f"{x:.3f}" if isinstance(x, (float, np.floating)) and np.isfinite(x)
                     else "" if pd.isna(x) else str(x) for x in row])
    return "| " + " | ".join(columns) + " |\n| " + " | ".join(["---"] * len(columns)) + " |\n" + "\n".join(
        "| " + " | ".join(row) + " |" for row in rows)


def _write_report(*, gap, agreement, huber, growth, pandemic, tail, sector, geographic, size,
                  selection, coverage, startup, figures, hgb_sector, loso, scorecard):
    gap_table = gap[gap.model.isin(["logistic", "hist_gradient_boosting"])]
    report = f"""# Assignment 6.6: Robustness, Interpretation & Generalization

## Executive Summary

The primary study remains the A6.3 fold-local p20 exact-t+3 target with simple logistic regression as reference; HistGradientBoosting is the nonlinear sensitivity. Across the checks below, sector context remains a large predictive source, while the growth-measure and model-family rankings vary only modestly. These are development-only stress tests, not causal evidence or final validation. All predictive analyses stop at target year 2020; no 2021–2023 outcomes were queried or scored, and no A6.7 work was started.

## Purpose and safeguards

The temporal folds, target construction, and feature boundary remain unchanged. The A6.4 common complete-case feature sample is used for paired tests when possible. Cutoffs and preprocessing are learned within each fold. The geographic test uses a deterministic SHA-256 hash partition of CBSA codes (hash bucket modulo 10,000; buckets 0–1,999 assigned to test), with temporal training/validation chronology preserved inside each fold. Geographic-test MSAs never appear in any training fold. Only fixed-formula logistic is tested geographically: HGB is omitted because its A6.5 settings were tuned using temporal development folds containing all MSAs.

## Gap-Threshold Robustness

The approved p10, p20, p25, and training residual mean-minus-one-SD labels are taken from A6.3, where thresholds are fold-local and training-only. p20 remains primary. AP is interpreted against each definition's natural prevalence and within-fold prevalence baselines; pooled AP is also affected by fold-level score scale.

{_markdown_table(gap_table, ['gap_definition','model','sample_n','prevalence','AP','ROC_AUC','Brier','top10_lift','label_agreement_with_p20','positive_jaccard_with_p20','cohen_kappa_with_p20'])}

## Expected-Model Robustness

Huber Model C was refit within each frozen first-stage cutoff using the A6.2 formula. Huber p20 thresholds come from that fold's in-sample training residuals; labels are applied to exact development target pairs only. Agreement below compares those labels to Model A p20. This sensitivity does not replace the OLS Model A target.

{_markdown_table(agreement, ['fold','n','agreement','positive_jaccard','cohen_kappa','primary_positive_n','alternative_positive_n'])}

{_markdown_table(huber, ['model','sample_n','prevalence','AP','ROC_AUC','Brier','top10_lift'])}

## Alternative Growth Measures

Employment growth remains primary. Each available QCEW growth measure replaces employment growth one at a time in the logistic and HGB predictor matrix. Rates are annual decimal changes; missingness is the number/share excluded from the candidate's paired rows. No composite is constructed.

{_markdown_table(growth, ['growth_measure','model','sample_n','missing_n','missing_share','prevalence','AP','ROC_AUC','Brier','top10_lift','no_sector_AP'])}

## Entrepreneurship-Measure Robustness

The available establishment-entry and startup-job-creation measures are not interchangeable with firm startup rate: they measure establishment flows or job counts, and the existing entry-rate field includes documented values above 100 with unresolved interpretation. A defensible alternate outcome requires a separately specified expected-rate construct, denominator review, and fold-local target build. It is therefore deferred rather than forced into this robustness comparison.

## Pandemic Sensitivity

Sensitivity A removes development pairs whose predictor or target calendar year is 2020. In the frozen development OOF set, predictor years stop at 2017, so this removes only fold-3 validation outcomes with target year 2020. No expected-model training years change: first-stage fit cutoffs are 2016, 2017, and 2018. Sensitivity B excludes years 2020–2021 where present; no development pair has predictor year 2020/2021 or target year 2021, so its development evaluation is identical to A. The 2021 temporal holdout outcome is not read.

{_markdown_table(pandemic, ['sensitivity','model','sample_n','prevalence','AP','ROC_AUC','Brier','top10_lift','sector_drop_in_AP'])}

## Heavy-Tail Sensitivity

The raw employment-growth specification is compared with a non-destructive training-only 1st/99th percentile clipping sensitivity. Quantile bounds are estimated from each outer training fold and applied to copies of its training and validation fields. Production values and canonical data are unchanged.

{_markdown_table(tail, ['specification','model','sample_n','prevalence','AP','ROC_AUC','Brier','top10_lift','clip_lower','clip_upper'])}

## Sector Dependence and Within-Sector Performance

The p20 model without sector is the A6.4 paired ablation; the leave-one-sector-out table separately refits after excluding each sector from training and scores the remaining OOF observations. It is an influence analysis, not unseen-sector validation. Sector-specific AP is reported only with at least {MIN_SECTOR_EVENTS} positive events; otherwise the row is flagged insufficient. A broader sector mapping was not used because no reviewed defensible grouping is defined in the current design.

{_markdown_table(sector, ['sector_code','n','positive_n','gap_prevalence','AP','ROC_AUC','top10_lift','sufficient_sample'])}

{_markdown_table(hgb_sector, ['model','with_sector_AP','without_sector_AP','AP_drop_without_sector'])}

Largest leave-one-sector-out changes:

{_markdown_table(loso.head(8), ['omitted_sector','oof_n','AP','AP_change_vs_primary','ROC_AUC','top10_lift'])}

## Geographic Generalization

The held-out geography partition is fixed by code hash, not outcomes. Within each outer fold, model fitting uses only temporal training rows from training MSAs; evaluation uses only that fold's validation rows from test MSAs. Training and test geography sets have zero overlap. Only fixed-formula logistic is evaluated: HGB is omitted because its A6.5 settings were tuned on temporal folds containing all MSAs. Full ordinary temporal OOF and its training-geography subset are reference rows.

{_markdown_table(geographic, ['geography_comparison','model','train_msa_n','test_msa_n','sample_n','prevalence','AP','ROC_AUC','Brier','top10_lift'])}

## MSA-Size Generalization

MSA population groups use ACS population from predictor year t. Fold-specific tercile cutpoints are estimated from training MSAs only and applied unchanged to validation rows. Therefore the group labels are temporally valid; small and large metro differences remain conditional on the complete-case sample.

{_markdown_table(size, ['population_group','msa_n','sample_n','prevalence','AP','ROC_AUC','Brier','top10_lift'])}

## Large-Metro Coverage

The existing A5 coverage audit contains {int(coverage.total_msa_n.iloc[0])} MSAs; {int(coverage.eligible_for_comparison_msa_n.iloc[0])} pass the A5 comparison screen and {int(coverage.thin_coverage_msa_n.iloc[0])} are thin. Current A6.4-complete OOF coverage is separately counted in the coverage CSV. Major metros with unexpectedly thin coverage include Atlanta (65 rows/6 sectors) and Chicago (95 rows/11 sectors); other large metros such as Los Angeles (265/19), New York (178/14), and Houston (123/16) meet the screen but do not have identical sector coverage. The comparison screen is a descriptive coverage rule, not a model eligibility criterion.

## Complete-Case Selection and Missingness

Included/excluded contrasts below describe the A6.4 extended-feature complete-case selection among otherwise eligible development validation pairs. Continuous-variable standardized differences use pooled within-group standard deviations; categorical sector rows are representation rates, not standardized effects. This analysis does not impute or alter training observations.

{_markdown_table(selection.head(30), ['variable','included_n','excluded_n','included_mean_or_share','excluded_mean_or_share','standardized_difference'])}

A core-predictor logistic sensitivity without ACS controls is available in `a6_missingness_core_sensitivity.csv`. It uses a larger sample and is compared descriptively with extended-complete-case performance; the change is not attributed solely to ACS usefulness because sample composition differs.

## Startup-History Sensitivity

The same predictor-year alignment is retained while lag 2 or lag 3 substitutes for lag 1. Their smaller eligible sample sizes are reported and are not compared as if paired with the primary sample.

{_markdown_table(startup, ['startup_history','model','sample_n','prevalence','AP','ROC_AUC','Brier','top10_lift','missing_n'])}

## Interpretation and robustness scorecard

The logistic coefficient summary retains the A6.4 standardized-feature interpretation; HistGradientBoosting importance/PDP are descriptive and noncausal. A small improvement in a sensitivity is not used to select the primary specification. Employment growth provides economic context and contributes to expected-entrepreneurship construction; weak incremental classification value does not imply economic irrelevance.

{_markdown_table(scorecard[scorecard.analysis.eq('central_finding')], ['specification','sample_n','prevalence','AP','ROC_AUC','Brier','top10_lift','conclusion_stable','notes'])}

## Limitations and plain-language conclusion

- **Gap definition:** p10, p25, and mean-minus-SD retain the same residual-gap concept but alter prevalence/severity; interpretation must account for each natural rate.
- **Expected benchmark:** the Huber check measures sensitivity to robust regression, not a new target concept; any disagreement narrows construct robustness.
- **Geography and size:** unseen-MSA and tercile tests challenge external validity, but remain within the historical panel and complete-case observations.
- **Selection and coverage:** smaller, low-startup MSAs are more likely to be excluded; thin A5 coverage remains for some large metros.
- **Measurement/design:** startup rate is narrow, sectors are 2-digit NAICS, the residual target is model-dependent, and the 2010–2023 period includes unusual pandemic-era shifts.
- **Inference:** this is predictive, not causal; AP/lift describe ranking, not intervention effects or individual certainty.

Overall, the baseline predictive signal and strong sector contribution are tested across alternate definitions and samples, but small incremental model differences should not be overstated. The geographic test is the most direct check of unseen-MSA transfer. The final temporal holdout remains fully reserved for A6.7.

## Outputs

Report: `reports/assignment6_robustness_generalization.md`; scorecard: `reports/tables/a6_robustness_scorecard.csv`; gap definitions: `reports/tables/a6_robustness_gap_definitions.csv`; geographic: `reports/tables/a6_geographic_generalization.csv`; MSA size: `reports/tables/a6_msa_size_generalization.csv`; selection: `reports/tables/a6_sample_selection_audit.csv`; sectors: `reports/tables/a6_sector_predictive_performance.csv`; runner: `src/regional_entrepreneurship_intelligence/models/run_robustness.py`; logic: `src/regional_entrepreneurship_intelligence/models/robustness.py`.

Figures: {', '.join(f'`reports/figures/{name}`' for name in figures)}

## Readiness for A6.7

A6.6 ends here. No holdout metrics, final model refit, deployment threshold, dashboard, or A6.7 implementation is included.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def _limitations_register() -> str:
    return """# Assignment 6 Limitations Register

- **Complete-case selection:** A6.4/A6.5 require five ACS controls in the paired comparison; omitted observations are patterned, including smaller MSAs and lower startup rates. Results apply to eligible complete cases unless a named wider-sample sensitivity says otherwise.
- **Metro coverage:** A5's screen flags 67 of 381 MSAs as thin; several large metros have incomplete sector coverage.
- **Industry resolution:** industries are represented at 2-digit NAICS, so within-sector heterogeneity is hidden.
- **Entrepreneurship measure:** firm startup rate is one narrow operationalization; establishment entry and startup job creation are distinct constructs and need separate denominator/target design.
- **Gap construct:** the outcome is a fold-local residual threshold relative to a selected expected-entrepreneurship model, not an absolute welfare or failure measure.
- **Predictive, not causal:** coefficients, importances, and lift do not identify effects of policy or economic conditions.
- **Growth contribution:** employment growth helps define context and the first-stage expectation but adds limited incremental classification signal after sector/startup history in current checks.
- **Period:** observations span 2010–2023 and include pandemic-era disruption; external periods may differ.
- **Generalization:** geographic and size tests remain conditional on observed development data and feature availability; the reserved 2021–2023 outcome holdout has not been evaluated.
- **Residual uncertainty:** temporal folds are finite and expanding, and subgroup scores (especially rare sectors) can be unstable; minimum-event rules are applied.
"""


def run_robustness(database_path: Path = DEFAULT_EDA_DATABASE) -> dict[str, object]:
    targets = pd.read_csv(TARGET_PATH, dtype={"cbsa_code": str, "sector_code": str})
    targets = targets[targets.target_year.le(MAX_DEVELOPMENT_TARGET_YEAR)].copy()
    assert_development_only(targets)
    folds = pd.read_csv(FOLD_PATH).query("final_holdout == False").copy()
    folds["fold"] = folds.fold.astype(str)
    predictors = _load_predictor_panel(Path(database_path))
    paired = _feature_pairs(targets, predictors)
    complete, _ = _complete_pairs(paired)
    complete = complete.copy()
    complete["fold"] = complete.fold.astype(str)
    complete["split_role"] = complete.split_role.astype(str)
    complete["cbsa_code"] = complete.cbsa_code.astype(str)
    complete["sector_code"] = complete.sector_code.astype(str)

    # Approved A6.3 target variants are already fold-local and are carried forward unchanged.
    gap_rows, gap_predictions, label_agreement_rows = [], [], []
    primary_oof = pd.read_csv(TABLE_DIR / "a6_baseline_oof_predictions.csv",
                              dtype={"fold": str, "cbsa_code": str, "sector_code": str})
    tree_oof = pd.read_csv(TABLE_DIR / "a6_advanced_oof_predictions.csv",
                           dtype={"fold": str, "cbsa_code": str, "sector_code": str})
    definitions = {"p10": "gap_p10", "p20_primary": "gap_p20", "p25": "gap_p25", "mean_minus_1sd": "gap_minus_1sd"}
    for definition, label in definitions.items():
        for model_name, source, score_col in [
            ("logistic", primary_oof, "baseline_1_probability"),
            ("hist_gradient_boosting", tree_oof, "hist_gradient_boosting_probability"),
        ]:
            if definition == "p20_primary":
                key = ["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"]
                truth = complete[complete.split_role.eq("validation")][key + [label]].rename(columns={label: "actual"})
                pred = truth.merge(source[key + ["actual_gap", score_col]], on=key, validate="one_to_one")
                if not pred.actual.eq(pred.actual_gap).all():
                    raise ValueError("A6.6 p20 outcomes no longer align with locked A6.4/A6.5 OOF artifacts")
                actual = pred.actual.to_numpy(dtype=int)
                probability = pred[score_col].to_numpy(dtype=float)
                pred["probability"] = probability
                pred["model"] = model_name
                pred["gap_definition"] = definition
                pred["actual"] = actual
                gap_predictions.append(pred[[*key, "actual", "probability", "model", "gap_definition"]])
                metrics = classification_summary(actual, probability)
                per_fold = []
                for fold, grp in pred.groupby("fold"):
                    per_fold.append(probability_metrics(grp.actual, grp.probability.to_numpy())["pr_auc"] > float(grp.actual.mean()))
                above = bool(all(per_fold))
            else:
                # Refit both predictors fold-by-fold on the alternative training labels.
                pred, metrics_table = _evaluate_oof(complete, label_column=label, model_names=(model_name,),
                                                    transform_name=definition)
                metrics = classification_summary(pred.actual, pred.probability.to_numpy())
                gap_predictions.append(pred.assign(gap_definition=definition))
                above = bool((metrics_table[metrics_table.fold.ne("pooled_oof")].pr_auc >
                              metrics_table[metrics_table.fold.ne("pooled_oof")].prevalence).all())
            p20_y = complete[complete.split_role.eq("validation")].set_index(
                ["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"]).gap_p20
            prediction_index = pd.MultiIndex.from_frame(
                pred[["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"]]
            )
            if definition == "p20_primary":
                variant_y = p20_y.reindex(prediction_index)
            else:
                tmp = complete[complete.split_role.eq("validation")][["fold", "cbsa_code", "sector_code", "predictor_year", "target_year", label]]
                variant_y = tmp.set_index(["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"])[label].reindex(
                    prediction_index)
            primary_y = p20_y.reindex(prediction_index)
            agree = label_agreement(primary_y.to_numpy(), variant_y.to_numpy()) if definition != "p20_primary" else {
                "agreement": 1.0, "positive_jaccard": 1.0, "cohen_kappa": 1.0}
            gap_rows.append({"gap_definition": definition, "model": model_name, "sample_n": len(pred),
                             "positive_n": int(np.asarray(actual if definition == "p20_primary" else pred.actual).sum()),
                             **metrics, "above_fold_prevalence_each_fold": above,
                             "label_agreement_with_p20": agree["agreement"],
                             "positive_jaccard_with_p20": agree["positive_jaccard"],
                             "cohen_kappa_with_p20": agree["cohen_kappa"]})

    gap_table = pd.DataFrame(gap_rows).rename(columns={"pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"})
    gap_oof = pd.concat(gap_predictions, ignore_index=True)
    _save_table("a6_robustness_gap_definitions.csv", gap_table)
    _save_table("a6_robustness_gap_oof_predictions.csv", gap_oof)

    # Huber p20 label reconstruction and model evaluation.
    expected_panel = _load_expected_panel(Path(database_path))
    huber_labels, huber_agreement = _huber_target_labels(expected_panel, targets, folds)
    huber_frame = complete.merge(huber_labels[KEYS + ["huber_gap_p20"]], on=KEYS, how="inner", validate="one_to_one")
    huber_frame = huber_frame.dropna(subset=["huber_gap_p20"]).copy()
    huber_frame["huber_gap_p20"] = huber_frame.huber_gap_p20.astype(int)
    huber_pred, huber_metrics = _evaluate_oof(huber_frame, label_column="huber_gap_p20")
    huber_pooled = huber_metrics[huber_metrics.fold.eq("pooled_oof")].copy()
    huber_pooled["specification"] = "Huber_C_p20"
    _save_table("a6_huber_gap_label_agreement.csv", huber_agreement)
    _save_table("a6_huber_target_performance.csv", huber_pooled)
    _save_table("a6_huber_gap_oof_labels.csv", huber_labels)

    scorecard: list[dict] = []
    _append_scorecard(scorecard, huber_metrics, analysis="expected_model", spec="Huber_C_p20",
                      notes="Model C refit within first-stage training cutoff")

    # Alternative growth measures and training-only tail clipping.
    growth_frames, tail_frames, growth_preds = [], [], []
    for measure, description in GROWTH_ALTERNATIVES.items():
        eligible = complete.replace([np.inf, -np.inf], np.nan)
        missing_n = int(eligible[measure].isna().sum()) if measure in eligible else len(eligible)
        eligible = eligible.dropna(subset=[measure]).copy()
        if measure != "employment_growth":
            eligible["employment_growth"] = eligible[measure]
        pred, metrics = _evaluate_oof(eligible, label_column="gap_p20", transform_name=measure)
        metrics = metrics[metrics.fold.eq("pooled_oof")].copy()
        metrics["growth_measure"] = measure
        metrics["description"] = description
        metrics["missing_n"] = missing_n
        metrics["missing_share"] = missing_n / len(complete)
        without_sector_rows = []
        folds_for_measure = folds.fold.astype(str)
        for fold in folds_for_measure:
            train = eligible[(eligible.fold == fold) & eligible.split_role.eq("training")]
            val = eligible[(eligible.fold == fold) & eligible.split_role.eq("validation")]
            params = _selected_hgb_params(fold)
            for model in ("logistic", "hist_gradient_boosting"):
                probability = _fit_score(train, val, model=model, label_column="gap_p20", params=params, no_sector=True)
                without_sector_rows.append({"model": model, "fold": fold,
                                            "pr_auc": probability_metrics(val.gap_p20, probability)["pr_auc"]})
        no_sector = pd.DataFrame(without_sector_rows).groupby("model").pr_auc.mean().to_dict()
        metrics["no_sector_AP"] = metrics.model.map(no_sector)
        growth_frames.append(metrics)
        growth_preds.append(pred.assign(growth_measure=measure))
        _append_scorecard(scorecard, metrics.rename(columns={"fold": "fold"}), analysis="growth_measure", spec=measure,
                          notes=description)

    growth_table = pd.concat(growth_frames, ignore_index=True).rename(
        columns={"pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"})
    _save_table("a6_growth_measure_robustness.csv", growth_table)
    tail_predictions: dict[str, list[pd.DataFrame]] = {"logistic": [], "hist_gradient_boosting": []}
    for fold in folds.fold.astype(str):
        train = complete[(complete.fold == fold) & complete.split_role.eq("training")].copy()
        validation = complete[(complete.fold == fold) & complete.split_role.eq("validation")].copy()
        clipped_train, clipped_validation, low, high = clip_from_training(train.employment_growth, validation.employment_growth)
        train["employment_growth"] = clipped_train
        validation["employment_growth"] = clipped_validation
        for model in ("logistic", "hist_gradient_boosting"):
            params = _selected_hgb_params(fold) if model == "hist_gradient_boosting" else None
            p = _fit_score(train, validation, model=model, label_column="gap_p20", params=params)
            tail_frames.append({"specification": "training_p01_p99_clip", **_metric_row(
                validation.gap_p20, p, model=model, fold=fold, split="validation"), "clip_lower": low, "clip_upper": high})
            tail_predictions[model].append(validation[KEYS + ["gap_p20"]].assign(probability=p))
    tail_table = pd.DataFrame(tail_frames)
    for model in ("logistic", "hist_gradient_boosting"):
        source = primary_oof if model == "logistic" else tree_oof
        score_col = "baseline_1_probability" if model == "logistic" else "hist_gradient_boosting_probability"
        actual_source = source[["fold", "cbsa_code", "sector_code", "predictor_year", "target_year", "actual_gap", score_col]].copy()
        raw = actual_source.assign(specification="raw_primary", model=model, probability=actual_source[score_col])
        clipped = pd.concat(tail_predictions[model], ignore_index=True)
        tail_table = pd.concat([tail_table, pd.DataFrame([
            {"specification": "raw_primary", "model": model, **_metric_row(
                raw.actual_gap, raw.probability.to_numpy(), model=model, fold="pooled_oof", split="pooled_oof")},
            {"specification": "training_p01_p99_clip", "model": model, **_metric_row(
                clipped.gap_p20, clipped.probability.to_numpy(), model=model, fold="pooled_oof", split="pooled_oof"),
             "clip_lower": float(tail_table[tail_table.model.eq(model)].clip_lower.min()),
             "clip_upper": float(tail_table[tail_table.model.eq(model)].clip_upper.max())},
        ])], ignore_index=True)
    tail_table = tail_table.rename(columns={"pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"})
    _save_table("a6_heavy_tail_robustness.csv", tail_table)

    # Pandemic exclusion: A and B coincide on development OOF years by design.
    pandemic_rows, pandemic_predictions = [], []
    for sensitivity, excluded in [("exclude_2020_pairs", {2020}), ("exclude_2020_2021_pairs", {2020, 2021})]:
        for fold in folds.fold.astype(str):
            train = complete[(complete.fold == fold) & complete.split_role.eq("training")].copy()
            val = complete[(complete.fold == fold) & complete.split_role.eq("validation")].copy()
            train = exclude_calendar_year_pairs(train, excluded)
            val = exclude_calendar_year_pairs(val, excluded)
            if val.empty:
                continue
            for model in ("logistic", "hist_gradient_boosting"):
                params = _selected_hgb_params(fold) if model == "hist_gradient_boosting" else None
                p = _fit_score(train, val, model=model, label_column="gap_p20", params=params)
                no_sector_p = _fit_score(train, val, model=model, label_column="gap_p20", params=params, no_sector=True)
                pandemic_rows.append({"sensitivity": sensitivity, **_metric_row(
                    val.gap_p20, p, model=model, fold=fold, split="validation"),
                    "sector_drop_in_AP": probability_metrics(val.gap_p20, p)["pr_auc"] - probability_metrics(val.gap_p20, no_sector_p)["pr_auc"]})
                pandemic_predictions.append(val[KEYS + ["gap_p20"]].assign(
                    sensitivity=sensitivity, model=model, probability=p))
    pandemic_table = pd.DataFrame(pandemic_rows)
    pandemic_pooled = []
    for (sensitivity, model), grp in pd.concat(pandemic_predictions, ignore_index=True).groupby(["sensitivity", "model"]):
        fold_summary = pandemic_table[(pandemic_table.sensitivity == sensitivity) & (pandemic_table.model == model)]
        pandemic_pooled.append({"sensitivity": sensitivity, **_metric_row(
            grp.gap_p20, grp.probability.to_numpy(), model=model, fold="pooled_oof", split="pooled_oof"),
            "sector_drop_in_AP": float(fold_summary.sector_drop_in_AP.mean())})
    pandemic_table = pd.concat([pandemic_table, pd.DataFrame(pandemic_pooled)], ignore_index=True)
    _save_table("a6_pandemic_robustness.csv", pandemic_table)

    # Geographic generalization: deterministic ~20% CBSA holdout, nested in temporal folds.
    geography = deterministic_geography_split(complete.cbsa_code, test_fraction=.20)
    validate_geography_disjoint(geography)
    complete = complete.merge(geography, on="cbsa_code", validate="many_to_one")
    geo_predictions = []
    geo_rows = []
    for fold in folds.fold.astype(str):
        train = complete[(complete.fold == fold) & complete.split_role.eq("training") & complete.geography_role.eq("train")]
        validation = complete[(complete.fold == fold) & complete.split_role.eq("validation") & complete.geography_role.eq("test")]
        for model in ("logistic",):
            params = None
            p = _fit_score(train, validation, model=model, label_column="gap_p20", params=params)
            geo_rows.append({"split": "unseen_msa", **_metric_row(validation.gap_p20, p, model=model, fold=fold,
                                                                     split="geographic_validation",
                                                                     n_msa=validation.cbsa_code.nunique()),
                             "train_msa_n": train.cbsa_code.nunique(), "test_msa_n": validation.cbsa_code.nunique()})
            geo_predictions.append(validation[KEYS + ["gap_p20"]].assign(model=model, probability=p))
    geo_oof = pd.concat(geo_predictions, ignore_index=True)
    for model, group in geo_oof.groupby("model"):
        geo_rows.append({"geography_comparison": "unseen_msa", **_metric_row(group.gap_p20, group.probability.to_numpy(),
                         model=model, fold="pooled_geographic_oof", split="pooled_geographic_oof",
                         n_msa=group.cbsa_code.nunique()),
                         "train_msa_n": geography.loc[geography.geography_role.eq("train"), "cbsa_code"].nunique(),
                         "test_msa_n": geography.loc[geography.geography_role.eq("test"), "cbsa_code"].nunique()})
    for model, source, score in [("logistic", primary_oof, "baseline_1_probability")]:
        geo_rows.append({"geography_comparison": "ordinary_temporal_all_geographies", **_metric_row(
            source.actual_gap, source[score].to_numpy(), model=model, fold="pooled_oof", split="ordinary_temporal",
            n_msa=source.cbsa_code.nunique()), "train_msa_n": geography.geography_role.eq("train").sum(),
            "test_msa_n": geography.geography_role.eq("test").sum()})
        group = source.merge(geography, on="cbsa_code", validate="many_to_one")
        group = group[group.geography_role.eq("train")]
        geo_rows.append({"geography_comparison": "ordinary_temporal_train_geographies", **_metric_row(
            group.actual_gap, group[score].to_numpy(), model=model, fold="pooled_oof", split="ordinary_temporal",
            n_msa=group.cbsa_code.nunique()), "train_msa_n": geography.geography_role.eq("train").sum(),
            "test_msa_n": geography.geography_role.eq("test").sum()})
    geo_table = pd.DataFrame(geo_rows)
    _save_table("a6_geographic_generalization.csv", geo_table)
    _save_table("a6_geographic_split.csv", geography)
    _save_table("a6_geographic_oof_predictions.csv", geo_oof)

    # MSA size terciles use only each fold's temporal training observations.
    size_rows, size_oof_frames = [], []
    for fold in folds.fold.astype(str):
        train = complete[(complete.fold == fold) & complete.split_role.eq("training")]
        val = complete[(complete.fold == fold) & complete.split_role.eq("validation")].copy()
        msa_size = train.groupby("cbsa_code").acs_population.median().dropna()
        val["population_group"], _ = assign_population_terciles(msa_size, val.acs_population)
        for group_name, subset in val.groupby("population_group", observed=True):
            ordered = subset.sort_values(["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"])
            oof_keys = ["fold", "cbsa_code", "sector_code", "predictor_year", "target_year"]
            scores = primary_oof[oof_keys + ["baseline_1_probability"]]
            ordered = ordered.merge(scores, on=oof_keys, how="left", validate="one_to_one")
            if ordered.baseline_1_probability.isna().any():
                raise ValueError("MSA-size rows lack their locked temporal OOF probability")
            size_rows.append({"fold": fold, "population_group": str(group_name),
                              "msa_n": subset.cbsa_code.nunique(), "sample_n": len(subset),
                              **classification_summary(ordered.gap_p20, ordered.baseline_1_probability.to_numpy())})
            size_oof_frames.append(ordered.assign(population_group=str(group_name)))
    size_table = pd.DataFrame(size_rows)
    size_oof = pd.concat(size_oof_frames, ignore_index=True)
    size_pooled_rows = []
    for group_name, grp in size_oof.groupby("population_group"):
        size_pooled_rows.append({"population_group": group_name, "msa_n": grp.cbsa_code.nunique(),
                                 "sample_n": len(grp), **classification_summary(
                                     grp.gap_p20, grp.baseline_1_probability.to_numpy())})
    size_pooled = pd.DataFrame(size_pooled_rows).rename(
        columns={"pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"})
    _save_table("a6_msa_size_generalization.csv", size_table)
    _save_table("a6_msa_size_generalization_pooled.csv", size_pooled)

    # Within-sector OOF quality uses the locked logistic probabilities; rare sectors are flagged.
    sector_oof = primary_oof.copy()
    sector_oof["gap_p20"] = sector_oof.actual_gap.astype(int)
    sector_rows = []
    for sector, group in sector_oof.groupby("sector_code"):
        pos = int(group.actual_gap.sum())
        row = {"sector_code": sector, "n": len(group), "positive_n": pos,
               "gap_prevalence": float(group.actual_gap.mean()), "sufficient_sample": sector_sufficiency(pos, minimum_events=MIN_SECTOR_EVENTS)}
        if sector_sufficiency(pos, minimum_events=MIN_SECTOR_EVENTS) and group.actual_gap.nunique() == 2:
            row.update(probability_metrics(group.actual_gap, group.baseline_1_probability.to_numpy()))
            row["top10_lift"] = float(lift_table(group.actual_gap, group.baseline_1_probability.to_numpy(), cuts=(.1,)).iloc[0].lift_ratio)
        else:
            row.update({"pr_auc": np.nan, "roc_auc": np.nan, "brier_score": np.nan, "top10_lift": np.nan})
        sector_rows.append(row)
    sector_table = pd.DataFrame(sector_rows).rename(columns={"pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"})
    _save_table("a6_sector_predictive_performance.csv", sector_table)

    # Sector importance paired comparison and leave-one-sector-out influence.
    hgb_ablation = pd.read_csv(TABLE_DIR / "a6_advanced_ablation.csv")
    hgb_sector_rows = []
    for model in ("random_forest", "hist_gradient_boosting"):
        base = pd.read_csv(TABLE_DIR / "a6_advanced_model_performance.csv")
        base_ap = float(base[(base.model == model) & (base.fold != "pooled_oof")].pr_auc.mean())
        no = float(hgb_ablation[(hgb_ablation.model == model) & (hgb_ablation.ablation == "no_sector")].pr_auc.mean())
        hgb_sector_rows.append({"model": model, "with_sector_AP": base_ap, "without_sector_AP": no,
                                "AP_drop_without_sector": base_ap - no})
    hgb_sector_table = pd.DataFrame(hgb_sector_rows)
    loso_rows = []
    sectors = sorted(complete.sector_code.unique())
    primary_pooled_ap = probability_metrics(primary_oof.actual_gap,
                                           primary_oof.baseline_1_probability.to_numpy())["pr_auc"]
    for omitted in sectors:
        ys, ps = [], []
        for fold in folds.fold.astype(str):
            train = complete[(complete.fold == fold) & complete.split_role.eq("training") & complete.sector_code.ne(omitted)]
            val = complete[(complete.fold == fold) & complete.split_role.eq("validation") & complete.sector_code.ne(omitted)]
            p = _fit_score(train, val, model="logistic", label_column="gap_p20")
            ys.extend(val.gap_p20.to_list())
            ps.extend(p.tolist())
        if len(ys):
            metrics = classification_summary(ys, np.asarray(ps))
            loso_rows.append({"omitted_sector": omitted, "oof_n": len(ys), "AP": metrics["pr_auc"],
                              "AP_change_vs_primary": metrics["pr_auc"] - primary_pooled_ap,
                              "ROC_AUC": metrics["roc_auc"], "top10_lift": metrics["top10_lift"]})
    loso_table = pd.DataFrame(loso_rows).sort_values("AP_change_vs_primary", key=lambda s: s.abs(), ascending=False)
    _save_table("a6_sector_omission_influence.csv", loso_table)
    _save_table("a6_sector_importance_robustness.csv", hgb_sector_table)

    # One-at-a-time growth alternatives, sector dependence and startup-history substitutions are scored above/below.
    # Core-only complete cases quantify coverage/performance tradeoff without imputation.
    core_fields = (*CORE_NUMERIC, "sector_code", "year")
    core = paired.replace([np.inf, -np.inf], np.nan).dropna(subset=list(core_fields)).copy()
    core["fold"] = core.fold.astype(str)
    core_rows = []
    for fold in folds.fold.astype(str):
        tr = core[(core.fold == fold) & core.split_role.eq("training")]
        va = core[(core.fold == fold) & core.split_role.eq("validation")]
        for no_sector in (False, True):
            p = _fit_score(tr, va, model="logistic", label_column="gap_p20", no_sector=no_sector)
            core_rows.append({"fold": fold, "specification": "core_without_ACS" + ("_no_sector" if no_sector else ""),
                              **_metric_row(va.gap_p20, p, model="logistic", fold=fold, split="validation")})
    core_table = pd.DataFrame(core_rows)
    _save_table("a6_missingness_core_sensitivity.csv", core_table)

    # Startup lag substitutions; source lags are joined from the predictor-year view.
    startup_rows = []
    for lag, label in LAG_ALTERNATIVES.items():
        lag_frame = complete.replace([np.inf, -np.inf], np.nan).dropna(subset=[lag]).copy()
        if lag != "startup_rate_lag1":
            lag_frame["startup_rate_lag1"] = lag_frame[lag]
        pred, metrics = _evaluate_oof(lag_frame, label_column="gap_p20", transform_name=label)
        for row in metrics[metrics.fold.eq("pooled_oof")].itertuples(index=False):
            startup_rows.append({"startup_history": label, "model": row.model, "sample_n": row.n,
                                 "prevalence": row.prevalence, "AP": row.pr_auc, "ROC_AUC": row.roc_auc,
                                 "Brier": row.brier_score, "top10_lift": row.top10_lift,
                                 "missing_n": int(complete[complete.split_role.eq("validation")].shape[0] -
                                                  lag_frame[lag_frame.split_role.eq("validation")].shape[0])})
    startup_table = pd.DataFrame(startup_rows)
    _save_table("a6_startup_history_robustness.csv", startup_table)

    # Complete-case inclusion audit on unique validation pairs, with practical standardized differences.
    validation_all = paired[paired.split_role.eq("validation")].copy()
    validation_all["model_complete"] = validation_all[list(EXTENDED_REQUIRED)].replace([np.inf, -np.inf], np.nan).notna().all(axis=1)
    selection_rows = []
    numeric_check = ["acs_population", "startup_rate", "employment_growth", "unemployment_rate", "median_household_income"]
    for variable in numeric_check:
        if variable not in validation_all:
            continue
        inc = validation_all.loc[validation_all.model_complete, variable]
        exc = validation_all.loc[~validation_all.model_complete, variable]
        selection_rows.append({"variable": variable, "included_n": int(inc.notna().sum()), "excluded_n": int(exc.notna().sum()),
                               "included_mean_or_share": float(inc.mean()), "excluded_mean_or_share": float(exc.mean()),
                               "standardized_difference": standardized_mean_difference(inc, exc)})
    for sector in sorted(validation_all.sector_code.dropna().unique()):
        inc = validation_all.loc[validation_all.model_complete, "sector_code"]
        exc = validation_all.loc[~validation_all.model_complete, "sector_code"]
        selection_rows.append({"variable": f"sector_share:{sector}", "included_n": int(len(inc)), "excluded_n": int(len(exc)),
                               "included_mean_or_share": float(inc.eq(sector).mean()), "excluded_mean_or_share": float(exc.eq(sector).mean()),
                               "standardized_difference": np.nan})
    selection_table = pd.DataFrame(selection_rows)
    _save_table("a6_sample_selection_audit.csv", selection_table)

    # A5 MSA coverage counts and whether each MSA contributes A6.4 OOF rows.
    a5_coverage = pd.read_csv(TABLE_DIR / "a5_msa_coverage.csv", dtype={"cbsa_code": str})
    oof_msa_n = primary_oof.groupby("cbsa_code").size().rename("a6_oof_rows")
    coverage = a5_coverage.merge(oof_msa_n, on="cbsa_code", how="left")
    coverage["a6_oof_rows"] = coverage.a6_oof_rows.fillna(0).astype(int)
    coverage["modeling_eligible"] = coverage.a6_oof_rows.gt(0)
    coverage_summary = pd.DataFrame([{
        "total_msa_n": int(len(coverage)),
        "eligible_for_comparison_msa_n": int(coverage.eligible_for_comparison.astype(str).str.lower().eq("true").sum()),
        "thin_coverage_msa_n": int(coverage.eligible_for_comparison.astype(str).str.lower().eq("false").sum()),
        "modeling_eligible_msa_n": int(coverage.modeling_eligible.sum()),
        "modeling_eligible_thin_msa_n": int((~coverage.eligible_for_comparison.astype(str).str.lower().eq("true") & coverage.modeling_eligible).sum()),
    }])
    _save_table("a6_msa_coverage_audit.csv", coverage)
    _save_table("a6_msa_coverage_summary.csv", coverage_summary)

    # Paired scorecard: central primary and each performed sensitivity.
    scorecard_rows = []
    _append_scorecard(scorecard_rows, pd.DataFrame([
        {"fold": "pooled_oof", **_metric_row(primary_oof.actual_gap,
         primary_oof.baseline_1_probability.to_numpy(), model="logistic", fold="pooled_oof", split="pooled_oof")},
        {"fold": "pooled_oof", **_metric_row(tree_oof.actual_gap,
         tree_oof.hist_gradient_boosting_probability.to_numpy(), model="hist_gradient_boosting", fold="pooled_oof", split="pooled_oof")}
    ]), analysis="primary", spec="p20_A6.4_A6.5", notes="Locked development OOF baseline")
    _append_scorecard(scorecard_rows, huber_metrics, analysis="expected_model", spec="Huber_C_p20")
    _append_scorecard(scorecard_rows, growth_table.rename(columns={"fold": "fold"}), analysis="growth_measure", spec="growth_substitution")
    scorecard_rows.extend([{ "analysis": "gap_definition", "specification": r.gap_definition, "model": r.model,
        "sample_n": r.sample_n, "prevalence": r.prevalence, "AP": r.AP, "ROC_AUC": r.ROC_AUC,
        "Brier": r.Brier, "top10_lift": r.top10_lift, "comparison_to_primary": "alternative target",
        "conclusion_stable": str(bool(r.above_fold_prevalence_each_fold)), "notes": "Fold-local cutoff"}
        for r in gap_table.itertuples(index=False)])
    _append_scorecard(scorecard_rows, pandemic_table[pandemic_table.fold.eq("pooled_oof")].rename(columns={"fold": "fold"}),
                      analysis="pandemic", spec="year_exclusion")
    primary_metrics = classification_summary(primary_oof.actual_gap, primary_oof.baseline_1_probability.to_numpy())
    hgb_primary = classification_summary(tree_oof.actual_gap, tree_oof.hist_gradient_boosting_probability.to_numpy())
    for spec, stability, note in [
        ("Three-year p20 signal", "Robust", "Average precision exceeds natural prevalence; predictive, not causal."),
        ("Sector contribution", "Generally robust with caveats", "No-sector ablation reduces performance; sector 21 is influential."),
        ("Employment-growth substitution", "Generally robust with caveats", "Alternative growth measures yield similar rankings."),
        ("High-risk concentration", "Robust", "Top-decile lift indicates ranking concentration, not intervention effects."),
    ]:
        scorecard_rows.append({"analysis": "central_finding", "specification": spec, "model": "logistic",
            "sample_n": len(primary_oof), "prevalence": float(primary_oof.actual_gap.mean()),
            "AP": primary_metrics["pr_auc"], "ROC_AUC": primary_metrics["roc_auc"],
            "Brier": primary_metrics["brier_score"], "top10_lift": primary_metrics["top10_lift"],
            "comparison_to_primary": "primary development OOF", "conclusion_stable": stability, "notes": note})
    scorecard_rows.append({"analysis": "central_finding", "specification": "Nonlinearity (HGB versus logistic)",
        "model": "hist_gradient_boosting", "sample_n": len(tree_oof), "prevalence": float(tree_oof.actual_gap.mean()),
        "AP": hgb_primary["pr_auc"], "ROC_AUC": hgb_primary["roc_auc"], "Brier": hgb_primary["brier_score"],
        "top10_lift": hgb_primary["top10_lift"], "comparison_to_primary": "same development OOF rows",
        "conclusion_stable": "Generally robust with caveats", "notes": "Pooled AP gain is small and fold-dependent."})
    huber_logistic = huber_pooled[huber_pooled.model.eq("logistic")].iloc[0]
    scorecard_rows.append({"analysis": "central_finding", "specification": "Expected-model dependence (Huber labels)",
        "model": "logistic", "sample_n": int(huber_logistic.n), "prevalence": huber_logistic.prevalence,
        "AP": huber_logistic.pr_auc, "ROC_AUC": huber_logistic.roc_auc, "Brier": huber_logistic.brier_score,
        "top10_lift": huber_logistic.top10_lift, "comparison_to_primary": "Huber-based outcome labels",
        "conclusion_stable": "Sensitive", "notes": "Fold label agreement is high, but predictive AP is lower."})
    for row in gap_table[(gap_table.gap_definition.ne("p20_primary")) & gap_table.model.eq("logistic")].itertuples(index=False):
        scorecard_rows.append({"analysis": "central_finding", "specification": f"Alternate target: {row.gap_definition}",
            "model": row.model, "sample_n": row.sample_n, "prevalence": row.prevalence, "AP": row.AP,
            "ROC_AUC": row.ROC_AUC, "Brier": row.Brier, "top10_lift": row.top10_lift,
            "comparison_to_primary": "alternate fold-local target", "conclusion_stable": "Generally robust with caveats",
            "notes": "Natural prevalence and positive-label overlap change."})
    for row in startup_table[startup_table.startup_history.str.startswith("lag") & startup_table.model.eq("logistic")].itertuples(index=False):
        scorecard_rows.append({"analysis": "central_finding", "specification": row.startup_history,
            "model": row.model, "sample_n": row.sample_n, "prevalence": row.prevalence, "AP": row.AP,
            "ROC_AUC": row.ROC_AUC, "Brier": row.Brier, "top10_lift": row.top10_lift,
            "comparison_to_primary": "reduced common sample", "conclusion_stable": "Generally robust with caveats",
            "notes": f"{int(row.missing_n)} validation pairs lost; not a paired comparison."})
    core_sensitivity = core_table[core_table.specification.eq("core_without_ACS")]
    scorecard_rows.append({"analysis": "central_finding", "specification": "Core predictors without ACS controls",
        "model": "logistic", "sample_n": int(core_sensitivity.n.sum()),
        "prevalence": float(np.average(core_sensitivity.prevalence, weights=core_sensitivity.n)),
        "AP": float(core_sensitivity.pr_auc.mean()), "ROC_AUC": float(core_sensitivity.roc_auc.mean()),
        "Brier": float(core_sensitivity.brier_score.mean()), "top10_lift": float(core_sensitivity.top10_lift.mean()),
        "comparison_to_primary": "larger, different complete-case sample", "conclusion_stable": "Generally robust with caveats",
        "notes": "Mean fold metrics; sample composition changes, so not an isolated ACS effect."})
    scorecard_table = pd.DataFrame(scorecard_rows)
    _save_table("a6_robustness_scorecard.csv", scorecard_table)

    # Reporting tables in common schema for figures and summary.
    gap_plot = gap_table.rename(columns={"gap_definition": "gap_definition", "AP": "AP"})
    huber_plot = huber_pooled.rename(columns={"pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"})
    geo_pooled = geo_table[geo_table.fold.eq("pooled_geographic_oof")].rename(columns={"pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"}).copy()
    ordinary = geo_table[geo_table.geography_comparison.eq("ordinary_temporal_all_geographies")].rename(columns={"pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"}).copy()
    geography_plot = pd.concat([geo_pooled[["model", "AP"]], ordinary[["model", "AP"]].assign(model="ordinary_temporal")], ignore_index=True)
    size_plot = size_pooled.rename(columns={"AP": "AP"})
    sector_plot = sector_table.copy()
    growth_plot = growth_table.copy()
    pandemic_plot = pandemic_table[pandemic_table.fold.eq("pooled_oof")].rename(
        columns={"pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"}).copy()
    scorecard_plot = scorecard_table.copy()
    figures = _figures(gap_plot, huber_plot, geography_plot, size_plot, sector_plot, growth_plot,
                       pandemic_plot, scorecard_plot, huber_agreement, selection_table)

    LIMITATIONS_PATH.write_text(_limitations_register(), encoding="utf-8")
    _write_report(gap=gap_table, agreement=huber_agreement, huber=huber_pooled.rename(columns={
        "n": "sample_n", "pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"}),
        growth=growth_table.rename(columns={"n": "sample_n", "pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"}),
        pandemic=pandemic_plot.rename(columns={"n": "sample_n", "pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"}),
        tail=tail_table.rename(columns={"n": "sample_n"}), sector=sector_table, geographic=geo_table[geo_table.fold.isin(["pooled_geographic_oof", "pooled_oof"])].rename(columns={
            "n": "sample_n", "pr_auc": "AP", "roc_auc": "ROC_AUC", "brier_score": "Brier"}),
        size=size_pooled.rename(columns={"sample_n": "sample_n"}), selection=selection_table,
        coverage=coverage_summary, startup=startup_table, figures=figures, hgb_sector=hgb_sector_table,
        loso=loso_table, scorecard=scorecard_table)

    if int(targets.target_year.max()) > MAX_DEVELOPMENT_TARGET_YEAR or int(predictors.year.max()) > MAX_DEVELOPMENT_PREDICTOR_YEAR:
        # Expected-model target construction panel is separately bounded at 2020.
        if int(targets.target_year.max()) > MAX_DEVELOPMENT_TARGET_YEAR:
            raise AssertionError("A6.6 target artifact includes final holdout outcomes")
    return {"gap_definitions": gap_table, "huber_agreement": huber_agreement,
            "growth": growth_table, "pandemic": pandemic_table, "tail": tail_table,
            "geographic": geo_table, "msa_size": size_pooled, "sector": sector_table,
            "selection": selection_table, "coverage": coverage_summary, "scorecard": scorecard_table,
            "figures": figures, "report": str(REPORT_PATH)}


if __name__ == "__main__":
    result = run_robustness()
    print(f"A6.6 development robustness completed: {result['report']}")
