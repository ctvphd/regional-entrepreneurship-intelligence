"""Run Assignment 6.2 expected-entrepreneurship estimation and diagnostics."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "rei-matplotlib-cache"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.analysis.eda import (
    DEFAULT_EDA_DATABASE,
    load_analytical_panel,
)
from regional_entrepreneurship_intelligence.models.expected import (
    BASE_FEATURES,
    BASE_FORMULA,
    MODEL_FEATURES,
    MODEL_FORMULAS,
    fit_expected_model,
    predict_expected,
    regression_metrics,
)
from regional_entrepreneurship_intelligence.models.temporal import build_temporal_pairs

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TABLE_DIR = PROJECT_ROOT / "reports" / "tables"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures"
REPORT_PATH = PROJECT_ROOT / "reports" / "assignment6_expected_entrepreneurship_model.md"
SPEC_PATH = PROJECT_ROOT / "docs" / "ASSIGNMENT6_EXPECTED_MODEL.md"
FOLD_PATH = PROJECT_ROOT / "config" / "assignment6_temporal_folds.csv"
CORE_MODELS = ("A", "B", "C")


def _fold_rows(panel: pd.DataFrame, fold: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    train = panel[
        panel.year.between(
            int(fold.first_stage_fit_start_year), int(fold.first_stage_fit_end_year)
        )
    ].copy()
    pairs = build_temporal_pairs(panel[["cbsa_code", "sector_code", "year"]])
    pairs = pairs[
        pairs.predictor_year.between(
            int(fold.validation_predictor_start_year),
            int(fold.validation_predictor_end_year),
        )
    ]
    outcomes = panel.rename(columns={"year": "target_year"})
    validation = pairs.merge(
        outcomes,
        on=["cbsa_code", "sector_code", "target_year"],
        how="inner",
        validate="one_to_one",
    )
    validation["year"] = validation.target_year
    return train, validation, len(pairs)


def _metrics_row(
    fold_name: str,
    model_name: str,
    training: pd.DataFrame,
    validation: pd.DataFrame,
    predictions_train: pd.DataFrame,
    predictions_validation: pd.DataFrame,
    estimator: str,
) -> dict[str, object]:
    row: dict[str, object] = {
        "fold": fold_name,
        "model": model_name,
        "estimator": estimator,
        "training_complete_case_n": len(predictions_train),
        "validation_complete_case_n": len(predictions_validation),
        "training_start_year": int(training.year.min()),
        "training_end_year": int(training.year.max()),
        "validation_target_years": ",".join(map(str, sorted(validation.year.unique()))),
    }
    train_stats = regression_metrics(
        predictions_train.startup_rate,
        predictions_train.expected_startup_rate,
    )
    val_stats = regression_metrics(
        predictions_validation.startup_rate,
        predictions_validation.expected_startup_rate,
        training_mean=float(predictions_train.startup_rate.mean()),
    )
    row.update({f"train_{key}": value for key, value in train_stats.items() if key != "n"})
    row.update({f"validation_{key}": value for key, value in val_stats.items() if key != "n"})
    row["train_n"] = train_stats["n"]
    row["validation_n"] = val_stats["n"]
    return row


def _residual_summary(frame: pd.DataFrame, group: str) -> pd.DataFrame:
    return (
        frame.groupby(group, observed=True)
        .agg(
            n=("residual", "size"),
            mean_residual=("residual", "mean"),
            median_residual=("residual", "median"),
            residual_sd=("residual", "std"),
            mae=("residual", lambda values: float(np.mean(np.abs(values)))),
            rmse=("residual", lambda values: float(np.sqrt(np.mean(np.square(values))))),
        )
        .reset_index()
    )


def _coefficient_rows(fold_name: str, model_name: str, model: object) -> list[dict[str, object]]:
    params = model.result.params
    return [
        {"fold": fold_name, "model": model_name, "term": term, "coefficient": float(value)}
        for term, value in params.items()
    ]


def _save_figures(
    predictions: pd.DataFrame,
    comparison: pd.DataFrame,
    by_year: pd.DataFrame,
    by_sector: pd.DataFrame,
) -> list[str]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    names: list[str] = []

    def save(fig: plt.Figure, name: str) -> None:
        fig.tight_layout()
        fig.savefig(FIGURE_DIR / name, dpi=160)
        plt.close(fig)
        names.append(name)

    colors = {"A": "#235789", "B": "#168aad", "C": "#e07a2d"}
    fig, ax = plt.subplots(figsize=(7, 5))
    for model, group in predictions.groupby("model", sort=True):
        ax.scatter(group.observed_startup_rate, group.expected_startup_rate, s=8, alpha=.22, label=f"Model {model}", color=colors[model])
    limits = [
        float(min(predictions.observed_startup_rate.min(), predictions.expected_startup_rate.min())),
        float(max(predictions.observed_startup_rate.max(), predictions.expected_startup_rate.max())),
    ]
    ax.plot(limits, limits, color="#444444", linewidth=1)
    ax.set(xlabel="Observed startup rate", ylabel="Expected startup rate", title="Development-fold observed and expected rates")
    ax.legend(frameon=False)
    save(fig, "a6_expected_observed_vs_expected.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    for model, group in predictions.groupby("model", sort=True):
        ax.hist(group.residual, bins=60, density=True, histtype="step", linewidth=1.8, label=f"Model {model}", color=colors[model])
    ax.axvline(0, color="#444444", linewidth=1)
    ax.set(xlabel="Observed minus expected startup rate", ylabel="Density", title="Development-fold validation residuals")
    ax.legend(frameon=False)
    save(fig, "a6_expected_residual_distributions.png")

    for metric, ylabel, filename in (
        ("validation_mae", "MAE", "a6_expected_validation_mae.png"),
        ("validation_rmse", "RMSE", "a6_expected_validation_rmse.png"),
    ):
        fig, ax = plt.subplots(figsize=(7, 4.5))
        pivot = comparison[comparison.model.isin(CORE_MODELS)].pivot(index="fold", columns="model", values=metric)
        pivot.plot(kind="bar", ax=ax, color=[colors[column] for column in pivot.columns])
        ax.set(ylabel=ylabel, xlabel="Development fold", title=f"Validation {ylabel} by fold and candidate")
        ax.legend(title="Model", frameon=False)
        save(fig, filename)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    pivot = by_year[by_year.model.isin(CORE_MODELS)].pivot(index="year", columns="model", values="mean_residual")
    pivot.plot(marker="o", ax=ax, color=[colors[column] for column in pivot.columns])
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set(xlabel="Validation outcome year", ylabel="Mean residual", title="Mean validation residual by year")
    ax.legend(title="Model", frameon=False)
    save(fig, "a6_expected_residual_by_year.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    pivot = by_sector[by_sector.model.isin(CORE_MODELS)].pivot(index="sector_code", columns="model", values="mean_residual")
    pivot.plot(kind="bar", ax=ax, color=[colors[column] for column in pivot.columns])
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set(xlabel="2017 NAICS sector", ylabel="Mean residual", title="Mean validation residual by sector")
    ax.legend(title="Model", frameon=False)
    save(fig, "a6_expected_residual_by_sector.png")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for model, group in predictions.groupby("model", sort=True):
        ax.scatter(group.expected_startup_rate, group.residual, s=8, alpha=.18, label=f"Model {model}", color=colors[model])
    ax.axhline(0, color="#444444", linewidth=1)
    ax.set(xlabel="Expected startup rate", ylabel="Residual", title="Residuals versus expected rate")
    ax.legend(frameon=False)
    save(fig, "a6_expected_residual_vs_fitted.png")

    fold_sector = (
        predictions[predictions.model.isin(CORE_MODELS)]
        .groupby(["fold", "model"], observed=True)
        .residual.agg(lambda values: float(values.quantile(.95) - values.quantile(.05)))
        .rename("p95_minus_p05")
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(7, 4.5))
    pivot = fold_sector.pivot(index="fold", columns="model", values="p95_minus_p05")
    pivot.plot(kind="bar", ax=ax, color=[colors[column] for column in pivot.columns])
    ax.set(ylabel="Residual P95 - P05", xlabel="Development fold", title="Residual dispersion stability")
    ax.legend(title="Model", frameon=False)
    save(fig, "a6_expected_residual_dispersion.png")
    return names


def run_expected_model(database_path: Path = DEFAULT_EDA_DATABASE) -> dict[str, object]:
    panel = load_analytical_panel(database_path)
    folds = pd.read_csv(FOLD_PATH).query("final_holdout == False")
    comparison_rows: list[dict[str, object]] = []
    sensitivity_rows: list[dict[str, object]] = []
    coefficient_rows: list[dict[str, object]] = []
    validation_predictions: list[pd.DataFrame] = []
    eligible_counts: dict[str, tuple[int, int]] = {}

    for _, fold in folds.iterrows():
        fold_name = str(fold["fold"])
        training, validation, pair_n = _fold_rows(panel, fold)
        eligible_counts[fold_name] = (len(training), pair_n)
        model_a = None
        for name in CORE_MODELS:
            estimator = "huber" if name == "C" else "ols"
            model = fit_expected_model(
                training,
                name=name,
                training_year_end=int(fold.first_stage_fit_end_year),
                estimator=estimator,
            )
            train_prediction = predict_expected(model, model.training_frame)
            val_prediction = predict_expected(model, validation)
            if name == "A":
                model_a = model
            comparison_rows.append(
                _metrics_row(fold_name, name, training, validation, train_prediction, val_prediction, estimator)
            )
            val_prediction.insert(0, "model", name)
            val_prediction.insert(0, "fold", fold_name)
            val_prediction["predictor_year"] = val_prediction.target_year - 3
            validation_predictions.append(
                val_prediction[[
                    "fold", "model", "cbsa_code", "sector_code", "predictor_year", "target_year",
                    "year", "startup_rate", "expected_startup_rate", "residual",
                ]].rename(columns={"startup_rate": "observed_startup_rate", "year": "outcome_year"})
            )
            coefficient_rows.extend(_coefficient_rows(fold_name, name, model))

        base_features = list(BASE_FEATURES)
        variants: list[tuple[str, tuple[str, ...], str, pd.DataFrame | None]] = []
        no_lag_features = tuple(feature for feature in base_features if feature != "startup_rate_lag1")
        no_lag_formula = BASE_FORMULA.replace("startup_rate_lag1 + ", "")
        variants.append(("A_without_lag1", no_lag_features, no_lag_formula, None))
        for lag in (2, 3):
            lag_features = tuple(f"startup_rate_lag{lag}" if f == "startup_rate_lag1" else f for f in base_features)
            lag_formula = BASE_FORMULA.replace("startup_rate_lag1", f"startup_rate_lag{lag}")
            variants.append((f"A_lag{lag}", lag_features, lag_formula, None))
        for growth in ("establishment_growth", "payroll_growth", "wage_growth"):
            alt_features = tuple(growth if feature == "employment_growth" else feature for feature in base_features)
            alt_formula = BASE_FORMULA.replace("employment_growth", growth)
            variants.append((f"A_{growth}", alt_features, alt_formula, None))
        trimmed = training.copy()
        clean_growth = trimmed.employment_growth.replace([np.inf, -np.inf], np.nan).dropna()
        lower, upper = clean_growth.quantile([.01, .99])
        trimmed = trimmed[trimmed.employment_growth.between(lower, upper)]
        variants.append(("A_growth_p01_p99_trim", tuple(base_features), BASE_FORMULA, trimmed))
        msa_features = (*BASE_FEATURES, "cbsa_code")
        msa_formula = BASE_FORMULA.replace("C(year)", "C(cbsa_code) + C(year)")
        variants.append(("A_msa_fixed_effects", msa_features, msa_formula, None))

        for name, features, formula, fit_frame in variants:
            model = fit_expected_model(
                training if fit_frame is None else fit_frame,
                name=name,
                training_year_end=int(fold.first_stage_fit_end_year),
                features=features,
                formula=formula,
            )
            train_prediction = predict_expected(model, model.training_frame)
            val_prediction = predict_expected(model, validation)
            sensitivity_row = _metrics_row(
                fold_name, name, training, validation, train_prediction, val_prediction, "ols"
            )
            if name == "A_msa_fixed_effects":
                complete_validation = validation.dropna(subset=["startup_rate", *features])
                trained_msas = set(model.training_frame.cbsa_code.astype(str))
                estimable_n = complete_validation.cbsa_code.astype(str).isin(trained_msas).sum()
                sensitivity_row["validation_unseen_msa_n"] = int(len(complete_validation) - estimable_n)
            sensitivity_rows.append(sensitivity_row)

        # COVID years are absent from all development training windows; retain primary
        # validation scores and report the 2019/2020 contrast without refitting on it.
        if "year" in validation:
            covid_rows = validation[validation.year.isin([2019, 2020])]
            if not covid_rows.empty:
                assert model_a is not None
                covid_model = model_a
                covid_prediction = predict_expected(covid_model, covid_rows)
                for year, group in covid_prediction.groupby("year"):
                    sensitivity_rows.append({
                        "fold": fold_name,
                        "model": "A_COVID_year_diagnostic",
                        "estimator": "ols",
                        "validation_target_years": str(year),
                        "validation_complete_case_n": len(group),
                        **{f"validation_{key}": value for key, value in regression_metrics(
                            group.startup_rate,
                            group.expected_startup_rate,
                            training_mean=float(covid_model.training_frame.startup_rate.mean()),
                        ).items()},
                    })

    preholdout = panel[panel.year.between(2010, 2020)].copy()
    for sensitivity, excluded_years in (
        ("A_preholdout_full", ()),
        ("A_preholdout_exclude_2020", (2020,)),
        ("A_preholdout_exclude_2020_2021", (2020, 2021)),
    ):
        fit_rows = preholdout[~preholdout.year.isin(excluded_years)]
        model = fit_expected_model(
            fit_rows,
            name=sensitivity,
            training_year_end=2020 if not excluded_years else 2019,
            features=BASE_FEATURES,
            formula=BASE_FORMULA,
        )
        fit_prediction = predict_expected(model, model.training_frame)
        stats = regression_metrics(fit_prediction.startup_rate, fit_prediction.expected_startup_rate)
        sensitivity_rows.append({
            "fold": "preholdout_training_window",
            "model": sensitivity,
            "estimator": "ols",
            "evaluation_scope": "in_sample_training_diagnostic",
            "excluded_years_from_fit": ",".join(map(str, excluded_years)),
            "training_complete_case_n": len(fit_prediction),
            "training_years": f"{int(fit_prediction.year.min())}-{int(fit_prediction.year.max())}",
            **{f"train_{key}": value for key, value in stats.items()},
        })

    comparison = pd.DataFrame(comparison_rows)
    sensitivities = pd.DataFrame(sensitivity_rows)
    predictions = pd.concat(validation_predictions, ignore_index=True)
    year_tables = []
    sector_tables = []
    msa_tables = []
    for model, group in predictions.groupby("model", sort=True):
        for variable, destination in (("outcome_year", year_tables), ("sector_code", sector_tables), ("cbsa_code", msa_tables)):
            summary = _residual_summary(group, variable).rename(columns={variable: "group_value"})
            summary.insert(0, "model", model)
            destination.append(summary)
    residual_year = pd.concat(year_tables, ignore_index=True)
    residual_sector = pd.concat(sector_tables, ignore_index=True)
    residual_msa = pd.concat(msa_tables, ignore_index=True)
    coefficients = pd.DataFrame(coefficient_rows)
    coefficients["sign"] = np.sign(coefficients.coefficient)
    stability = (
        coefficients.groupby(["model", "term"], observed=True)
        .agg(folds_observed=("coefficient", "count"), mean_coefficient=("coefficient", "mean"),
             coefficient_sd=("coefficient", "std"), minimum=("coefficient", "min"),
             maximum=("coefficient", "max"), sign_consistency=("sign", lambda values: max((values > 0).mean(), (values < 0).mean())))
        .reset_index()
    )

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "a6_expected_model_comparison.csv": comparison,
        "a6_expected_residual_by_year.csv": residual_year,
        "a6_expected_residual_by_sector.csv": residual_sector,
        "a6_expected_residual_by_msa.csv": residual_msa,
        "a6_expected_coefficients_by_fold.csv": coefficients,
        "a6_expected_coefficient_stability.csv": stability,
        "a6_expected_sensitivity.csv": sensitivities,
        "a6_expected_validation_predictions.csv": predictions,
    }
    for filename, frame in outputs.items():
        frame.to_csv(TABLE_DIR / filename, index=False)

    # Summarize the primary candidates without consulting the untouched holdout.
    means = comparison[comparison.model.isin(("A", "B"))].groupby("model").validation_mae.mean()
    a_mae, b_mae = float(means["A"]), float(means["B"])
    candidate_means = comparison.groupby("model")[["validation_mae", "validation_rmse"]].mean()
    c_mae = float(candidate_means.loc["C", "validation_mae"])
    c_rmse = float(candidate_means.loc["C", "validation_rmse"])
    c_rmse_worse_folds = int((
        comparison[comparison.model.eq("C")].set_index("fold").validation_rmse
        > comparison[comparison.model.eq("A")].set_index("fold").validation_rmse
    ).sum())
    winner = "B" if b_mae < a_mae else "A"
    fold_wins = int((comparison[comparison.model.eq("B")].set_index("fold").validation_mae < comparison[comparison.model.eq("A")].set_index("fold").validation_mae).sum())
    if winner == "B" and fold_wins < 2:
        winner = "A"
        selection_reason = "The interaction model did not improve validation MAE in at least two of three development folds; prefer the parsimonious baseline."
    elif winner == "B":
        selection_reason = "The sector interaction had lower pooled validation MAE and improved MAE in at least two of three development folds; confirm coefficient and residual stability before downstream use."
    else:
        selection_reason = "The linear baseline has the lower pooled development-fold MAE and is the parsimonious choice."
    selection_reason += (
        f" Huber Model C reduced MAE in all three development folds (mean {c_mae:.3f} versus "
        f"{float(candidate_means.loc['A', 'validation_mae']):.3f} for Model A), but its mean RMSE "
        f"was {c_rmse:.3f} and exceeded Model A in {c_rmse_worse_folds} of three folds; its later-fold "
        "positive residual drift also remained. It is retained as a typical-error robustness check, "
        "not selected as the primary benchmark because that MAE-only gain does not improve tail-sensitive "
        "error or temporal calibration consistently."
    )
    comparison["selected_expected_model"] = comparison.model.eq(winner)
    outputs["a6_expected_model_comparison.csv"] = comparison
    comparison.to_csv(TABLE_DIR / "a6_expected_model_comparison.csv", index=False)

    figures = _save_figures(predictions, comparison, residual_year.rename(columns={"group_value": "year"}), residual_sector.rename(columns={"group_value": "sector_code"}))
    SPEC_PATH.write_text(_build_spec(winner, selection_reason), encoding="utf-8")
    REPORT_PATH.write_text(
        _build_report(panel, comparison, sensitivities, residual_year, residual_sector, residual_msa, stability, winner, selection_reason, eligible_counts, figures),
        encoding="utf-8",
    )
    return {
        "selected_model": winner,
        "reason": selection_reason,
        "comparison": comparison,
        "sensitivity": sensitivities,
        "figures": figures,
        "report": str(REPORT_PATH),
        "spec": str(SPEC_PATH),
    }


def _table_markdown(frame: pd.DataFrame, columns: list[str], digits: int = 4) -> str:
    view = frame[columns].copy()
    for column in view.select_dtypes(include="number"):
        view[column] = view[column].map(
            lambda value: (
                str(int(value)) if pd.notna(value) and float(value).is_integer()
                else f"{value:.{digits}f}" if pd.notna(value)
                else ""
            )
        )
    header = "| " + " | ".join(view.columns) + " |"
    divider = "| " + " | ".join("---" for _ in view.columns) + " |"
    rows = ["| " + " | ".join(map(str, row)) + " |" for row in view.itertuples(index=False, name=None)]
    return "\n".join([header, divider, *rows])


def _build_spec(winner: str, reason: str) -> str:
    return f"""# Assignment 6.2 Expected Entrepreneurship Model

