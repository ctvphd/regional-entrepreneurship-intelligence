"""Cached Streamlit adapters around the pure A7.2 artifact loader."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from .health import check_dashboard_health
from .loader import DATA_DIR, load_dashboard_labels, load_dashboard_metadata, load_dataset, load_filter_options


@st.cache_data(show_spinner=False)
def cached_health(data_dir: str = str(DATA_DIR)) -> dict:
    return check_dashboard_health(Path(data_dir))


@st.cache_data(show_spinner=False)
def cached_dataset(name: str, data_dir: str = str(DATA_DIR)):
    return load_dataset(name, data_dir=Path(data_dir))


@st.cache_data(show_spinner=False)
def cached_metadata(data_dir: str = str(DATA_DIR)) -> dict:
    return load_dashboard_metadata(data_dir=Path(data_dir))


@st.cache_data(show_spinner=False)
def cached_filter_options(data_dir: str = str(DATA_DIR)) -> dict:
    return load_filter_options(data_dir=Path(data_dir))


@st.cache_data(show_spinner=False)
def cached_labels(data_dir: str = str(DATA_DIR)) -> dict:
    return load_dashboard_labels(data_dir=Path(data_dir))
