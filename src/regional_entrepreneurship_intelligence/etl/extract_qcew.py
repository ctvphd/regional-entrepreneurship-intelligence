"""QCEW source profiling and raw-ingestion helpers for Assignment 4.7.

This module preserves source-native annual QCEW rows in ``raw_qcew``. It does
not aggregate counties to CBSAs, standardize NAICS, calculate growth rates, or
create lags.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

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
from regional_entrepreneurship_intelligence.database.naics_versions import source_year_naics
from regional_entrepreneurship_intelligence.database.schema import create_schema


QCEW_SAMPLE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "qcew"
    / "sample"
    / "qcew_annual_area_sample_2022_2023.csv"
)
QCEW_ANNUAL_BY_AREA_URL_PATTERN = (
    "https://data.bls.gov/cew/data/files/{year}/csv/{year}_annual_by_area.zip"
)
QCEW_SAMPLE_ACCESS_URL = (
    "https://data.bls.gov/cew/data/api/{year}/a/area/{area_fips}.csv"
)
QCEW_PRODUCT = "QCEW NAICS-Based Annual CSV Data, Area Slices"
QCEW_RELEASE = "QCEW annual CSV open data, 2022-2023 sample"

REQUIRED_QCEW_COLUMNS = {
    "area_fips",
    "own_code",
    "industry_code",
    "agglvl_code",
    "size_code",
    "year",
    "qtr",
    "disclosure_code",
    "annual_avg_estabs",
    "annual_avg_emplvl",
    "total_annual_wages",
    "avg_annual_pay",
}

@dataclass(frozen=True)
class QCEWRawLoadResult:
    """Summary returned by QCEW raw ingestion."""

    manifest_id: int
    pipeline_run_id: str
    rows_read: int
    rows_inserted: int
    rows_skipped_existing: int
    raw_row_count: int
    suppressed_or_status_row_count: int


def read_qcew_csv(csv_path: str | Path) -> list[dict[str, str]]:
    """Read a QCEW CSV while preserving source values as strings."""
    path = Path(csv_path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    validate_qcew_rows(rows, fieldnames=reader.fieldnames or [])
    return rows


def validate_qcew_rows(rows: list[dict[str, str]], *, fieldnames: list[str]) -> None:
    """Validate required annual QCEW fields without transforming rows."""
    missing_columns = REQUIRED_QCEW_COLUMNS - set(fieldnames)
    if missing_columns:
        raise ValueError(f"Missing required QCEW columns: {sorted(missing_columns)}")
    if not rows:
        raise ValueError("QCEW source contains no data rows")

    for index, row in enumerate(rows, start=1):
        if not row.get("year", "").isdigit():
            raise ValueError(f"Invalid QCEW year at row {index}: {row.get('year')}")
        for field in (
            "area_fips",
            "own_code",
            "industry_code",
            "annual_avg_estabs",
            "annual_avg_emplvl",
            "total_annual_wages",
            "avg_annual_pay",
        ):
            if row.get(field) is None:
                raise ValueError(f"Missing QCEW field {field} at row {index}")


def load_qcew_raw(
    connection: sqlite3.Connection,
    csv_path: str | Path = QCEW_SAMPLE_PATH,
    *,
    official_source_url: str = "official QCEW annual area CSV slices",
    source_version: str = QCEW_RELEASE,
) -> QCEWRawLoadResult:
    """Load source-native annual QCEW rows into ``raw_qcew`` idempotently."""
    path = Path(csv_path)
    rows = read_qcew_csv(path)
    seed_reference_data(connection)
    manifest_id = _ensure_qcew_manifest(
        connection,
        path,
        official_source_url=official_source_url,
        source_version=source_version,
        row_count=len(rows),
        source_year=int(rows[0]["year"]) if len({row["year"] for row in rows}) == 1 else None,
    )
    run_id = start_pipeline_run(connection, stage="raw_qcew_ingestion")
    inserted = 0
    skipped = 0
    existing_rows = {
        row[0] for row in connection.execute(
            "SELECT source_row_identifier FROM raw_qcew WHERE raw_source_filename = ?;",
            (path.name,),
        )
    }
    try:
        with connection:
            for row in rows:
                source_row_identifier = qcew_source_row_identifier(row)
                if source_row_identifier in existing_rows:
                    skipped += 1
                    continue
                connection.execute(
                    """
                    INSERT INTO raw_qcew (
                        manifest_id,
                        pipeline_run_id,
                        source_year,
                        source_geography_id,
                        source_industry_id,
                        source_ownership_code,
                        source_size_code,
                        source_naics_version,
                        source_row_identifier,
                        raw_source_filename,
                        disclosure_code,
                        annual_avg_estabs,
                        annual_avg_emplvl,
                        total_annual_wages,
                        avg_annual_pay,
                        is_suppressed,
                        raw_payload,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        manifest_id,
                        run_id,
                        int(row["year"]),
                        row["area_fips"],
                        row["industry_code"],
                        row["own_code"],
                        row["size_code"],
                        source_year_naics("QCEW", int(row["year"])).native_version,
                        source_row_identifier,
                        path.name,
                        row.get("disclosure_code", ""),
                        row.get("annual_avg_estabs", ""),
                        row.get("annual_avg_emplvl", ""),
                        row.get("total_annual_wages", ""),
                        row.get("avg_annual_pay", ""),
                        1 if row_has_status(row) else 0,
                        json.dumps(row, sort_keys=True),
                        "Loaded source-native annual QCEW row; no growth calculation or standardization applied.",
                    ),
                )
                inserted += 1
                existing_rows.add(source_row_identifier)
        finish_pipeline_run(
            connection,
            run_id,
            records_read=len(rows),
            records_written=inserted,
            records_rejected=0,
            warnings=(
                f"Skipped {skipped} existing QCEW raw rows during idempotent rerun."
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

    raw_row_count = connection.execute("SELECT COUNT(*) FROM raw_qcew;").fetchone()[0]
    return QCEWRawLoadResult(
        manifest_id=manifest_id,
        pipeline_run_id=run_id,
        rows_read=len(rows),
        rows_inserted=inserted,
        rows_skipped_existing=skipped,
        raw_row_count=raw_row_count,
        suppressed_or_status_row_count=sum(row_has_status(row) for row in rows),
    )


def qcew_source_row_identifier(row: dict[str, str]) -> str:
    """Build a deterministic source-native QCEW row identifier."""
    return "|".join(
        [
            "qcew_annual_area",
            f"year={row['year']}",
            f"area={row['area_fips']}",
            f"own={row['own_code']}",
            f"industry={row['industry_code']}",
            f"size={row['size_code']}",
            f"qtr={row['qtr']}",
        ]
    )


def row_has_status(row: dict[str, str]) -> bool:
    """Annual suppression is distinct from LQ and over-the-year status."""
    return bool((row.get("disclosure_code") or "").strip())


def _ensure_qcew_manifest(
    connection: sqlite3.Connection,
    csv_path: Path,
    *,
    official_source_url: str,
    source_version: str,
    row_count: int,
    source_year: int | None,
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
        WHERE source_name = 'BLS Quarterly Census of Employment and Wages (QCEW)';
        """
    ).fetchone()[0]
    return insert_source_manifest(
        connection,
        source_id=source_id,
        source_name="BLS Quarterly Census of Employment and Wages (QCEW)",
        source_agency="U.S. Bureau of Labor Statistics",
        dataset_name=QCEW_PRODUCT,
        access_method="official BLS annual by-area ZIP county-sector extract",
        source_url_or_endpoint=official_source_url,
        source_year=source_year,
        source_version=source_version,
        raw_filename=csv_path.name,
        file_checksum=checksum,
        row_count=row_count,
        notes=(
            "Local production extract from the official annual by-area ZIP; "
            "county, private ownership, all establishment sizes, annual rows, "
            "and selected broad sectors only. Extract checksum and selected-row "
            "count are recorded; original ZIP archives remain Git-ignored."
        ),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    """CLI entry point for QCEW raw ingestion."""
    parser = argparse.ArgumentParser(description="Load source-native QCEW raw rows.")
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=QCEW_SAMPLE_PATH,
        help="Path to a source-native QCEW CSV extract or permitted sample.",
    )
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        create_schema(connection)
        result = load_qcew_raw(connection, args.csv_path)
    print(
        "Loaded QCEW raw rows: "
        f"read={result.rows_read}, "
        f"inserted={result.rows_inserted}, "
        f"skipped_existing={result.rows_skipped_existing}, "
        f"raw_qcew={result.raw_row_count}, "
        f"manifest_id={result.manifest_id}"
    )


if __name__ == "__main__":
    main()