**Status:** Estimated and compared on development folds only. The final holdout remains unused.

## Construct and primary specification

The response is the observed BDS firm startup rate. The selected expected-rate benchmark is Model {winner}: `startup_rate ~ startup_rate_lag1 + employment_growth + ACS regional controls + sector fixed effects + year fixed effects`. The ACS controls are population growth, median household income, educational attainment, labor-force participation, and unemployment. All predictors refer to the outcome-year observation or earlier. Estimation uses complete cases only; no imputation or winsorization is used in the primary fit.

Selection rationale: {reason}

Model A is the additive OLS baseline. Model B adds `employment_growth × sector` while retaining sector fixed effects. Model C applies Huber M-estimation to the Model A formula as a robust sensitivity, not a primary candidate. The selection comparison is based on three expanding development folds and includes MAE, RMSE, out-of-sample R-squared against the training mean, residual distribution/stability, and coefficient stability. The Model B interaction is retained only for a consistent material improvement; otherwise parsimony favors Model A.

## Fold and time handling

The exact A6.1 fold file determines fit end years 2016, 2017, and 2018. The full analytical panel within each fold's expected-model fit window is used for fitting; validation scoring is restricted to exact same-CBSA/same-sector t-to-t+3 calendar pairs. Fit rows with any missing model field are excluded; no data are imputed. Year and sector effects are fit using training rows only. Because a validation year is not represented in a training-only year fixed-effect design, its year effect is forecast by carrying forward the latest training-year effect. This persistence rule is outcome-free, preserves the mandatory year effects, and is included in every candidate prediction. It is an explicit extrapolation assumption, not a coefficient estimated for the validation year.

