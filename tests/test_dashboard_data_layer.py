from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

import numpy as np

from regional_entrepreneurship_intelligence.dashboard.data_layer import (
    PANEL_COLUMNS,
    TABLE_DIR,
    _read_panel,
    build_datasets,
    validate_dashboard_outputs,
)
from regional_entrepreneurship_intelligence.dashboard.loader import (
    DATASETS,
    load_dashboard_labels,
    load_dashboard_metadata,
    load_dataset,
    load_filter_options,
)


class DashboardDataLayerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datasets = build_datasets()

    def test_all_dataset_keys_are_unique(self):
        checks = validate_dashboard_outputs(self.datasets)
        self.assertTrue(checks.status.eq("pass").all())

    def test_prediction_horizon_and_split_labels(self):
        frame = self.datasets["dashboard_model_predictions"]
        self.assertTrue((frame.target_year == frame.predictor_year + 3).all())
        self.assertTrue(frame.development_or_holdout.isin(["development_oof", "final_holdout"]).all())
        self.assertEqual(set(frame.development_or_holdout), {"development_oof", "final_holdout"})

    def test_probabilities_are_bounded_and_labels_binary(self):
        frame = self.datasets["dashboard_model_predictions"]
        for col in ("logistic_probability", "hgb_probability"):
            self.assertTrue(frame[col].between(0, 1).all())
        self.assertTrue(frame.actual_gap.isin([0, 1]).all())

    def test_model_summary_reconciles_with_final_holdout_artifact(self):
        import pandas as pd

        source = pd.read_csv(TABLE_DIR / "a6_final_model_performance.csv")
        source = source.loc[source.dataset.eq("holdout") & source.model.eq("logistic")].iloc[0]
        summary = self.datasets["dashboard_model_summary"]
        for metric in ("AP", "prevalence", "ROC_AUC", "Brier", "top10_lift"):
            value = summary.loc[(summary.dataset_split == "final_holdout") &
                                (summary.model == "logistic") & (summary.metric == metric), "value"].iloc[0]
            self.assertTrue(np.isclose(value, source[metric], rtol=0, atol=1e-14))

    def test_dashboard_fields_types_and_expected_nulls(self):
        panel = self.datasets["dashboard_msa_industry_year"]
        self.assertEqual(str(panel.cbsa_code.dtype), "string")
        self.assertEqual(str(panel.sector_code.dtype), "string")
        self.assertTrue(panel.year.notna().all())
        self.assertTrue(panel.expected_startup_rate.isna().any())
        self.assertTrue(panel.observed_historical_gap_status.isna().any())
        self.assertFalse(any(c in panel for c in ("logistic_probability", "hgb_probability", "risk_category")))

    def test_coverage_is_one_row_per_msa_and_uses_documented_values(self):
        import pandas as pd

        coverage = self.datasets["dashboard_coverage"]
        self.assertFalse(coverage.cbsa_code.duplicated().any())
        self.assertTrue(coverage.coverage_status.isin(["comparison_eligible", "thin"]).all())
        source = pd.read_csv(TABLE_DIR / "a5_msa_coverage.csv")
        self.assertEqual(int(coverage.comparison_eligible_flag.sum()), int(source.eligible_for_comparison.sum()))
        self.assertEqual(int((coverage.coverage_status == "thin").sum()), int((~source.eligible_for_comparison).sum()))

    def test_calibration_and_subgroup_datasets_have_explicit_splits(self):
        self.assertEqual(set(self.datasets["dashboard_calibration"].dataset_split),
                         {"development_oof", "final_holdout"})
        for name in ("dashboard_model_by_year", "dashboard_model_by_sector", "dashboard_model_by_msa_size"):
            self.assertTrue(self.datasets[name].dataset_split.eq("final_holdout").all())

    def test_all_parquet_datasets_are_allow_listed_by_loader(self):
        self.assertEqual(DATASETS, {
            "msa_industry_year", "model_predictions", "model_summary", "calibration",
            "model_by_year", "model_by_sector", "model_by_msa_size", "coverage", "sources",
        })
        with self.assertRaises(ValueError):
            load_dataset("../../database/assignment4_production", data_dir=Path("."))

    def test_sources_include_only_documented_project_inputs_and_outputs(self):
        sources = self.datasets["dashboard_sources"]
        self.assertTrue({"BDS", "QCEW", "ACS", "CBP"}.issubset(
            set(sources.source_name.str.extract(r"\(([^)]+)\)", expand=False).dropna())
        ))
        self.assertTrue(sources.source_name.str.contains("Assignment 6 finalized").any())

    def test_panel_reader_uses_read_only_connection_and_preserves_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "small.sqlite"
            connection = sqlite3.connect(path)
            definitions = ", ".join(f'"{col}" ' + ("TEXT" if col in {"cbsa_code", "cbsa_name", "sector_code", "sector_title", "source_quality_notes"} else "INTEGER" if col == "year" else "REAL") for col in PANEL_COLUMNS)
            connection.execute(f"CREATE TABLE v_analytics_msa_industry_year ({definitions})")
            values = ["01001", "Example, ST", "11", "Agriculture", 2020] + [1.0] * (len(PANEL_COLUMNS) - 5)
            connection.execute(f"INSERT INTO v_analytics_msa_industry_year VALUES ({','.join('?' for _ in PANEL_COLUMNS)})", values)
            connection.commit()
            connection.close()
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = _read_panel(path)
            after = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(before, after)
            self.assertEqual(result.cbsa_code.iloc[0], "01001")

    def test_dashboard_loader_reads_written_files_when_present(self):
        import json

        import pandas as pd

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            sample = pd.DataFrame({"cbsa_code": pd.Series(["01001"], dtype="string")})
            sample.to_parquet(data_dir / "dashboard_msa_industry_year.parquet", engine="pyarrow")
            (data_dir / "dashboard_metadata.json").write_text(json.dumps({"schema_version": "1.0.0"}), encoding="utf-8")
            (data_dir / "dashboard_labels.json").write_text(json.dumps({"models": {"logistic": "Logistic"}}), encoding="utf-8")
            self.assertEqual(load_dataset("msa_industry_year", data_dir=data_dir).cbsa_code.iloc[0], "01001")
            self.assertEqual(load_dashboard_metadata(data_dir=data_dir)["schema_version"], "1.0.0")
            self.assertEqual(load_dashboard_labels(data_dir=data_dir)["models"]["logistic"], "Logistic")

    def test_filter_options_cover_required_filters_without_unapproved_risk_bands(self):
        options = load_filter_options()
        self.assertTrue(options["msa_options"])
        self.assertTrue(options["sector_options"])
        self.assertTrue(options["year_options"])
        self.assertEqual(options["observed_historical_gap_status_options"], [0, 1])
        self.assertEqual(options["prediction_availability_options"], ["available", "unavailable"])
        self.assertEqual(options["risk_category_options"], [])

    def test_no_streamlit_runtime_is_required(self):
        import sys

        self.assertNotIn("streamlit", sys.modules)


if __name__ == "__main__":
    unittest.main()
