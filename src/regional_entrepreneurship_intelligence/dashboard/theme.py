"""Streamlit page setup and restrained project theme."""

from __future__ import annotations

import streamlit as st

from .constants import APP_TITLE


def configure_page() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=":material/monitoring:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