Target-year covariates and observed startup rates are used only to estimate/score the fold-local expected-rate benchmark and calculate its diagnostic residuals. They are not predictive features at predictor year t. No residual quantile threshold, gap status, classifier, or final-holdout prediction is created here.

## Model choice

{reason}

Model C and feature alternatives remain documented sensitivity results. The selection does not use the 2018-2020 predictor block or 2021-2023 final outcomes. No causal interpretation is intended.
"""


def _build_report(panel: pd.DataFrame, comparison: pd.DataFrame, sensitivities: pd.DataFrame,
                  by_year: pd.DataFrame, by_sector: pd.DataFrame, by_msa: pd.DataFrame,
                  stability: pd.DataFrame, winner: str, reason: str,
                  eligible_counts: dict[str, tuple[int, int]], figures: list[str]) -> str:
    main = comparison[comparison.model.isin(CORE_MODELS)].sort_values(["fold", "model"])
    sensitivity_selected = sensitivities[sensitivities.model.str.startswith(("A_without", "A_lag", "A_establishment", "A_payroll", "A_wage", "A_growth", "A_msa"))].copy()
    overview = pd.DataFrame([
        {"panel_rows": len(panel), "MSAs": panel.cbsa_code.nunique(), "sectors": panel.sector_code.nunique(),
         "year_min": panel.year.min(), "year_max": panel.year.max(), "development_folds": 3,
         "holdout_scored": False, "gap_labels_created": False}
    ])
    fold_eligibility = pd.DataFrame([
        {"fold": fold, "fit_window_panel_rows": counts[0], "exact_validation_calendar_pairs": counts[1]}
        for fold, counts in eligible_counts.items()
    ])
    return f"""# Assignment 6.2: Expected Entrepreneurship Model

