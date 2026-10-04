from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.models.baseline import (
    MODEL_FEATURES,
    build_predictor_pairs,
    calibration_table,
    complete_predictor_sample,
    fit_logistic_baseline,
    fit_prevalence_baseline,
    lift_table,
    predict_gap_probability,
    probability_metrics,
    validate_oof_predictions,
)
from regional_entrepreneurship_intelligence.models.run_baseline import _load_predictor_panel


class BaselineModelTest(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(19)
        n = 120
        startup = rng.normal(6, 2, n)
        lag = rng.normal(6, 2, n)
        growth = rng.normal(0.02, 0.04, n)
        year = np.tile(np.arange(2010, 2016), n // 6)
        sector = np.where(np.arange(n) % 2, "11", "21")
        probability = 1 / (1 + np.exp(-(-1.5 + 0.3 * (startup - 6) + 0.2 * (lag - 6))))
        target = rng.binomial(1, probability)
        self.frame = pd.DataFrame({
            "startup_rate": startup, "startup_rate_lag1": lag, "employment_growth": growth,
            "acs_population_growth": rng.normal(0.01, 0.02, n),
            "median_household_income": rng.normal(60000, 8000, n),
            "educational_attainment_pct": rng.normal(30, 5, n),
            "labor_force_participation_pct": rng.normal(63, 3, n),
            "unemployment_rate": rng.normal(5, 2, n),
            "year": year, "sector_code": sector, "gap_p20": target,
        })
        self.train = self.frame.iloc[:90].copy()
        self.validation = self.frame.iloc[90:].copy()

    def test_prevalence_uses_training_labels_only_and_preserves_natural_rate(self) -> None:
        prevalence = fit_prevalence_baseline(self.train.gap_p20)
        self.assertAlmostEqual(prevalence, self.train.gap_p20.mean())
        self.assertNotEqual(prevalence, self.validation.gap_p20.mean())

    def test_feature_registry_is_predictor_year_only_and_excludes_target_fields(self) -> None:
        targets = pd.DataFrame({"cbsa_code": ["10180"], "sector_code": ["11"], "predictor_year": [2014],
                                "target_year": [2017], "gap_p20": [1], "alignment_residual": [-2.0]})
        panel = pd.DataFrame({
            "cbsa_code": [10180, 10180], "sector_code": ["11", "11"], "year": [2014, 2017],
            "startup_rate": [6.0, 99.0], "startup_rate_lag1": [5.0, 98.0], "employment_growth": [.02, 99.0],
            "acs_population": [200000, 999999], "acs_population_growth": [.01, 99.0],
            "median_household_income": [60000, 999999], "educational_attainment_pct": [30, 99],
            "labor_force_participation_pct": [63, 99], "unemployment_rate": [5, 99],
        })
        paired = build_predictor_pairs(targets, panel)
        self.assertEqual(paired.loc[0, "year"], 2014)
        self.assertEqual(paired.loc[0, "startup_rate"], 6.0)
        self.assertEqual(paired.loc[0, "target_year"], 2017)
        self.assertEqual(paired.loc[0, "gap_p20"], 1)
        self.assertNotIn("alignment_residual", MODEL_FEATURES["baseline_2_extended"])
        self.assertNotIn("target_year", MODEL_FEATURES["baseline_2_extended"])

    def test_missing_extended_predictors_are_audited_not_imputed(self) -> None:
        sample = self.frame.iloc[:4].copy()
        sample.loc[sample.index[0], "median_household_income"] = np.nan
        complete, audit = complete_predictor_sample(sample)
        self.assertEqual(len(complete), 3)
        self.assertEqual(int(audit.additional_feature_missing.sum()), 1)
        self.assertTrue(complete.median_household_income.notna().all())

    def test_logistic_preprocessing_and_fit_use_training_only(self) -> None:
        fitted = fit_logistic_baseline(self.train, model="baseline_1_simple")
        self.assertAlmostEqual(fitted.numeric_means["startup_rate"], self.train.startup_rate.mean())
        scored = self.validation.copy()
        original_probability = predict_gap_probability(fitted, scored)
        scored["gap_p20"] = 1 - scored.gap_p20
        np.testing.assert_allclose(original_probability, predict_gap_probability(fitted, scored))
        self.assertTrue(np.isfinite(original_probability).all())
        self.assertTrue(((original_probability >= 0) & (original_probability <= 1)).all())

    def test_preprocessing_is_unchanged_by_validation_distribution(self) -> None:
        fitted = fit_logistic_baseline(self.train, model="baseline_2_extended")
        shifted = self.validation.copy()
        shifted["median_household_income"] *= 100
        predict_gap_probability(fitted, shifted)
        self.assertAlmostEqual(fitted.numeric_means["median_household_income"], self.train.median_household_income.mean())

    def test_metrics_calibration_and_lift_handle_prevalence_and_ties(self) -> None:
        actual = pd.Series([0, 1, 0, 1, 0, 1])
        metrics = probability_metrics(actual, np.repeat(actual.mean(), len(actual)))
        self.assertAlmostEqual(metrics["roc_auc"], 0.5)
        self.assertAlmostEqual(metrics["pr_auc"], actual.mean())
        calibration = calibration_table(actual, np.repeat(actual.mean(), len(actual)))
        self.assertEqual(len(calibration), 1)
        lift = lift_table(actual, np.repeat(actual.mean(), len(actual)))
        self.assertTrue(np.allclose(lift.lift_ratio, 1.0))

    def test_holdout_years_are_not_loaded_from_predictor_view(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "panel.sqlite"
            connection = sqlite3.connect(path)
            connection.execute("CREATE TABLE panel (year INTEGER, value INTEGER)")
            connection.executemany("INSERT INTO panel VALUES (?, ?)", [(2017, 1), (2018, 2), (2023, 3)])
            connection.execute("CREATE VIEW v_analytics_msa_industry_year AS SELECT * FROM panel")
            connection.commit()
            connection.close()
            panel = _load_predictor_panel(path)
            self.assertEqual(panel.year.tolist(), [2017])

    def test_canonical_panel_read_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "readonly.sqlite"
            connection = sqlite3.connect(path)
            connection.execute("CREATE TABLE panel (year INTEGER)")
            connection.execute("INSERT INTO panel VALUES (2017)")
            connection.execute("CREATE VIEW v_analytics_msa_industry_year AS SELECT * FROM panel")
            connection.commit()
            connection.close()
            _load_predictor_panel(path)
            connection = sqlite3.connect(path)
            try:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM panel").fetchone()[0], 1)
            finally:
                connection.close()

    def test_pooled_oof_key_definition_has_no_duplicate_validation_pair(self) -> None:
        oof = pd.DataFrame({"fold": ["fold_1", "fold_2"], "cbsa_code": ["10180", "10180"],
                            "sector_code": ["11", "11"], "predictor_year": [2014, 2015],
                            "target_year": [2017, 2018], "actual_gap": [0, 1]})
        validate_oof_predictions(oof)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_oof_predictions(pd.concat([oof, oof.iloc[[0]]], ignore_index=True))
        with self.assertRaisesRegex(ValueError, r"exact t\+3"):
            validate_oof_predictions(oof.assign(target_year=[2018, 2018]))

    def test_no_advanced_classifiers_are_registered(self) -> None:
        self.assertEqual(set(MODEL_FEATURES), {
            "baseline_1_simple", "baseline_2_extended", "baseline_2_no_startup_lag1",
            "baseline_2_no_employment_growth", "baseline_1_no_sector", "baseline_1_no_time",
        })


if __name__ == "__main__":
    unittest.main()
