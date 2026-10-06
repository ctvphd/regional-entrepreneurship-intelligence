"""Pure-Python, read-only loaders for validated dashboard artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "dashboard"
DATASETS = {
    "msa_industry_year", "model_predictions", "model_summary", "calibration",
    "model_by_year", "model_by_sector", "model_by_msa_size", "coverage", "sources",
}


def load_dataset(name: str, *, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Load one allow-listed Parquet artifact without mutating source data."""
    if name not in DATASETS:
        raise ValueError(f"Unknown dashboard dataset: {name}")
    path = data_dir / f"dashboard_{name}.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"Dashboard data is not built yet: {path.name}")
    return pd.read_parquet(path, engine="pyarrow")


def load_msa_industry_year(*, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return load_dataset("msa_industry_year", data_dir=data_dir)


def load_model_predictions(*, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return load_dataset("model_predictions", data_dir=data_dir)


def load_model_summary(*, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return load_dataset("model_summary", data_dir=data_dir)


def load_calibration(*, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return load_dataset("calibration", data_dir=data_dir)


def load_coverage(*, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return load_dataset("coverage", data_dir=data_dir)


def load_sources(*, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return load_dataset("sources", data_dir=data_dir)


def load_dashboard_metadata(*, data_dir: Path = DATA_DIR) -> dict:
    path = data_dir / "dashboard_metadata.json"
    if not path.is_file():
        raise FileNotFoundError("Dashboard metadata is not built yet")
    return json.loads(path.read_text(encoding="utf-8"))


def load_dashboard_labels(*, data_dir: Path = DATA_DIR) -> dict:
    path = data_dir / "dashboard_labels.json"
    if not path.is_file():
        raise FileNotFoundError("Dashboard labels are not built yet")
    return json.loads(path.read_text(encoding="utf-8"))


def load_filter_options(*, data_dir: Path = DATA_DIR) -> dict:
    path = data_dir / "dashboard_filter_options.json"
    if not path.is_file():
        raise FileNotFoundError("Dashboard filter options are not built yet")
    return json.loads(path.read_text(encoding="utf-8"))