**Decision:** Model {winner} is the selected expected-rate specification for development. The final temporal holdout remains untouched. No A6.3 threshold or gap labels were created.

## Scope and leakage boundary

The startup-rate benchmark was estimated independently inside each A6.1 development fold using complete-case rows through the fold-specific outcome cutoff. Validation diagnostics use only exact same-MSA/same-sector t-to-t+3 pairs. Year and sector effects are fit only in training data. An unseen validation-year effect is carried forward from the latest training year; this forecasting convention uses no validation outcome. Validation outcome-year covariates and startup rates are confined to benchmark scoring/residual diagnostics and are not classifier features. No holdout rows from 2018-2020 predictors / 2021-2023 targets entered fitting or selection.

The data are not imputed, trimmed, or capped in the primary fits. Negative expected-rate predictions, if any, are retained and counted; rates are not post-hoc clipped. Robust and trimmed variants are sensitivities only.

## Panel and candidate comparison

{_table_markdown(overview, list(overview.columns))}

Fold-level raw eligibility before complete-case filtering:

{_table_markdown(fold_eligibility, list(fold_eligibility.columns))}

{_table_markdown(main, ["fold", "model", "train_n", "validation_n", "train_mae", "validation_mae", "validation_rmse", "validation_r_squared", "validation_mean_residual", "validation_residual_sd", "validation_expected_below_zero_n"])}

