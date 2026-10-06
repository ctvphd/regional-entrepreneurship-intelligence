from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from regional_entrepreneurship_intelligence.dashboard.data_access import cached_dataset
from regional_entrepreneurship_intelligence.dashboard.components import (
    coverage_badge,
    dataframe_csv_bytes,
    development_holdout_label,
)
from regional_entrepreneurship_intelligence.dashboard.constants import (
    REQUIRED_ARTIFACTS,
    REQUIRED_DATASETS,
)
from streamlit.testing.v1 import AppTest
from regional_entrepreneurship_intelligence.dashboard.health import (
    REQUIRED_FIELDS,
    check_dashboard_health,
)
from regional_entrepreneurship_intelligence.dashboard.loader import (
    DATA_DIR,
    load_dashboard_metadata,
    load_filter_options,
)
from regional_entrepreneurship_intelligence.dashboard.state import (
    default_filter_state,
    initialize_filter_state,
    reset_filter_state,
)
from regional_entrepreneurship_intelligence.dashboard.pages import (
    about,
    explorer,
    overview,
    performance,
    quality,
)


class DashboardShellTest(unittest.TestCase):
    def test_all_five_page_modules_import(self):
        self.assertTrue(all(callable(module.render) for module in (overview, explorer, performance, quality, about)))

    def test_app_startup_renders_without_exceptions(self):
        entry_point = Path(__file__).parents[1] / "streamlit_app.py"
        app = AppTest.from_file(str(entry_point), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.title), 1)
        self.assertEqual(app.title[0].value, "Regional Entrepreneurship Intelligence")

    def test_metadata_and_required_artifacts_are_available(self):
        metadata = load_dashboard_metadata()
        self.assertEqual(metadata["dashboard_data_version"], "1.0.0")
        self.assertEqual(metadata["primary_model"], "logistic")
        self.assertEqual(metadata["forecast_horizon_years"], 3)
        self.assertEqual(metadata["study_period"]["descriptive"], [2010, 2023])
        self.assertTrue(all((DATA_DIR / name).is_file() for name in REQUIRED_ARTIFACTS))
        self.assertTrue(all((DATA_DIR / f"dashboard_{name}.parquet").is_file() for name in REQUIRED_DATASETS))

    def test_cached_loader_wrapper_returns_dataframe(self):
        cached_dataset.clear()
        frame = cached_dataset("coverage")
        self.assertIsInstance(frame, pd.DataFrame)
        self.assertIn("coverage_status", frame)

    def test_filters_are_based_on_a72_options(self):
        options = load_filter_options()
        self.assertGreater(len(options["msa_options"]), 0)
        self.assertGreater(len(options["sector_options"]), 0)
        self.assertEqual(options["year_options"], sorted(options["year_options"]))
        self.assertEqual(options["risk_category_options"], [])
        self.assertEqual(options["observed_historical_gap_status_options"], [0, 1])

    def test_filter_state_initializes_sanitizes_and_resets(self):
        options = load_filter_options()
        defaults = default_filter_state(options)
        state = {"selected_year": -1, "selected_msa": "invalid", "selected_sectors": ["bad"]}
        initialize_filter_state(state, options)
        self.assertEqual(state, defaults)
        state["selected_year"] = options["year_options"][0]
        state["selected_msa"] = options["msa_options"][0]["value"]
        reset_filter_state(state, options)
        self.assertEqual(state, defaults)

    def test_coverage_accepts_only_approved_a72_statuses(self):
        self.assertIn("Comparison eligible", coverage_badge("comparison_eligible"))
        self.assertIn("Thin coverage", coverage_badge("thin"))
        for status in ("strong", "moderate", "unknown"):
            with self.assertRaises(ValueError):
                coverage_badge(status)

    def test_development_and_holdout_labels_are_unambiguous(self):
        self.assertEqual(development_holdout_label("development_oof"), "Development OOF")
        self.assertEqual(development_holdout_label("final_holdout"), "Final temporal holdout")
        with self.assertRaises(ValueError):
            development_holdout_label("live_forecast")

    def test_csv_helper_returns_utf8_bytes_without_index(self):
        payload = dataframe_csv_bytes(pd.DataFrame({"meaningful_field": [1]}))
        self.assertEqual(payload, b"meaningful_field\n1\n")

    def test_ui_modules_have_no_model_training_or_sqlite_logic(self):
        root = Path(__file__).parents[1] / "src" / "regional_entrepreneurship_intelligence" / "dashboard"
        ui_files = [root / "app.py", root / "components.py", root / "filters.py", root / "state.py", *sorted((root / "pages").glob("*.py"))]
        banned_roots = {"sklearn", "statsmodels", "sqlite3"}
        for path in ui_files:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertFalse(imported & banned_roots, f"Forbidden scientific/storage import in {path.name}")
            self.assertNotIn("connect(", path.read_text(encoding="utf-8"))


