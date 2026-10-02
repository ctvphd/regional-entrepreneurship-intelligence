"""CBP source profiling and raw-ingestion helpers for Assignment 4.10."""

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
from regional_entrepreneurship_intelligence.database.schema import create_schema


CBP_SAMPLE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "cbp"
    / "sample"
    / "cbp_county_sector_sample_2022_2023.csv"
)
CBP_PRODUCT = "County Business Patterns API"
CBP_RELEASE = "County Business Patterns API, 2022-2023 sample"
CBP_API_ENDPOINT_PATTERN = "https://api.census.gov/data/{year}/cbp"

REQUIRED_CBP_COLUMNS = {
    "source_year",
    "cbp_product",
    "state_fips",
    "county_fips",
    "county_geoid",
    "county_name",
    "source_industry_id",
    "source_industry_label",
    "source_naics_version",
    "legal_form_code",
    "employment_size_code",
    "establishments",
    "employment",
    "annual_payroll",
    "first_quarter_payroll",
    "official_api_url",
    "raw_response",
}

CBP_FLAG_COLUMNS = {
    "establishments_flag",
    "employment_flag",
    "annual_payroll_flag",
    "first_quarter_payroll_flag",
}


@dataclass(frozen=True)
class CBPRawLoadResult:
    """Summary returned by CBP raw ingestion."""

    manifest_id: int
    pipeline_run_id: str
    rows_read: int
    rows_inserted: int
    rows_skipped_existing: int
    raw_row_count: int
    flagged_row_count: int


