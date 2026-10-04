from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.models.advanced import (
    ABLATIONS,
    TREE_FEATURES,
    feature_ablation,
    fit_advanced_model,
    make_inner_temporal_split,
    predict_gap_probability,
    validate_advanced_oof,
    validate_tree_features,
)


class AdvancedModelsTest(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(41)
        n = 240
        x = rng.normal(size=n)
        frame = pd.DataFrame({
            "startup_rate": x,
            "startup_rate_lag1": rng.normal(size=n),
            "employment_growth": rng.normal(size=n),
            "acs_population_growth": rng.normal(size=n),
            "median_household_income": rng.normal(60000, 5000, n),
            "educational_attainment_pct": rng.normal(30, 4, n),
            "labor_force_participation_pct": rng.normal(63, 3, n),
            "unemployment_rate": rng.normal(5, 1, n),
            "sector_code": np.where(np.arange(n) % 2, "11", "21"),
            "year": np.repeat(np.arange(2010, 2016), 40),
            "predictor_year": np.repeat(np.arange(2010, 2016), 40),
        })
        frame["target_year"] = frame.predictor_year + 3
        frame["gap_p20"] = (x > 0).astype(int)
        self.frame = frame

    def test_inner_split_is_strictly_forward(self):
        split = make_inner_temporal_split(self.frame)
        self.assertEqual(split.predictor_cutoff, 2015)
        self.assertLess(split.fit.predictor_year.max(), split.validation.predictor_year.min())
        self.assertLess(split.fit.target_year.max(), split.validation.target_year.min())

    def test_full_model_features_are_registered_and_future_fields_rejected(self):
        validate_tree_features(TREE_FEATURES)
        with self.assertRaises(ValueError):
            validate_tree_features((*TREE_FEATURES, "gap_p20"))
        with self.assertRaises(ValueError):
            validate_tree_features((*TREE_FEATURES, "startup_rate_t_plus_3"))

    def test_preprocessing_fits_on_training_rows_and_scores_without_labels(self):
        train = self.frame.iloc[:160].copy()
        validation = self.frame.iloc[160:].copy()
        validation.loc[:, "median_household_income"] = 1_000_000
        fitted = fit_advanced_model(
            train,
            model_name="random_forest",
            params={"n_estimators": 20, "max_depth": 3, "min_samples_leaf": 5, "max_features": "sqrt"},
        )
        numeric_scaler = fitted.named_steps["preprocess"].named_transformers_["numeric"]
        self.assertAlmostEqual(numeric_scaler.mean_[TREE_FEATURES.index("median_household_income")],
                               train.median_household_income.mean())
        probabilities = predict_gap_probability(fitted, validation)
        self.assertEqual(len(probabilities), len(validation))
        self.assertTrue(np.isfinite(probabilities).all())
        self.assertTrue(((probabilities >= 0) & (probabilities <= 1)).all())
        before = train.gap_p20.copy()
        validation["gap_p20"] = 1 - validation.gap_p20
        np.testing.assert_array_equal(train.gap_p20, before)
        self.assertIsNone(fitted.named_steps["classifier"].class_weight)

    def test_ablations_are_non_mutating_and_remove_only_declared_features(self):
        original = self.frame.copy(deep=True)
        reduced = feature_ablation("random_forest", TREE_FEATURES, ABLATIONS["no_acs_controls"])
        self.assertTrue(set(ABLATIONS["no_acs_controls"]).isdisjoint(reduced))
        pd.testing.assert_frame_equal(self.frame, original)

    def test_oof_validator_enforces_exact_horizon_and_development_cutoff(self):
        valid = pd.DataFrame({
            "fold": ["fold_1"], "cbsa_code": ["10180"], "sector_code": ["11"],
            "predictor_year": [2014], "target_year": [2017], "actual_gap": [1],
        })
        validate_advanced_oof(valid)
        with self.assertRaisesRegex(ValueError, "holdout boundary"):
            validate_advanced_oof(valid.assign(predictor_year=2018, target_year=2021))
        with self.assertRaisesRegex(ValueError, "unique"):
            validate_advanced_oof(pd.concat([valid, valid], ignore_index=True))


if __name__ == "__main__":
    unittest.main()