class DashboardHealthTest(unittest.TestCase):
    def test_missing_artifacts_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            result = check_dashboard_health(Path(directory))
        self.assertFalse(result["healthy"])
        self.assertTrue(any(not check["passed"] for check in result["checks"]))

    def test_corrupt_metadata_is_reported_without_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in REQUIRED_ARTIFACTS:
                (root / name).write_text("{invalid", encoding="utf-8")
            result = check_dashboard_health(root)
        self.assertFalse(result["healthy"])
        self.assertTrue(any(check["name"] == "metadata_readable" and not check["passed"] for check in result["checks"]))

    def test_required_fields_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in REQUIRED_ARTIFACTS:
                (root / name).touch()
            for name in REQUIRED_DATASETS:
                (root / f"dashboard_{name}.parquet").touch()
            metadata = {
                "dashboard_data_version": "1.0.0",
                "study_period": {},
                "primary_model": "logistic",
                "forecast_horizon_years": 3,
                "final_A6_commit": "test",
            }
            options = {
                "msa_options": [], "sector_options": [], "year_options": [],
                "risk_category_options": [], "observed_historical_gap_status_options": [],
            }
            with patch("regional_entrepreneurship_intelligence.dashboard.health.load_dashboard_metadata", return_value=metadata), patch(
                "regional_entrepreneurship_intelligence.dashboard.health.load_filter_options", return_value=options
            ), patch("regional_entrepreneurship_intelligence.dashboard.health.load_dataset") as load:
                load.side_effect = lambda name, data_dir: pd.DataFrame(
                    columns=sorted((REQUIRED_FIELDS[name] - {"target_year"}) if name == "model_predictions" else REQUIRED_FIELDS[name])
                )
                result = check_dashboard_health(root)
        self.assertFalse(result["healthy"])
        failure = next(check for check in result["checks"] if check["name"] == "dashboard_model_predictions")
        self.assertIn("target_year", failure["detail"])

    def test_all_artifacts_with_valid_metadata_and_fields_pass_health(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in REQUIRED_ARTIFACTS:
                (root / name).touch()
            for name in REQUIRED_DATASETS:
                (root / f"dashboard_{name}.parquet").touch()
            metadata = {
                "dashboard_data_version": "1.0.0",
                "study_period": {"descriptive": [2010, 2023]},
                "primary_model": "logistic",
                "forecast_horizon_years": 3,
                "final_A6_commit": "test",
            }
            options = {
                "msa_options": [], "sector_options": [], "year_options": [],
                "risk_category_options": [], "observed_historical_gap_status_options": [],
            }
            with patch("regional_entrepreneurship_intelligence.dashboard.health.load_dashboard_metadata", return_value=metadata), patch(
                "regional_entrepreneurship_intelligence.dashboard.health.load_filter_options", return_value=options
            ), patch("regional_entrepreneurship_intelligence.dashboard.health.load_dataset") as load:
                load.side_effect = lambda name, data_dir: pd.DataFrame(columns=sorted(REQUIRED_FIELDS[name]))
                result = check_dashboard_health(root)
        self.assertTrue(result["healthy"], json.dumps(result, indent=2))


if __name__ == "__main__":
    unittest.main()