def read_cbp_csv(csv_path: str | Path) -> list[dict[str, str]]:
    """Read a CBP sample CSV while preserving source values as strings."""
    path = Path(csv_path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    validate_cbp_rows(rows, fieldnames=reader.fieldnames or [])
    return rows


def validate_cbp_rows(rows: list[dict[str, str]], *, fieldnames: list[str]) -> None:
    """Validate required CBP fields without transforming rows."""
    missing_columns = REQUIRED_CBP_COLUMNS - set(fieldnames)
    if missing_columns:
        raise ValueError(f"Missing required CBP columns: {sorted(missing_columns)}")
    if not rows:
        raise ValueError("CBP source contains no data rows")
    for index, row in enumerate(rows, start=1):
        if not row.get("source_year", "").isdigit():
            raise ValueError(f"Invalid CBP year at row {index}: {row.get('source_year')}")
        if len(row.get("county_geoid", "")) != 5:
            raise ValueError(f"Invalid CBP county GEOID at row {index}")


def load_cbp_raw(
    connection: sqlite3.Connection,
    csv_path: str | Path = CBP_SAMPLE_PATH,
    *,
    official_source_url: str = "official Census CBP API endpoints embedded per row",
    source_version: str = CBP_RELEASE,
) -> CBPRawLoadResult:
    """Load source-native CBP rows into ``raw_cbp`` idempotently."""
    path = Path(csv_path)
    rows = read_cbp_csv(path)
    seed_reference_data(connection)
    manifest_id = _ensure_cbp_manifest(
        connection,
        path,
        official_source_url=official_source_url,
        source_version=source_version,
        row_count=len(rows),
    )
    run_id = start_pipeline_run(connection, stage="raw_cbp_ingestion")
    inserted = 0
    skipped = 0
    try:
        with connection:
            for row in rows:
                source_row_identifier = cbp_source_row_identifier(row)
                existing = connection.execute(
                    """
                    SELECT raw_cbp_id
                    FROM raw_cbp
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
                    INSERT INTO raw_cbp (
                        manifest_id,
                        pipeline_run_id,
                        source_year,
                        source_geography_id,
                        source_state_fips,
                        source_county_fips,
                        source_county_geoid,
                        source_industry_id,
                        source_industry_label,
                        source_naics_version,
                        legal_form_code,
                        employment_size_code,
                        source_row_identifier,
                        raw_source_filename,
                        establishments,
                        establishments_flag,
                        employment,
                        employment_flag,
                        annual_payroll,
                        annual_payroll_flag,
                        first_quarter_payroll,
                        first_quarter_payroll_flag,
                        is_suppressed,
                        raw_payload,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        manifest_id,
                        run_id,
                        int(row["source_year"]),
                        row["county_geoid"],
                        row["state_fips"],
                        row["county_fips"],
                        row["county_geoid"],
                        row["source_industry_id"],
                        row["source_industry_label"],
                        row["source_naics_version"],
                        row["legal_form_code"],
                        row["employment_size_code"],
                        source_row_identifier,
                        path.name,
                        row["establishments"],
                        row.get("establishments_flag", ""),
                        row["employment"],
                        row.get("employment_flag", ""),
                        row["annual_payroll"],
                        row.get("annual_payroll_flag", ""),
                        row["first_quarter_payroll"],
                        row.get("first_quarter_payroll_flag", ""),
                        1 if row_has_flag(row) else 0,
                        json.dumps(row, sort_keys=True),
                        "Loaded source-native CBP county-industry row; no aggregation applied.",
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
                f"Skipped {skipped} existing CBP raw rows during idempotent rerun."
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

    raw_row_count = connection.execute("SELECT COUNT(*) FROM raw_cbp;").fetchone()[0]
    return CBPRawLoadResult(
        manifest_id=manifest_id,
        pipeline_run_id=run_id,
        rows_read=len(rows),
        rows_inserted=inserted,
        rows_skipped_existing=skipped,
        raw_row_count=raw_row_count,
        flagged_row_count=sum(row_has_flag(row) for row in rows),
    )


def cbp_source_row_identifier(row: dict[str, str]) -> str:
    """Build a deterministic source-native CBP row identifier."""
    return "|".join(
        [
            "cbp_county",
            f"year={row['source_year']}",
            f"county={row['county_geoid']}",
            f"industry={row['source_industry_id']}",
            f"lfo={row['legal_form_code']}",
            f"empszes={row['employment_size_code']}",
        ]
    )


def row_has_flag(row: dict[str, str]) -> bool:
    """Return true when a CBP row contains disclosure/noise/status flags."""
    return any((row.get(column) or "").strip() for column in CBP_FLAG_COLUMNS)


def _ensure_cbp_manifest(
    connection: sqlite3.Connection,
    csv_path: Path,
    *,
    official_source_url: str,
    source_version: str,
    row_count: int,
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
        WHERE source_name = 'Census County Business Patterns (CBP)';
        """
    ).fetchone()[0]
    return insert_source_manifest(
        connection,
        source_id=source_id,
        source_name="Census County Business Patterns (CBP)",
        source_agency="U.S. Census Bureau",
        dataset_name=CBP_PRODUCT,
        access_method="official Census API",
        source_url_or_endpoint=official_source_url,
        source_year=2023,
        source_version=source_version,
        raw_filename=csv_path.name,
        file_checksum=checksum,
        row_count=row_count,
        notes=(
            "A4.10 committed sample derived from official Census CBP API "
            "responses for selected counties, years, and 2017 NAICS sectors. "
            "The API key is not stored in the raw file or manifest."
        ),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    """CLI entry point for CBP raw ingestion."""
    parser = argparse.ArgumentParser(description="Load source-native CBP raw rows.")
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=CBP_SAMPLE_PATH,
        help="Path to a source-native CBP sample CSV.",
    )
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        create_schema(connection)
        result = load_cbp_raw(connection, args.csv_path)
    print(
        "Loaded CBP raw rows: "
        f"read={result.rows_read}, "
        f"inserted={result.rows_inserted}, "
        f"skipped_existing={result.rows_skipped_existing}, "
        f"raw_cbp={result.raw_row_count}, "
        f"flagged={result.flagged_row_count}, "
        f"manifest_id={result.manifest_id}"
    )


if __name__ == "__main__":
    main()
