from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.models.expected import (
    BASE_FEATURES,
    MODEL_FORMULAS,
    complete_cases,
    fit_expected_model,
    predict_expected,
)


class ExpectedModelTest(unittest.TestCase):
    def setUp(self) -> None:
        rows = []
        for year in range(2010, 2017):
            for msa in range(1, 31):
                sector = str(10 + msa % 3)
                growth = ((msa % 7) - 3) / 100
                lag = 1.0 + msa / 10 + (year - 2010) / 5
                rows.append({
                    "cbsa_code": f"{msa:05d}",
                    "sector_code": sector,
                    "year": year,
                    "startup_rate_lag1": lag,
                    "employment_growth": growth,
                    "acs_population_growth": .01 + (msa * 17 % 31) / 10000 + (year - 2010) / 100000,
                    "median_household_income": 50000 + (msa * 7919 % 19000) + (year - 2010) * 230,
                    "educational_attainment_pct": 25 + (msa * 37 % 53) / 2,
                    "labor_force_participation_pct": 60 + (msa * 29 % 27) / 5,
                    "unemployment_rate": 4 + (msa * 13 % 19) / 20,
                    "startup_rate": 2 + .4 * lag + .2 * growth + (int(sector) - 10) / 10 + (year - 2010) / 20,
                })
        self.frame = pd.DataFrame(rows)

    def test_primary_models_retain_required_fixed_effects_and_interaction(self) -> None:
        self.assertIn("C(sector_code)", MODEL_FORMULAS["A"])
        self.assertIn("C(year)", MODEL_FORMULAS["A"])
        self.assertIn("employment_growth:C(sector_code)", MODEL_FORMULAS["B"])
        self.assertIn("C(sector_code)", MODEL_FORMULAS["B"])

    def test_fit_refuses_rows_after_temporal_cutoff(self) -> None:
        with self.assertRaisesRegex(ValueError, "after cutoff"):
            fit_expected_model(self.frame, name="A", training_year_end=2015)

    def test_validation_year_effect_carries_forward_latest_training_year(self) -> None:
        train = self.frame[self.frame.year <= 2015]
        model = fit_expected_model(train, name="A", training_year_end=2015)
        validation = self.frame[self.frame.year == 2016].copy()
        scored = predict_expected(model, validation)
        manual = validation.copy()
        manual["year"] = 2015
        expected = np.asarray(model.result.predict(manual))
        np.testing.assert_allclose(scored.expected_startup_rate, expected)
        self.assertTrue((scored.residual == scored.startup_rate - scored.expected_startup_rate).all())

    def test_complete_case_excludes_missing_and_infinite_without_imputation(self) -> None:
        sample = self.frame.iloc[:4].copy()
        sample.loc[sample.index[0], "employment_growth"] = np.inf
        sample.loc[sample.index[1], "median_household_income"] = np.nan
        clean = complete_cases(sample, BASE_FEATURES)
        self.assertEqual(len(clean), 2)
        self.assertTrue(np.isfinite(clean.employment_growth).all())


if __name__ == "__main__":
    unittest.main()