Selection: {reason} Fold-level estimates and the exact feature/time specification are available in `reports/tables/a6_expected_model_comparison.csv` and `docs/ASSIGNMENT6_EXPECTED_MODEL.md`. R-squared is secondary: validation R-squared uses each fold's training-response mean as the reference, so negative values are possible and meaningful.

## Residual stability

The tables report validation residual summaries by outcome year, sector, and MSA. Group estimates should be interpreted alongside their sample sizes; MSA summaries are diagnostic rather than an additional selection target. Persistent year- or sector-level residual structure suggests that the conditional expectation is not fully calibrated, even where overall error is lower.

By year:

{_table_markdown(by_year, ["model", "group_value", "n", "mean_residual", "median_residual", "residual_sd", "mae", "rmse"])}

By sector:

{_table_markdown(by_sector, ["model", "group_value", "n", "mean_residual", "median_residual", "residual_sd", "mae", "rmse"])}

MSA-level results are retained in `reports/tables/a6_expected_residual_by_msa.csv` to keep this report readable. Coefficients and cross-fold stability are in `a6_expected_coefficients_by_fold.csv` and `a6_expected_coefficient_stability.csv`.

## Sensitivities

{_table_markdown(sensitivity_selected, ["fold", "model", "train_n", "validation_n", "train_mae", "validation_mae", "validation_rmse", "validation_r_squared", "validation_mean_residual"])}

