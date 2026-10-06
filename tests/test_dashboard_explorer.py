from __future__ import annotations

import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

from regional_entrepreneurship_intelligence.dashboard.charts import (
    build_alignment_history_chart,
    build_employment_growth_chart,
    build_gap_timeline,
    build_observed_expected_chart,
    build_prediction_history_chart,
    build_startup_trend_chart,
)
from regional_entrepreneurship_intelligence.dashboard.data_access import cached_dataset, cached_filter_options
from regional_entrepreneurship_intelligence.dashboard.explorer_data import (
    ExplorerDataError,
    alignment_interpretation,
    attach_prediction_records,
    build_top_risk_ranking,
    filter_explorer_data,
    filter_predictions,
    filtered_csv_frame,
    selection_summary,
    validate_explorer_inputs,
)
from regional_entrepreneurship_intelligence.dashboard.loader import load_dashboard_labels, load_dashboard_metadata
from regional_entrepreneurship_intelligence.dashboard.state import (
    default_filter_state,
    initialize_filter_state,
    reset_filter_state,
)


class DashboardExplorerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.panel = cached_dataset("msa_industry_year")
        cls.predictions = cached_dataset("model_predictions")
        cls.options = cached_filter_options()
        cls.labels = load_dashboard_labels()
        cls.metadata = load_dashboard_metadata()
        cls.prediction_years = {
            split: sorted(cls.predictions.loc[cls.predictions.development_or_holdout == split, "predictor_year"].astype(int).unique())
            for split in ("final_holdout", "development_oof")
        }
        cls.sample = cls.panel.iloc[0]

    def test_artifact_contract_is_unique_and_exact_t_plus_three(self):
        validate_explorer_inputs(self.panel, self.predictions, 3)
        bad = self.predictions.copy()
        bad.loc[bad.index[0], "target_year"] += 1
        with self.assertRaisesRegex(ExplorerDataError, "exact forecast horizon"):
            validate_explorer_inputs(self.panel, bad, 3)

    def test_msa_sector_year_and_gap_filters_compose(self):
        msa, sector, year = str(self.sample.cbsa_code), str(self.sample.sector_code), int(self.sample.year)
        filtered = filter_explorer_data(self.panel, msa=msa, sectors=[sector], year=year)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(str(filtered.iloc[0].cbsa_code), msa)
        self.assertEqual(str(filtered.iloc[0].sector_code), sector)
        self.assertEqual(int(filtered.iloc[0].year), year)
        if not pd.isna(self.sample.observed_historical_gap_status):
            gap = int(self.sample.observed_historical_gap_status)
            gap_rows = filter_explorer_data(self.panel, msa=msa, sectors=[sector], year=year, gap_status=gap)
            self.assertEqual(len(gap_rows), 1)
            self.assertTrue((gap_rows.observed_historical_gap_status == gap).all())
            self.assertTrue(filter_explorer_data(self.panel, msa=msa, sectors=[sector], year=year, gap_status=1-gap).empty)
        with self.assertRaisesRegex(ValueError, "not available"):
            filter_explorer_data(self.panel, year=1900)

    def test_prediction_availability_uses_exact_msa_sector_predictor_year_key(self):
        row = self.predictions.query("development_or_holdout == 'final_holdout'").iloc[0]
        panel_key = self.panel.query(
            "cbsa_code == @row.cbsa_code and sector_code == @row.sector_code and year == @row.predictor_year"
        )
        matched = filter_explorer_data(
            self.panel, msa=str(row.cbsa_code), sectors=[str(row.sector_code)], year=int(row.predictor_year),
            has_prediction=True, predictions=self.predictions,
        )
        self.assertEqual(len(panel_key), 1)
        self.assertEqual(len(matched), 1)
        self.assertEqual(str(matched.iloc[0].cbsa_code), str(row.cbsa_code))
        attached = attach_prediction_records(panel_key, self.predictions)
        self.assertEqual(int(attached.iloc[0].target_year), int(row.target_year))
        self.assertEqual(float(attached.iloc[0].logistic_probability), float(row.logistic_probability))

    def test_prediction_filters_keep_splits_separate_and_top_ranking_uses_logistic(self):
        holdout = filter_predictions(self.predictions, split="final_holdout", predictor_year=2020)
        development = filter_predictions(self.predictions, split="development_oof", predictor_year=2017)
        self.assertEqual(set(holdout.development_or_holdout), {"final_holdout"})
        self.assertEqual(set(development.development_or_holdout), {"development_oof"})
        self.assertTrue((holdout.target_year == holdout.predictor_year + 3).all())
        top = build_top_risk_ranking(
            self.predictions, split="final_holdout", predictor_year=2020, top_n=10, labels=self.labels
        )
        self.assertLessEqual(len(top), 10)
        self.assertTrue(top["Predicted gap probability (logistic)"].is_monotonic_decreasing)
        self.assertIn("Actual target gap (retrospective)", top.columns)
        self.assertTrue(set(top["Actual target gap (retrospective)"]).issubset({"Gap observed", "No gap observed", "Unavailable"}))
        for n in (10, 25, 50):
            self.assertLessEqual(len(build_top_risk_ranking(
                self.predictions, split="final_holdout", predictor_year=2020, top_n=n, labels=self.labels
            )), n)
        with self.assertRaises(ValueError):
            build_top_risk_ranking(self.predictions, split="final_holdout", predictor_year=2020, top_n=20)
        with self.assertRaises(ValueError):
            filter_predictions(self.predictions, split="all", predictor_year=2020)

    def test_reset_restores_all_explorer_and_prediction_defaults(self):
        defaults = default_filter_state(self.options, self.prediction_years)
        self.assertIsNone(defaults["selected_msa"])
        self.assertEqual(defaults["selected_sectors"], [])
        self.assertEqual(defaults["selected_year"], max(self.options["year_options"]))
        self.assertIsNone(defaults["selected_gap_status"])
        self.assertFalse(defaults["selected_has_prediction"])
        self.assertEqual(defaults["selected_top_n"], 10)
        self.assertEqual(defaults["selected_prediction_split"], "final_holdout")
        state = {
            "selected_msa": "bad", "selected_sectors": ["bad"], "selected_year": 1900,
            "selected_gap_status": 9, "selected_has_prediction": True, "selected_top_n": 50,
            "selected_prediction_split": "development_oof", "selected_prediction_year": 2014,
        }
        initialize_filter_state(state, self.options, self.prediction_years)
        self.assertEqual(state["selected_msa"], None)
        self.assertEqual(state["selected_sectors"], [])
        reset_filter_state(state, self.options, self.prediction_years)
        self.assertEqual(state, defaults)

    def test_nulls_are_not_zero_and_alignment_language_respects_status(self):
        self.assertIn("unavailable", alignment_interpretation(pd.NA, pd.NA).lower())
        self.assertIn("below expectation", alignment_interpretation(-1.5, 0).lower())
        self.assertIn("materially below", alignment_interpretation(-4.0, 1).lower())
        self.assertIn("at or above", alignment_interpretation(0.5, 0).lower())
        history = self.panel.query("cbsa_code == @self.sample.cbsa_code and sector_code == @self.sample.sector_code")
        attached = attach_prediction_records(history, self.predictions)
        missing_rows = attached.loc[attached.logistic_probability.isna()]
        self.assertTrue(missing_rows.empty or missing_rows.logistic_probability.isna().all())

    def test_major_metro_incomplete_sector_scope_and_extreme_rate_are_not_filled_or_clipped(self):
        chicago = filter_explorer_data(self.panel, msa="16980")
        self.assertEqual(chicago["sector_code"].nunique(), 11)
        self.assertLess(chicago["sector_code"].nunique(), self.panel["sector_code"].nunique())
        self.assertEqual(set(chicago["coverage_status"]), {"thin"})
        bay_city = self.panel.query("cbsa_code == '13020' and sector_code == '11' and year == 2015")
        self.assertEqual(len(bay_city), 1)
        self.assertEqual(float(bay_city.iloc[0].startup_rate), 80.0)
        self.assertTrue(pd.isna(bay_city.iloc[0].expected_startup_rate))

    def test_filtered_csv_contains_only_dashboard_fields_and_metadata(self):
        row = self.predictions.query("development_or_holdout == 'final_holdout'").iloc[0]
        joined = attach_prediction_records(self.panel, self.predictions)
        filtered = filter_explorer_data(
            joined, msa=str(row.cbsa_code), sectors=[str(row.sector_code)], year=int(row.predictor_year)
        )
        export = filtered_csv_frame(
            filtered, dashboard_version=self.metadata["dashboard_data_version"],
            primary_model=self.metadata["primary_model"],
        )
        self.assertEqual(len(export), 1)
        self.assertIn("dashboard_data_version", export.columns)
        self.assertIn("primary_model", export.columns)
        self.assertIn("actual_target_gap_retrospective", export.columns)
        self.assertNotIn("sqlite_path", export.columns)
        self.assertEqual(export.iloc[0]["prediction_target_year"], export.iloc[0]["prediction_predictor_year"] + 3)

    def test_dynamic_selection_summary_and_plotly_charts(self):
        prediction = self.predictions.query("development_or_holdout == 'final_holdout'").iloc[0]
        rows = self.panel.query(
            "cbsa_code == @prediction.cbsa_code and sector_code == @prediction.sector_code"
        )
        text = selection_summary(rows, msa=str(prediction.cbsa_code), sectors=[str(prediction.sector_code)], year=int(rows.year.max()))
        self.assertIn(str(rows.msa_name.iloc[0]), text)
        self.assertIn(str(rows.sector_name.iloc[0]), text)
        self.assertIn(str(int(rows.year.max())), text)
        figures = (
            build_observed_expected_chart(rows), build_startup_trend_chart(rows),
            build_employment_growth_chart(rows), build_alignment_history_chart(rows),
            build_gap_timeline(rows), build_prediction_history_chart(
                filter_predictions(self.predictions, split="final_holdout", predictor_year=None,
                                   msa=str(prediction.cbsa_code), sectors=[str(prediction.sector_code)])
            ),
        )
        self.assertTrue(all(hasattr(fig, "data") and len(fig.data) for fig in figures))
        self.assertEqual(figures[0].layout.xaxis.title.text, "Descriptive calendar year")
        self.assertEqual(figures[3].layout.yaxis.title.text, "Observed minus expected (percentage points)")

    def test_explorer_renders_without_exceptions_and_keeps_categories_unavailable(self):
        app = AppTest.from_string(
            "from regional_entrepreneurship_intelligence.dashboard.pages import explorer\nexplorer.render()",
            default_timeout=30,
        ).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any(item.label == "Only rows with an evaluation prediction" for item in app.checkbox))
        self.assertTrue(any(item.label == "Download filtered CSV" for item in app.download_button))
        risk_filter = next(item for item in app.selectbox if item.label == "Risk category")
        self.assertTrue(risk_filter.disabled)

        prediction = self.predictions.query(
            "cbsa_code == '35620' and sector_code == '44-45' and predictor_year == 2020 and development_or_holdout == 'final_holdout'"
        ).iloc[0]
        app.get_by_key("selected_msa").select(str(prediction.cbsa_code)).run()
        app.get_by_key("selected_sectors").select(str(prediction.sector_code)).run()
        app.get_by_key("selected_year").select(int(prediction.predictor_year)).run()
        app.get_by_key("selected_gap_status").select(0).run()
        app.get_by_key("selected_has_prediction").check().run()
        app.get_by_key("selected_prediction_split").select("development_oof").run()
        app.get_by_key("selected_prediction_year").select(min(self.prediction_years["development_oof"])).run()
        app.get_by_key("selected_top_n").select(25).run()
        self.assertEqual(app.get_by_key("selected_msa").value, str(prediction.cbsa_code))
        self.assertEqual(app.get_by_key("selected_sectors").value, [str(prediction.sector_code)])
        self.assertEqual(app.get_by_key("selected_year").value, int(prediction.predictor_year))
        self.assertEqual(app.get_by_key("selected_gap_status").value, 0)
        self.assertTrue(app.get_by_key("selected_has_prediction").value)
        self.assertEqual(app.get_by_key("selected_prediction_split").value, "development_oof")
        self.assertEqual(app.get_by_key("selected_prediction_year").value, min(self.prediction_years["development_oof"]))
        self.assertEqual(app.get_by_key("selected_top_n").value, 25)
        self.assertGreaterEqual(len(app.get("plotly_chart")), 6)
        app.get_by_key("reset_explorer_filters").click().run()
        self.assertIsNone(app.get_by_key("selected_msa").value)
        self.assertEqual(app.get_by_key("selected_sectors").value, [])
        self.assertEqual(app.get_by_key("selected_year").value, max(self.options["year_options"]))
        self.assertIsNone(app.get_by_key("selected_gap_status").value)
        self.assertFalse(app.get_by_key("selected_has_prediction").value)
        self.assertEqual(app.get_by_key("selected_top_n").value, 10)
        self.assertEqual(app.get_by_key("selected_prediction_split").value, "final_holdout")
        self.assertEqual(app.get_by_key("selected_prediction_year").value, max(self.prediction_years["final_holdout"]))
        self.assertEqual(len(app.exception), 0)

    def test_thin_msa_missing_expectation_and_prediction_have_clear_empty_states(self):
        app = AppTest.from_string(
            "from regional_entrepreneurship_intelligence.dashboard.pages import explorer\nexplorer.render()",
            default_timeout=30,
        ).run()
        app.get_by_key("selected_msa").select("12060").run()
        app.get_by_key("selected_sectors").select("23").run()
        app.get_by_key("selected_year").select(2013).run()
        self.assertEqual(len(app.exception), 0)
        self.assertLessEqual(len(app.get("plotly_chart")), 2)
        self.assertTrue(any(item.label == "Expected startup rate" and item.value == "N/A" for item in app.metric))
        self.assertTrue(any("Expected startup activity is unavailable" in item.value for item in app.info))
        self.assertTrue(any("No prediction records exist" in item.value for item in app.info))
        self.assertTrue(any("marked thin by the A5 descriptive coverage screen" in item.value for item in app.warning))
        app.get_by_key("selected_gap_status").select(1).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("marked thin by the A5 descriptive coverage screen" in item.value for item in app.warning))


if __name__ == "__main__":
    unittest.main()
