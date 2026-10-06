"""Multipage Streamlit shell consuming only finalized A7.2 artifacts."""

from __future__ import annotations

import streamlit as st

from .constants import DATA_LAYER_REBUILD_COMMAND
from .data_access import cached_health, cached_metadata
from .loader import DATA_DIR
from .pages import about, explorer, overview, performance, quality
from .theme import configure_page


def main() -> None:
    configure_page()
    health = cached_health()
    if not health["healthy"]:
        st.error("Dashboard data is missing or invalid. Rebuild the A7.2 data layer, then reload this page.")
        st.code(DATA_LAYER_REBUILD_COMMAND, language="powershell")
        with st.expander("Health check details"):
            st.json(health)
        st.stop()

    # Pages read validated dashboard artifacts and narrowly scoped frozen reports.
    navigation = st.navigation(
        [
            st.Page(overview.render, title="Overview", url_path="overview", icon=":material/space_dashboard:", default=True),
            st.Page(explorer.render, title="Explore Markets", url_path="explorer", icon=":material/search:"),
            st.Page(performance.render, title="Model Insights", url_path="performance", icon=":material/assessment:"),
            st.Page(quality.render, title="Data & Confidence", url_path="quality", icon=":material/fact_check:"),
            st.Page(about.render, title="About the Analysis", url_path="about", icon=":material/menu_book:"),
        ],
        position="sidebar",
    )
    navigation.run()
