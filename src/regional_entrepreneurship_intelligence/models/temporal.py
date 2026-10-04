"""Calendar-exact temporal-fold specification helpers; no outcomes are fit."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pandas as pd

from regional_entrepreneurship_intelligence.models.design import PREDICTION_HORIZON_YEARS


@dataclass(frozen=True)
class TemporalFold:
    name: str
    train_predictor_start_year: int
    train_predictor_end_year: int
    train_outcome_start_year: int
    train_outcome_end_year: int
    validation_predictor_start_year: int
    validation_predictor_end_year: int
    validation_target_start_year: int
    validation_target_end_year: int
    final_holdout: bool = False
    eligible_train_pairs: int | None = None
    eligible_validation_pairs: int | None = None

    @property
    def expected_model_fit_start_year(self) -> int:
        return self.train_predictor_start_year

    @property
    def expected_model_fit_end_year(self) -> int:
        return self.train_outcome_end_year


FOLD_TEMPLATES = (
    TemporalFold("fold_1", 2010, 2013, 2013, 2016, 2014, 2014, 2017, 2017),
    TemporalFold("fold_2", 2010, 2014, 2013, 2017, 2015, 2015, 2018, 2018),
    TemporalFold("fold_3", 2010, 2015, 2013, 2018, 2016, 2017, 2019, 2020),
    TemporalFold("final_holdout", 2010, 2017, 2013, 2020, 2018, 2020, 2021, 2023, True),
)


def validate_prediction_horizon(
    predictor_year: int, target_year: int, horizon: int = PREDICTION_HORIZON_YEARS
) -> None:
    if target_year != predictor_year + horizon:
        raise ValueError(
            f"Expected exact t+{horizon} target; received {predictor_year}->{target_year}"
        )


def build_temporal_pairs(
    panel_keys: pd.DataFrame,
    *,
    key_columns: tuple[str, ...] = ("cbsa_code", "sector_code"),
    year_column: str = "year",
    horizon: int = PREDICTION_HORIZON_YEARS,
) -> pd.DataFrame:
    """Return only exact-calendar key/year pairs, never outcome values or labels."""
    required = {*key_columns, year_column}
    absent = sorted(required - set(panel_keys.columns))
    if absent:
        raise ValueError(f"Panel keys are missing required fields: {absent}")
    keys = panel_keys[list(key_columns) + [year_column]].copy()
    if horizon < 1:
        raise ValueError("Prediction horizon must be a positive number of calendar years")
    if keys.duplicated(list(key_columns) + [year_column]).any():
        raise ValueError("Duplicate MSA-sector-year keys cannot define temporal pairs")
    predictors = keys.rename(columns={year_column: "predictor_year"})
    predictors["target_year"] = predictors.predictor_year + horizon
    outcomes = keys.rename(columns={year_column: "target_year"})
    pairs = predictors.merge(
        outcomes,
        on=[*key_columns, "target_year"],
        how="inner",
        validate="one_to_one",
    )
    return pairs[[*key_columns, "predictor_year", "target_year"]].sort_values(
        [*key_columns, "predictor_year"]
    ).reset_index(drop=True)


def validate_temporal_folds(folds: tuple[TemporalFold, ...]) -> None:
    if not folds or not folds[-1].final_holdout:
        raise ValueError("The final fold must be an explicitly reserved holdout")
    holdouts = [fold for fold in folds if fold.final_holdout]
    if len(holdouts) != 1:
        raise ValueError("Exactly one final holdout is required")
    previous_validation_target_end = None
    for fold in folds:
        if fold.train_predictor_start_year > fold.train_predictor_end_year:
            raise ValueError(f"Invalid training predictor range in {fold.name}")
        if fold.train_predictor_end_year >= fold.validation_predictor_start_year:
            raise ValueError(f"Training predictors overlap validation predictor time in {fold.name}")
        if fold.validation_predictor_start_year > fold.validation_predictor_end_year:
            raise ValueError(f"Invalid validation predictor range in {fold.name}")
        validate_prediction_horizon(fold.validation_predictor_start_year, fold.validation_target_start_year)
        validate_prediction_horizon(fold.validation_predictor_end_year, fold.validation_target_end_year)
        if fold.train_outcome_end_year >= fold.validation_target_start_year:
            raise ValueError(f"Training outcomes overlap validation target time in {fold.name}")
        if fold.train_outcome_start_year > fold.train_outcome_end_year:
            raise ValueError(f"Invalid training outcome range in {fold.name}")
        if fold.train_outcome_start_year != fold.train_predictor_start_year + PREDICTION_HORIZON_YEARS:
            raise ValueError(f"Training outcome range does not follow exact horizon in {fold.name}")
        if fold.train_outcome_end_year != fold.train_predictor_end_year + PREDICTION_HORIZON_YEARS:
            raise ValueError(f"Training outcome range does not follow exact horizon in {fold.name}")
        if previous_validation_target_end is not None:
            if fold.validation_target_start_year <= previous_validation_target_end:
                raise ValueError("Development validation target periods must advance without overlap")
        if not fold.final_holdout:
            previous_validation_target_end = fold.validation_target_end_year
    if folds[-1].train_outcome_end_year >= folds[-1].validation_target_start_year:
        raise ValueError("Final holdout outcome years overlap training outcome years")


def generate_temporal_fold_spec(
    panel_keys: pd.DataFrame | None = None,
) -> tuple[TemporalFold, ...]:
    """Return the frozen expanding folds, optionally attaching key-pair counts."""
    validate_temporal_folds(FOLD_TEMPLATES)
    if panel_keys is None:
        return FOLD_TEMPLATES
    pairs = build_temporal_pairs(panel_keys)
    enriched = []
    for fold in FOLD_TEMPLATES:
        training = pairs.predictor_year.between(
            fold.train_predictor_start_year, fold.train_predictor_end_year
        )
        validation = pairs.predictor_year.between(
            fold.validation_predictor_start_year, fold.validation_predictor_end_year
        )
        enriched.append(
            replace(
                fold,
                eligible_train_pairs=int(training.sum()),
                eligible_validation_pairs=int(validation.sum()),
            )
        )
    return tuple(enriched)


def latest_targetable_predictor_year(max_observed_year: int, horizon: int = PREDICTION_HORIZON_YEARS) -> int:
    return max_observed_year - horizon


def validate_msa_only(geography_types: list[str] | tuple[str, ...]) -> None:
    unexpected = sorted({str(value) for value in geography_types if value != "MSA"})
    if unexpected:
        raise ValueError(f"A6 primary design requires MSA-only geography; found {unexpected}")