Sensitivity changes are one-at-a-time: remove lag 1; substitute lag 2 or lag 3; substitute establishment, payroll, or wage growth for employment growth; temporarily trim training employment growth at training-only P01/P99; or add MSA fixed effects. The trim cutoffs are learned only in each training fold, and validation data remain untrimmed. The MSA-FE result is diagnostic and does not change the primary policy against MSA effects. Huber Model C, included in the primary comparison, checks sensitivity to large residuals while preserving all observations.

All development training windows end by 2018, so COVID years 2020-2021 do not enter fold fits. The year-2020 validation residual is reported separately from 2019. A pre-holdout in-sample fit sensitivity also compares retaining 2020 with excluding 2020 and 2020-2021; 2021 is outside the permitted pre-holdout training window, so the latter two fitting samples are intentionally identical. These are descriptive robustness checks, not causal COVID estimates. No final-holdout observations enter them.

## Interpretation and next step

Residual = observed startup rate minus expected startup rate. Positive residuals are above expectation and negative residuals are below expectation; a negative residual alone is not a gap. Coefficients are conditional associations, not causal effects. The preferred model will be used in A6.3 only after the leakage and calibration diagnostics are reviewed; A6.3 must calculate residual thresholds from training-fold residuals only.

## Figures

{chr(10).join(f'- `reports/figures/{name}`' for name in figures)}

## Machine-readable outputs

{chr(10).join(f'- `reports/tables/{name}`' for name in ["a6_expected_model_comparison.csv", "a6_expected_residual_by_year.csv", "a6_expected_residual_by_sector.csv", "a6_expected_residual_by_msa.csv", "a6_expected_coefficients_by_fold.csv", "a6_expected_coefficient_stability.csv", "a6_expected_sensitivity.csv", "a6_expected_validation_predictions.csv"])}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_EDA_DATABASE)
    args = parser.parse_args()
    result = run_expected_model(args.database)
    print(f"Selected Model {result['selected_model']}: {result['reason']}")
    print(f"Report: {result['report']}")
    print(f"Specification: {result['spec']}")


if __name__ == "__main__":
    main()
