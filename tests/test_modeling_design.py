from __future__ import annotations

import unittest
from dataclasses import replace

import pandas as pd

from regional_entrepreneurship_intelligence.models.design import validate_modeling_design
from regional_entrepreneurship_intelligence.models.features import (
    FEATURE_REGISTRY,
    PROHIBITED_FEATURES,
    validate_feature_timing,
    validate_feature_years,
)
from regional_entrepreneurship_intelligence.models.temporal import (
    build_temporal_pairs,
    generate_temporal_fold_spec,
    latest_targetable_predictor_year,
    validate_msa_only,
    validate_prediction_horizon,
    validate_temporal_folds,
)


class ModelingDesignTest(unittest.TestCase):
    def test_exact_t3_pairs_exclude_nonconsecutive_available_observations(self) -> None:
        keys = pd.DataFrame(
            {
                "cbsa_code": ["001", "001", "001", "002", "002"],
                "sector_code": ["11"] * 5,
                "year": [2015, 2017, 2018, 2015, 2019],
            }
        )
        pairs = build_temporal_pairs(keys)
        self.assertEqual(pairs[["cbsa_code", "predictor_year", "target_year"]].values.tolist(), [["001", 2015, 2018]])
        self.assertEqual(list(pairs.columns), ["cbsa_code", "sector_code", "predictor_year", "target_year"])
        with self.assertRaises(ValueError):
            validate_prediction_horizon(2015, 2019)
        validate_prediction_horizon(2015, 2018)

    def test_fold_ranges_keep_outcomes_before_validation_and_holdout_is_last(self) -> None:
        keys = pd.DataFrame(
            [("001", "11", year) for year in range(2010, 2024)],
            columns=["cbsa_code", "sector_code", "year"],
        )
        folds = generate_temporal_fold_spec(keys)
        validate_temporal_folds(folds)
        self.assertTrue(folds[-1].final_holdout)
        self.assertEqual(folds[-1].validation_predictor_start_year, 2018)
        self.assertEqual(folds[-1].validation_predictor_end_year, 2020)
        self.assertEqual(folds[-1].validation_target_start_year, 2021)
        self.assertEqual(folds[-1].validation_target_end_year, 2023)
        self.assertLess(folds[-2].validation_target_end_year, folds[-1].validation_target_start_year)
        for fold in folds:
            self.assertLess(fold.train_outcome_end_year, fold.validation_target_start_year)
            self.assertEqual(fold.eligible_train_pairs, fold.train_predictor_end_year - fold.train_predictor_start_year + 1)
        invalid = (replace(folds[0], train_outcome_end_year=2017), *folds[1:])
        with self.assertRaises(ValueError):
            validate_temporal_folds(invalid)

    def test_latest_targetable_year_and_actual_fold_pair_counts(self) -> None:
        self.assertEqual(latest_targetable_predictor_year(2023), 2020)
        design = validate_modeling_design()
        self.assertEqual(design["primary_gap_quantile"], 0.20)
        self.assertEqual(design["gap_threshold_scope"], "training_fold_only")

    def test_feature_registry_rejects_future_and_unknown_predictors(self) -> None:
        names = tuple(row["variable"] for row in FEATURE_REGISTRY)
        validate_feature_timing(names)
        self.assertTrue(PROHIBITED_FEATURES)
        with self.assertRaises(ValueError):
            validate_feature_timing(["startup_rate", "gap_status_t_plus_3"])
        with self.assertRaises(ValueError):
            validate_feature_timing(["invented_predictor"])
        validate_feature_years({"startup_rate": 2014, "employment_growth": 2013}, 2014)
        with self.assertRaises(ValueError):
            validate_feature_years({"future_acs": 2015}, 2014)

    def test_micropolitan_scope_is_rejected(self) -> None:
        validate_msa_only(["MSA", "MSA"])
        with self.assertRaises(ValueError):
            validate_msa_only(["MSA", "Micropolitan"])


if __name__ == "__main__":
    unittest.main()
