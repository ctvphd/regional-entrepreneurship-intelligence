from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from regional_entrepreneurship_intelligence.etl.run_pipeline import run_pipeline
from regional_entrepreneurship_intelligence.database.connection import PROJECT_ROOT


class ProductionPreflightTest(unittest.TestCase):
    def test_missing_cache_fails_before_database_or_log_creation_with_exact_paths(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "data" / "review") as temporary:
            root = Path(temporary)
            missing = [root / "bds.csv", root / "qcew.zip", root / "acs.csv"]
            database, logs = root / "production.sqlite", root / "logs"
            with patch("regional_entrepreneurship_intelligence.etl.run_pipeline.required_production_inputs", return_value=missing):
                with self.assertRaises(FileNotFoundError) as raised:
                    run_pipeline(database, log_dir=logs)
            message = str(raised.exception)
            self.assertIn("Required inputs: 3; present: 0; missing: 3", message)
            self.assertIn("Production reproduction requires the authorized local source cache", message)
            for path in missing:
                self.assertIn(str(path), message)
            self.assertFalse(database.exists())
            self.assertFalse(logs.exists())


if __name__ == "__main__":
    unittest.main()
