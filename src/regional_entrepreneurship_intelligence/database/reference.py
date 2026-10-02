"""Reference-table seed helpers for Assignment 4.3.

This module only loads deterministic project reference rows. It does not
download, ingest, or synthesize live source data.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from regional_entrepreneurship_intelligence.database.schema import seed_ref_year


APPROVED_SOURCES: tuple[dict[str, str | None], ...] = (
    {
        "source_name": "Census Business Dynamics Statistics (BDS)",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "Business Dynamics Statistics",
        "default_access_method": "API or bulk file",
        "homepage_url": None,
        "notes": "Source URL or endpoint will be verified during BDS-specific ingestion.",
    },
    {
        "source_name": "BLS Quarterly Census of Employment and Wages (QCEW)",
        "source_agency": "U.S. Bureau of Labor Statistics",
        "dataset_name": "Quarterly Census of Employment and Wages",
        "default_access_method": "official bulk files",
        "homepage_url": None,
        "notes": "Bulk-file location will be verified during QCEW-specific ingestion.",
    },
    {
        "source_name": "Census County Business Patterns (CBP)",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "County Business Patterns",
        "default_access_method": "API initially; bulk files if needed",
        "homepage_url": None,
        "notes": "Source URL or endpoint will be verified during CBP-specific ingestion.",
    },
    {
        "source_name": "American Community Survey (ACS)",
        "source_agency": "U.S. Census Bureau",
        "dataset_name": "American Community Survey",
        "default_access_method": "API",
        "homepage_url": None,
        "notes": "Source URL or endpoint will be verified during ACS-specific ingestion.",
    },
)


def seed_ref_source(connection: sqlite3.Connection) -> None:
    """Populate the approved source registry without fetching source records."""
    connection.executemany(
        """
        INSERT INTO ref_source (
            source_name,
            source_agency,
            dataset_name,
            default_access_method,
            homepage_url,
            notes
        )
        VALUES (
            :source_name,
            :source_agency,
            :dataset_name,
            :default_access_method,
            :homepage_url,
            :notes
        )
        ON CONFLICT(source_name) DO UPDATE SET
            source_agency = excluded.source_agency,
            dataset_name = excluded.dataset_name,
            default_access_method = excluded.default_access_method,
            homepage_url = excluded.homepage_url,
            notes = excluded.notes;
        """,
        APPROVED_SOURCES,
    )


def seed_reference_data(connection: sqlite3.Connection) -> None:
    """Seed deterministic reference tables that are verified for A4.3.

    Geography and industry references are intentionally not populated here.
    Those tables require authoritative CBSA and NAICS reference/crosswalk files
    that have not yet been added to the repository.
    """
    connection.execute("PRAGMA foreign_keys = ON;")
    with connection:
        seed_ref_year(connection)
        seed_ref_source(connection)


def get_reference_counts(connection: sqlite3.Connection) -> dict[str, int]:
    """Return row counts for all reference tables."""
    tables = ("ref_year", "ref_source", "ref_geography", "ref_industry")
    return {
        table: int(
            connection.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
        )
        for table in tables
    }


def list_approved_source_names() -> tuple[str, ...]:
    """Return the approved source names in deterministic order."""
    return tuple(str(source["source_name"]) for source in APPROVED_SOURCES)


def approved_source_by_name(source_name: str) -> dict[str, Any]:
    """Return one approved source definition by name."""
    for source in APPROVED_SOURCES:
        if source["source_name"] == source_name:
            return dict(source)
    raise KeyError(f"Unknown approved source: {source_name}")
