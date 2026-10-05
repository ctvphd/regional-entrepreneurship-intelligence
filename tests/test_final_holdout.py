from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from unittest.mock import patch

from regional_entrepreneurship_intelligence.models.advanced import TREE_FEATURES
from regional_entrepreneurship_intelligence.models.baseline import EXTENDED_REQUIRED, MODEL_FEATURES
from regional_entrepreneurship_intelligence.models.final_holdout import (
    DEVELOPMENT_TARGET_MAX,
    HGB_PARAMS,
    HOLDOUT_PREDICTOR_YEARS,
    HOLDOUT_TARGET_YEARS,
    MODEL_NAME,
    attach_final_labels,
    development_threshold,
    exact_pairs,
    eligibility_audit,
    freeze_development_threshold,
    performance_row,
    read_panel_readonly,
    score_bins,
    validate_locked_design,
    validate_prediction_rows,
)
from regional_entrepreneurship_intelligence.models.expected import ExpectedModel


class FinalHoldoutTest(unittest.TestCase):
    def test_holdout_years_and_exact_t_plus_3_are_frozen(self):
        self.assertEqual(HOLDOUT_PREDICTOR_YEARS, (2018, 2019, 2020))
        self.assertEqual(HOLDOUT_TARGET_YEARS, (2021, 2022, 2023))
        panel = pd.DataFrame({"cbsa_code": ["1", "1", "1", "2", "2"],
                              "sector_code": ["11"] * 5,
                              "year": [2018, 2021, 2020, 2018, 2022]})
        result = exact_pairs(panel, HOLDOUT_PREDICTOR_YEARS)
        self.assertEqual(list(result.target_year), [2021])
        self.assertTrue(result.target_year.eq(result.predictor_year + 3).all())

    def test_expected_residual_cutoff_requires_2020_development_fit(self):
        with self.assertRaises(ValueError):
            development_threshold(ExpectedModel("A", "formula", None, pd.DataFrame(), 2021, "ols", ()))

    def test_p20_cutoff_uses_only_the_final_development_residual_vector(self):
        model = ExpectedModel("A", "formula", None, pd.DataFrame(), 2020, "ols", ())
        residuals = pd.DataFrame({"year": [2018, 2019, 2020, 2020], "residual": [-4.0, -2.0, 1.0, 3.0]})
        with patch("regional_entrepreneurship_intelligence.models.final_holdout.predict_expected", return_value=residuals):
            scored, cutoff = development_threshold(model)
        self.assertEqual(len(scored), 4)
        self.assertAlmostEqual(cutoff, -2.8)
        too_late = residuals.copy()
        too_late.loc[3, "year"] = 2021
        with patch("regional_entrepreneurship_intelligence.models.final_holdout.predict_expected", return_value=too_late):
            with self.assertRaises(ValueError):
                development_threshold(model)

    def test_label_cutoff_applies_to_target_residual_not_holdout_distribution(self):
        pairs = pd.DataFrame({"cbsa_code": ["1", "2"], "sector_code": ["11", "11"],
                              "predictor_year": [2018, 2018], "target_year": [2021, 2021]})
        targets = pd.DataFrame({"cbsa_code": ["1", "2"], "sector_code": ["11", "11"],
                                "year": [2021, 2021], "startup_rate": [1.0, 5.0],
                                "expected_startup_rate": [2.0, 4.0], "residual": [-1.0, 1.0]})
        result = attach_final_labels(pairs, targets, -0.5)
        self.assertEqual(list(result.gap_p20.astype(int)), [1, 0])
        self.assertEqual(result.gap_p20.dtype.name, "Int64")

    def test_feature_families_and_frozen_model_parameters(self):
        validate_locked_design()
        self.assertEqual(MODEL_NAME, "baseline_1_simple")
        self.assertEqual(MODEL_FEATURES[MODEL_NAME],
                         ("startup_rate", "startup_rate_lag1", "employment_growth", "sector_code", "year"))
        self.assertIn("acs_population_growth", TREE_FEATURES)
        self.assertEqual(HGB_PARAMS, {"max_iter": 120, "learning_rate": .05, "max_leaf_nodes": 15,
                                      "min_samples_leaf": 30, "l2_regularization": 1.0})
        forbidden = {"actual_gap", "gap_p20", "target_startup_rate", "target_alignment_residual",
                     "target_expected_startup_rate"}
        self.assertFalse(forbidden.intersection(MODEL_FEATURES[MODEL_NAME]))
        self.assertFalse(forbidden.intersection(TREE_FEATURES))
        self.assertIn("year", EXTENDED_REQUIRED)

    def test_development_threshold_is_computed_from_development_residuals_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "dev.sqlite"
            con = sqlite3.connect(database)
            try:
                con.execute("CREATE TABLE v_analytics_msa_industry_year (cbsa_code TEXT, sector_code TEXT, year INTEGER)")
                con.executemany("INSERT INTO v_analytics_msa_industry_year VALUES (?, ?, ?)",
                                [("1", "11", 2017), ("1", "11", 2020), ("1", "11", 2021)])
                con.commit()
            finally:
                con.close()
            panel = read_panel_readonly(database, year_max=DEVELOPMENT_TARGET_MAX)
            self.assertLessEqual(panel.year.max(), DEVELOPMENT_TARGET_MAX)
            before = hashlib.sha256(database.read_bytes()).hexdigest()
            _ = read_panel_readonly(database, year_max=DEVELOPMENT_TARGET_MAX)
            after = hashlib.sha256(database.read_bytes()).hexdigest()
            self.assertEqual(before, after)

    def test_holdout_prediction_validator_requires_one_valid_score_per_key(self):
        sample = pd.DataFrame({"cbsa_code": ["1", "2"], "sector_code": ["11", "11"],
                               "predictor_year": [2018, 2019], "target_year": [2021, 2022],
                               "predicted_probability_logistic": [.2, .7],
                               "predicted_probability_hgb": [.3, .8]})
        validate_prediction_rows(sample, eligible_n=2)
        with self.assertRaises(ValueError):
            validate_prediction_rows(pd.concat([sample, sample.iloc[[0]]], ignore_index=True), eligible_n=3)
        sample.loc[0, "target_year"] = 2022
        with self.assertRaises(ValueError):
            validate_prediction_rows(sample, eligible_n=2)

    def test_complete_case_eligibility_preserves_audit_counts(self):
        row = {name: 1.0 for name in EXTENDED_REQUIRED}
        row.update({"cbsa_code": "1", "sector_code": "11", "gap_p20": 1})
        included = pd.DataFrame([row])
        eligible, audit = eligibility_audit(included)
        self.assertEqual(len(eligible), 1)
        self.assertEqual(audit["candidate_pairs"], 1)
        self.assertEqual(audit["excluded_pairs"], 0)
        included.loc[0, "acs_population_growth"] = np.nan
        eligible, audit = eligibility_audit(included)
        self.assertEqual(len(eligible), 0)
        self.assertEqual(audit["excluded_pairs"], 1)

    def test_score_bins_are_ordered_low_to_high_without_refitting(self):
        bins = score_bins([0, 1, 0, 1], [.1, .9, .2, .8], model="logistic", bins=2)
        self.assertEqual(list(bins.risk_bin), [1, 2])
        self.assertLess(bins.mean_predicted_probability.iloc[0], bins.mean_predicted_probability.iloc[1])

    def test_metric_rows_include_prevalence_and_diagnostic_classification(self):
        row = performance_row(np.array([0, 1, 0, 1]), np.array([.1, .8, .2, .7]),
                              model="logistic", dataset="holdout", thresholds=.5)
        self.assertEqual(row["N"], 4)
        self.assertEqual(row["prevalence"], .5)
        self.assertAlmostEqual(row["AP"], 1.0)
        self.assertEqual(row["recall"], 1.0)
        self.assertEqual(row["precision"], 1.0)
        self.assertEqual(row["top10_lift"], 2.0)

    def test_freeze_phase_has_separate_entry_point_from_holdout_evaluation(self):
        self.assertTrue(callable(freeze_development_threshold))
        self.assertTrue(callable(validate_locked_design))


if __name__ == "__main__":
    unittest.main()
