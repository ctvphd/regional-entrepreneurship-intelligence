from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from regional_entrepreneurship_intelligence.models.expected import fit_expected_model, predict_expected
from regional_entrepreneurship_intelligence.models.robustness import (
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


class RobustnessTest(unittest.TestCase):
    def test_fixed_hash_geography_partition_is_reproducible_and_disjoint(self):
        codes = pd.Series([f"{i:05d}" for i in range(1, 501)])
        first = deterministic_geography_split(codes)
        second = deterministic_geography_split(codes)
        pd.testing.assert_frame_equal(first, second)
        validate_geography_disjoint(first)
        self.assertTrue(.17 < first.geography_role.eq("test").mean() < .23)
        with self.assertRaisesRegex(ValueError, "one geographic role"):
            validate_geography_disjoint(pd.concat([first, first.iloc[[0]].assign(geography_role="test")]))

    def test_fold_local_population_terciles_use_training_distribution_only(self):
        train = pd.Series(np.arange(1.0, 10.0))
        groups, cutpoints = assign_population_terciles(train, pd.Series([8.5, 1000.0]))
        self.assertTrue(np.allclose(cutpoints, [3.6666666667, 6.3333333333]))
        self.assertEqual(list(groups.astype(str)), ["upper_third", "upper_third"])

    def test_predictor_sensitivity_fields_join_only_on_predictor_year(self):
        pairs = pd.DataFrame({"cbsa_code": ["10180"], "sector_code": ["11"],
                              "predictor_year": [2014], "target_year": [2017]})
        panel = pd.DataFrame({"cbsa_code": ["10180", "10180"], "sector_code": ["11", "11"],
                              "year": [2014, 2017], "establishment_growth": [.03, 99.0]})
        result = attach_predictor_year_fields(pairs, panel, ("establishment_growth",))
        self.assertEqual(result.loc[0, "establishment_growth"], .03)
        with self.assertRaisesRegex(ValueError, r"exact t\+3"):
            attach_predictor_year_fields(pairs.assign(target_year=2018), panel, ("establishment_growth",))

    def test_pandemic_exclusions_are_deterministic_and_non_mutating(self):
        frame = pd.DataFrame({"predictor_year": [2014, 2015, 2017], "target_year": [2017, 2018, 2020]})
        before = frame.copy(deep=True)
        result = exclude_calendar_year_pairs(frame, {2020, 2021})
        self.assertEqual(len(result), 2)
        pd.testing.assert_frame_equal(frame, before)

    def test_development_boundary_rejects_temporal_holdout_pairs(self):
        dev = pd.DataFrame({"predictor_year": [2017], "target_year": [2020]})
        assert_development_only(dev)
        with self.assertRaisesRegex(ValueError, "temporal boundary"):
            assert_development_only(pd.DataFrame({"predictor_year": [2018], "target_year": [2021]}))

    def test_label_agreement_reports_positive_overlap_and_kappa(self):
        result = label_agreement(pd.Series([1, 1, 0, 0]), pd.Series([1, 0, 0, 0]))
        self.assertEqual(result["agreement"], .75)
        self.assertEqual(result["positive_jaccard"], .5)
        self.assertEqual(result["primary_positive_n"], 2)

    def test_training_only_tail_clipping_does_not_mutate_source_values(self):
        training = pd.Series([0.0, 1.0, 2.0, 3.0, 100.0])
        validation = pd.Series([-500.0, 2.0, 500.0])
        train_before, val_before = training.copy(), validation.copy()
        clipped_train, clipped_val, low, high = clip_from_training(training, validation)
        self.assertEqual(low, 0.04)
        self.assertAlmostEqual(high, 96.12)
        self.assertTrue(clipped_val.between(low, high).all())
        pd.testing.assert_series_equal(training, train_before)
        pd.testing.assert_series_equal(validation, val_before)

    def test_sector_metrics_can_be_gated_by_minimum_positive_events(self):
        self.assertFalse(sector_sufficiency(29, minimum_events=30))
        self.assertTrue(sector_sufficiency(30, minimum_events=30))

    def test_selection_effect_size_handles_balanced_groups_without_mutation(self):
        included = pd.Series([1.0, 2.0, 3.0])
        excluded = pd.Series([5.0, 6.0, 7.0])
        before = included.copy()
        self.assertLess(standardized_mean_difference(included, excluded), 0)
        pd.testing.assert_series_equal(included, before)

    def test_huber_expected_fit_and_residual_cutoff_are_training_local(self):
        rng = np.random.default_rng(76)
        years = np.repeat(np.arange(2010, 2019), 80)
        n = len(years)
        frame = pd.DataFrame({
            "year": years,
            "sector_code": np.where(np.arange(n) % 2, "11", "21"),
            "startup_rate": rng.normal(5, 1, n),
            "startup_rate_lag1": rng.normal(5, 1, n),
            "employment_growth": rng.normal(0, .05, n),
            "acs_population_growth": rng.normal(0, .02, n),
            "median_household_income": rng.normal(60000, 5000, n),
            "educational_attainment_pct": rng.normal(30, 4, n),
            "labor_force_participation_pct": rng.normal(63, 3, n),
            "unemployment_rate": rng.normal(5, 1, n),
        })
        model = fit_expected_model(frame[frame.year.le(2016)], name="C", training_year_end=2016, estimator="huber")
        fitted = predict_expected(model, model.training_frame)
        cutoff = fitted.residual.quantile(.20)
        future = predict_expected(model, frame[frame.year.eq(2018)])
        self.assertEqual(model.training_frame.year.max(), 2016)
        self.assertLessEqual(cutoff, fitted.residual.quantile(.25))
        self.assertEqual(future.year.max(), 2018)


if __name__ == "__main__":
    unittest.main()
