"""Validate required, finalized dashboard artifacts without querying SQLite."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .constants import REQUIRED_ARTIFACTS, REQUIRED_DATASETS
from .loader import DATA_DIR, load_dashboard_metadata, load_dataset, load_filter_options

REQUIRED_FIELDS = {
    "msa_industry_year": {"cbsa_code", "sector_code", "year", "startup_rate"},
    "model_predictions": {"cbsa_code", "sector_code", "predictor_year", "target_year", "logistic_probability"},
    "model_summary": {"dataset_split", "model", "metric", "value"},
    "calibration": {"dataset_split", "model", "risk_bin"},
    "model_by_year": {"predictor_year", "target_year", "model"},
    "model_by_sector": {"sector_code", "model"},
    "model_by_msa_size": {"msa_size_group", "model"},
    "coverage": {"cbsa_code", "coverage_status"},
    "sources": {"source_name", "dataset"},
}


def check_dashboard_health(data_dir: Path = DATA_DIR) -> dict:
    checks = []
    for name in REQUIRED_ARTIFACTS:
        path = data_dir / name
        checks.append({"name": name, "passed": path.is_file(), "detail": "found" if path.is_file() else "missing"})
    for name in REQUIRED_DATASETS:
        path = data_dir / f"dashboard_{name}.parquet"
        if not path.is_file():
            checks.append({"name": f"dashboard_{name}", "passed": False, "detail": "missing"})
            continue
        try:
            frame = load_dataset(name, data_dir=data_dir)
            missing = sorted(REQUIRED_FIELDS[name] - set(frame.columns))
            passed = not missing
            detail = f"{len(frame)} rows" if passed else f"missing required fields: {', '.join(missing)}"
            checks.append({"name": f"dashboard_{name}", "passed": passed, "detail": detail, "row_count": len(frame)})
        except Exception as exc:  # health output should report a bad artifact, not crash
            checks.append({"name": f"dashboard_{name}", "passed": False, "detail": f"unreadable: {exc}"})
    try:
        metadata = load_dashboard_metadata(data_dir=data_dir)
        if not isinstance(metadata, dict):
            raise ValueError("metadata root must be a JSON object")
        version = metadata.get("dashboard_data_version", "")
        version_ok = isinstance(version, str) and bool(re.fullmatch(r"\d+\.\d+\.\d+", version))
        checks.append({"name": "metadata_version", "passed": version_ok, "detail": version or "missing"})
        for field in ("study_period", "primary_model", "forecast_horizon_years", "final_A6_commit"):
            checks.append({"name": f"metadata_{field}", "passed": field in metadata, "detail": "present" if field in metadata else "missing"})
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        checks.append({"name": "metadata_readable", "passed": False, "detail": f"unreadable: {exc}"})
    try:
        options = load_filter_options(data_dir=data_dir)
        passed = isinstance(options, dict) and all(
            key in options
            for key in (
                "msa_options",
                "sector_options",
                "year_options",
                "risk_category_options",
                "observed_historical_gap_status_options",
            )
        )
        checks.append({"name": "filter_options", "passed": passed, "detail": "valid keys" if passed else "required option groups missing"})
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        checks.append({"name": "filter_options", "passed": False, "detail": f"unreadable: {exc}"})
    return {"healthy": all(check["passed"] for check in checks), "checks": checks}


def main() -> int:
    result = check_dashboard_health()
    print("Dashboard health: " + ("PASS" if result["healthy"] else "FAIL"))
    for check in result["checks"]:
        print(f"{'PASS' if check['passed'] else 'FAIL'} {check['name']}: {check['detail']}")
    return 0 if result["healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
