"""BDS source profiling and raw-ingestion helpers for Assignment 4.5.

This module preserves Census BDS source-native rows in ``raw_bds``. It does
not standardize geography, standardize NAICS, calculate rates, or create lags.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from regional_entrepreneurship_intelligence.database.connection import (
    DEFAULT_DATABASE_PATH,
    PROJECT_ROOT,
    connect_database,
)
from regional_entrepreneurship_intelligence.database.metadata import (
    finish_pipeline_run,
    insert_source_manifest,
    start_pipeline_run,
)
from regional_entrepreneurship_intelligence.database.reference import seed_reference_data
from regional_entrepreneurship_intelligence.database.schema import create_schema


BDS_MSA_SECTOR_PRODUCT = "Business Dynamics Statistics: MSA by Sector"
BDS_MSA_SECTOR_RELEASE = "2023 BDS release, 1978-2023 time series"
BDS_MSA_SECTOR_BULK_URL = (
    "https://www2.census.gov/programs-surveys/bds/tables/time-series/2023/"
    "bds2023_msa_sec.csv"
)
BDS_MSA_SECTOR_FIRM_AGE_PRODUCT = (
    "Business Dynamics Statistics: MSA by Sector by Firm Age Coarse"
)
BDS_MSA_SECTOR_FIRM_AGE_BULK_URL = (
    "https://www2.census.gov/programs-surveys/bds/tables/time-series/2023/"
    "bds2023_msa_sec_fac.csv"
)
BDS_SAMPLE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "bds"
    / "sample"
    / "bds2023_msa_sec_sample_2010_2023.csv"
)
BDS_FIRM_AGE_SAMPLE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "bds"
    / "sample"
    / "bds2023_msa_sec_fac_sample_2010_2023.csv"
)
STUDY_YEARS = set(range(2010, 2024))

REQUIRED_BDS_COLUMNS = {
    "year",
    "msa",
    "sector",
    "firms",
    "estabs",
    "emp",
    "denom",
    "estabs_entry",
    "job_creation_births",
}
REQUIRED_BDS_FIRM_AGE_COLUMNS = REQUIRED_BDS_COLUMNS | {"fagecoarse"}

BDS_STATUS_VALUES = {"D", "N", "S", "X"}
BDS_SUPPRESSION_VALUES = {"D", "S"}


@dataclass(frozen=True)
class BDSRawLoadResult:
    """Summary returned by BDS raw ingestion."""

    manifest_id: int
    pipeline_run_id: str
    rows_read: int
    rows_inserted: int
    rows_skipped_existing: int
    raw_row_count: int
    study_window_row_count: int
    suppressed_or_unavailable_row_count: int


@dataclass(frozen=True)
class BDSFirmAgeRawLoadResult:
    """Summary returned by BDS firm-age raw ingestion."""

    manifest_id: int
    pipeline_run_id: str
    rows_read: int
    rows_inserted: int
    rows_skipped_existing: int
    raw_row_count: int
    age0_row_count: int
    suppressed_or_unavailable_row_count: int


def read_bds_csv(csv_path: str | Path) -> list[dict[str, str]]:
    """Read a BDS CSV file while preserving all source values as strings."""
    path = Path(csv_path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    validate_bds_rows(rows, fieldnames=reader.fieldnames or [])
    return rows


def read_bds_firm_age_csv(csv_path: str | Path) -> list[dict[str, str]]:
    """Read a BDS firm-age CSV file while preserving source values."""
    path = Path(csv_path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    validate_bds_firm_age_rows(rows, fieldnames=reader.fieldnames or [])
    return rows


def validate_bds_rows(
    rows: list[dict[str, str]],
    *,
    fieldnames: list[str],
) -> None:
    """Validate required source-native BDS fields without transforming rows."""
    missing_columns = REQUIRED_BDS_COLUMNS - set(fieldnames)
    if missing_columns:
        raise ValueError(f"Missing required BDS columns: {sorted(missing_columns)}")
    if not rows:
        raise ValueError("BDS source contains no data rows")

    years = set()
    for index, row in enumerate(rows, start=1):
        year = row.get("year", "").strip()
        msa = row.get("msa", "").strip()
        sector = row.get("sector", "").strip()
        if not year.isdigit():
            raise ValueError(f"Invalid BDS year at row {index}: {year}")
        if not msa:
            raise ValueError(f"Blank BDS MSA at row {index}")
        if not sector:
            raise ValueError(f"Blank BDS sector at row {index}")
        years.add(int(year))

    if not years & STUDY_YEARS:
        raise ValueError("BDS rows do not overlap the 2010-2023 study window")


def validate_bds_firm_age_rows(
    rows: list[dict[str, str]],
    *,
    fieldnames: list[str],
) -> None:
    """Validate required BDS firm-age fields without transforming rows."""
    missing_columns = REQUIRED_BDS_FIRM_AGE_COLUMNS - set(fieldnames)
    if missing_columns:
        raise ValueError(
            f"Missing required BDS firm-age columns: {sorted(missing_columns)}"
        )
    validate_bds_rows(rows, fieldnames=fieldnames)
    if not any(row.get("fagecoarse") == "a) 0" for row in rows):
        raise ValueError("BDS firm-age source does not include the age-0 category")


def load_bds_raw(
    connection: sqlite3.Connection,
    csv_path: str | Path = BDS_SAMPLE_PATH,
    *,
    official_source_url: str = BDS_MSA_SECTOR_BULK_URL,
    source_version: str = BDS_MSA_SECTOR_RELEASE,
    source_year: int = 2023,
) -> BDSRawLoadResult:
    """Load BDS source-native CSV rows into ``raw_bds`` idempotently."""
    path = Path(csv_path)
    rows = read_bds_csv(path)
    seed_reference_data(connection)

    manifest_id = _ensure_bds_manifest(
        connection,
        path,
        official_source_url=official_source_url,
        source_version=source_version,
        source_year=source_year,
        row_count=len(rows),
    )
    run_id = start_pipeline_run(connection, stage="raw_bds_ingestion")
    inserted = 0
    skipped = 0
    try:
        with connection:
            for row in rows:
                source_row_identifier = bds_source_row_identifier(row)
                existing = connection.execute(
                    """
                    SELECT raw_bds_id
                    FROM raw_bds
                    WHERE raw_source_filename = ?
                      AND source_row_identifier = ?;
                    """,
                    (path.name, source_row_identifier),
                ).fetchone()
                if existing:
                    skipped += 1
                    continue
                connection.execute(
                    """
                    INSERT INTO raw_bds (
                        manifest_id,
                        pipeline_run_id,
                        source_year,
                        source_geography_id,
                        source_industry_id,
                        source_naics_version,
                        source_row_identifier,
                        raw_source_filename,
                        is_suppressed,
                        raw_payload,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        manifest_id,
                        run_id,
                        int(row["year"]),
                        row["msa"],
                        row["sector"],
                        "BDS source-native sector coding; not standardized to 2022 NAICS in A4.5",
                        source_row_identifier,
                        path.name,
                        1 if row_has_suppression(row) else 0,
                        json.dumps(row, sort_keys=True),
                        "Loaded source-native BDS MSA by sector row; no standardization applied.",
                    ),
                )
                inserted += 1
        finish_pipeline_run(
            connection,
            run_id,
            records_read=len(rows),
            records_written=inserted,
            records_rejected=0,
            warnings=(
                f"Skipped {skipped} existing raw rows during idempotent rerun."
                if skipped
                else None
            ),
        )
    except Exception as exc:
        finish_pipeline_run(
            connection,
            run_id,
            status="failed",
            records_read=len(rows),
            records_written=inserted,
            records_rejected=0,
            error_message=str(exc),
        )
        raise

    raw_row_count = connection.execute("SELECT COUNT(*) FROM raw_bds;").fetchone()[0]
    study_window_row_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM raw_bds
        WHERE source_year BETWEEN 2010 AND 2023;
        """
    ).fetchone()[0]
    suppressed_or_unavailable = sum(row_has_status_value(row) for row in rows)

    return BDSRawLoadResult(
        manifest_id=manifest_id,
        pipeline_run_id=run_id,
        rows_read=len(rows),
        rows_inserted=inserted,
        rows_skipped_existing=skipped,
        raw_row_count=raw_row_count,
        study_window_row_count=study_window_row_count,
        suppressed_or_unavailable_row_count=suppressed_or_unavailable,
    )


def load_bds_firm_age_raw(
    connection: sqlite3.Connection,
    csv_path: str | Path = BDS_FIRM_AGE_SAMPLE_PATH,
    *,
    official_source_url: str = BDS_MSA_SECTOR_FIRM_AGE_BULK_URL,
    source_version: str = BDS_MSA_SECTOR_RELEASE,
    source_year: int = 2023,
) -> BDSFirmAgeRawLoadResult:
    """Load BDS source-native firm-age rows into ``raw_bds_firm_age``."""
    path = Path(csv_path)
    rows = read_bds_firm_age_csv(path)
    seed_reference_data(connection)

    manifest_id = _ensure_bds_manifest(
        connection,
        path,
        official_source_url=official_source_url,
        source_version=source_version,
        source_year=source_year,
        row_count=len(rows),
        dataset_name=BDS_MSA_SECTOR_FIRM_AGE_PRODUCT,
        access_method=(
            "official bulk CSV sample derived from Census BDS MSA by Sector "
            "by Firm Age Coarse bulk file"
        ),
    )
    run_id = start_pipeline_run(connection, stage="raw_bds_firm_age_ingestion")
    inserted = 0
    skipped = 0
    try:
        with connection:
            for row in rows:
                source_row_identifier = bds_firm_age_source_row_identifier(row)
                existing = connection.execute(
                    """
                    SELECT raw_bds_firm_age_id
                    FROM raw_bds_firm_age
                    WHERE raw_source_filename = ?
                      AND source_row_identifier = ?;
                    """,
                    (path.name, source_row_identifier),
                ).fetchone()
                if existing:
                    skipped += 1
                    continue
                connection.execute(
                    """
                    INSERT INTO raw_bds_firm_age (
                        manifest_id,
                        pipeline_run_id,
                        source_year,
                        source_geography_id,
                        source_industry_id,
                        source_fagecoarse,
                        source_naics_version,
                        source_row_identifier,
                        raw_source_filename,
                        is_suppressed,
                        raw_payload,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        manifest_id,
                        run_id,
                        int(row["year"]),
                        row["msa"],
                        row["sector"],
                        row["fagecoarse"],
                        "BDS source-native sector coding; Census BDS uses 2017 NAICS",
                        source_row_identifier,
                        path.name,
                        1 if row_has_suppression(row) else 0,
                        json.dumps(row, sort_keys=True),
                        "Loaded source-native BDS firm-age row; no standardization applied.",
                    ),
                )
                inserted += 1
        finish_pipeline_run(
            connection,
            run_id,
            records_read=len(rows),
            records_written=inserted,
            records_rejected=0,
            warnings=(
                f"Skipped {skipped} existing firm-age raw rows during idempotent rerun."
                if skipped
                else None
            ),
        )
    except Exception as exc:
        finish_pipeline_run(
            connection,
            run_id,
            status="failed",
            records_read=len(rows),
            records_written=inserted,
            records_rejected=0,
            error_message=str(exc),
        )
        raise

    raw_row_count = connection.execute(
        "SELECT COUNT(*) FROM raw_bds_firm_age;"
    ).fetchone()[0]
    age0_row_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM raw_bds_firm_age
        WHERE source_fagecoarse = 'a) 0';
        """
    ).fetchone()[0]

    return BDSFirmAgeRawLoadResult(
        manifest_id=manifest_id,
        pipeline_run_id=run_id,
        rows_read=len(rows),
        rows_inserted=inserted,
        rows_skipped_existing=skipped,
        raw_row_count=raw_row_count,
        age0_row_count=age0_row_count,
        suppressed_or_unavailable_row_count=sum(row_has_status_value(row) for row in rows),
    )


def bds_source_row_identifier(row: dict[str, str]) -> str:
    """Build a deterministic source-native row identifier."""
    parts = [
        "bds2023_msa_sec",
        f"year={row['year']}",
        f"msa={row['msa']}",
        f"sector={row['sector']}",
    ]
    return "|".join(parts)


def bds_firm_age_source_row_identifier(row: dict[str, str]) -> str:
    """Build a deterministic source-native firm-age row identifier."""
    return "|".join(
        [
            "bds2023_msa_sec_fac",
            f"year={row['year']}",
            f"msa={row['msa']}",
            f"sector={row['sector']}",
            f"fagecoarse={row['fagecoarse']}",
        ]
    )


def row_has_suppression(row: dict[str, str]) -> bool:
    """Return true when a source row contains Census suppression flags."""
    return any(value in BDS_SUPPRESSION_VALUES for value in row.values())


def row_has_status_value(row: dict[str, str]) -> bool:
    """Return true when a source row contains D, N, S, or X status values."""
    return any(value in BDS_STATUS_VALUES for value in row.values())


def _ensure_bds_manifest(
    connection: sqlite3.Connection,
    csv_path: Path,
    *,
    official_source_url: str,
    source_version: str,
    source_year: int,
    row_count: int,
    dataset_name: str = BDS_MSA_SECTOR_PRODUCT,
    access_method: str = "official bulk CSV sample derived from Census BDS bulk file",
) -> int:
    checksum = _sha256(csv_path)
    existing = connection.execute(
        """
        SELECT manifest_id
        FROM metadata_source_manifest
        WHERE raw_filename = ?
          AND file_checksum = ?
          AND source_url_or_endpoint = ?;
        """,
        (csv_path.name, checksum, official_source_url),
    ).fetchone()
    if existing:
        return int(existing[0])

    source_id = connection.execute(
        """
        SELECT source_id
        FROM ref_source
        WHERE source_name = 'Census Business Dynamics Statistics (BDS)';
        """
    ).fetchone()[0]
    return insert_source_manifest(
        connection,
        source_id=source_id,
        source_name="Census Business Dynamics Statistics (BDS)",
        source_agency="U.S. Census Bureau",
        dataset_name=dataset_name,
        access_method=access_method,
        source_url_or_endpoint=official_source_url,
        source_year=source_year,
        source_version=source_version,
        raw_filename=csv_path.name,
        file_checksum=checksum,
        row_count=row_count,
        notes=(
            "A4.5 committed sample derived from the official BDS MSA by Sector "
            "or MSA by Sector by Firm Age Coarse bulk CSV. Full national raw "
            "files are not committed."
        ),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    """CLI entry point for sample/raw BDS ingestion."""
    parser = argparse.ArgumentParser(description="Load source-native BDS raw rows.")
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=BDS_SAMPLE_PATH,
        help="Path to a source-native BDS CSV extract or permitted sample.",
    )
    parser.add_argument(
        "--firm-age-csv-path",
        type=Path,
        default=None,
        help="Optional path to a source-native BDS firm-age CSV extract or sample.",
    )
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        create_schema(connection)
        result = load_bds_raw(connection, args.csv_path)
        firm_age_result = (
            load_bds_firm_age_raw(connection, args.firm_age_csv_path)
            if args.firm_age_csv_path is not None
            else None
        )
    print(
        "Loaded BDS raw rows: "
        f"read={result.rows_read}, "
        f"inserted={result.rows_inserted}, "
        f"skipped_existing={result.rows_skipped_existing}, "
        f"raw_bds={result.raw_row_count}, "
        f"manifest_id={result.manifest_id}"
    )
    if firm_age_result is not None:
        print(
            "Loaded BDS firm-age raw rows: "
            f"read={firm_age_result.rows_read}, "
            f"inserted={firm_age_result.rows_inserted}, "
            f"skipped_existing={firm_age_result.rows_skipped_existing}, "
            f"raw_bds_firm_age={firm_age_result.raw_row_count}, "
            f"manifest_id={firm_age_result.manifest_id}"
        )


if __name__ == "__main__":
    main()
