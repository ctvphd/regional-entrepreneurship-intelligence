"""ACS source profiling and raw-ingestion helpers for Assignment 4.9."""

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


ACS_SAMPLE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "acs"
    / "sample"
    / "acs5_profile_msa_sample_2020_2023.csv"
)
ACS_PRODUCT = "ACS 5-year Data Profile"
ACS_RELEASE = "ACS 5-year Data Profile API, 2020-2023 sample"
ACS_API_ENDPOINT_PATTERN = "https://api.census.gov/data/{year}/acs/acs5/profile"

REQUIRED_ACS_COLUMNS = {
    "source_year",
    "acs_product",
    "source_geography_id",
    "source_geography_name",
    "control_name",
    "variable_id",
    "moe_variable_id",
    "estimate",
    "margin_of_error",
    "variable_label",
    "official_api_url",
    "raw_response",
}


@dataclass(frozen=True)
class ACSRawLoadResult:
    """Summary returned by ACS raw ingestion."""

    manifest_id: int
    pipeline_run_id: str
    rows_read: int
    rows_inserted: int
    rows_skipped_existing: int
    raw_row_count: int


def read_acs_csv(csv_path: str | Path) -> list[dict[str, str]]:
    """Read an ACS sample CSV while preserving source values as strings."""
    path = Path(csv_path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(row) for row in reader]
    validate_acs_rows(rows, fieldnames=reader.fieldnames or [])
    return rows


def validate_acs_rows(rows: list[dict[str, str]], *, fieldnames: list[str]) -> None:
    """Validate required ACS fields without transforming rows."""
    missing_columns = REQUIRED_ACS_COLUMNS - set(fieldnames)
    if missing_columns:
        raise ValueError(f"Missing required ACS columns: {sorted(missing_columns)}")
    if not rows:
        raise ValueError("ACS source contains no data rows")
    for index, row in enumerate(rows, start=1):
        if not row.get("source_year", "").isdigit():
            raise ValueError(f"Invalid ACS year at row {index}: {row.get('source_year')}")
        for field in (
            "source_geography_id",
            "source_geography_name",
            "control_name",
            "variable_id",
            "estimate",
        ):
            if row.get(field) is None:
                raise ValueError(f"Missing ACS field {field} at row {index}")


def load_acs_raw(
    connection: sqlite3.Connection,
    csv_path: str | Path = ACS_SAMPLE_PATH,
    *,
    official_source_url: str = "official Census ACS 5-year profile API endpoints embedded per row",
    source_version: str = ACS_RELEASE,
) -> ACSRawLoadResult:
    """Load source-native ACS rows into ``raw_acs`` idempotently."""
    path = Path(csv_path)
    rows = read_acs_csv(path)
    seed_reference_data(connection)
    manifest_id = _ensure_acs_manifest(
        connection,
        path,
        official_source_url=official_source_url,
        source_version=source_version,
        row_count=len(rows),
        source_year=int(rows[0]["source_year"]) if len({row["source_year"] for row in rows}) == 1 else None,
    )
    run_id = start_pipeline_run(connection, stage="raw_acs_ingestion")
    inserted = 0
    skipped = 0
    existing_rows = {
        row[0] for row in connection.execute(
            "SELECT source_row_identifier FROM raw_acs WHERE raw_source_filename = ?;",
            (path.name,),
        )
    }
    try:
        with connection:
            for row in rows:
                source_row_identifier = acs_source_row_identifier(row)
                if source_row_identifier in existing_rows:
                    skipped += 1
                    continue
                connection.execute(
                    """
                    INSERT INTO raw_acs (
                        manifest_id,
                        pipeline_run_id,
                        source_year,
                        source_geography_id,
                        source_geography_name,
                        source_industry_id,
                        source_variable_id,
                        source_moe_variable_id,
                        source_product,
                        control_name,
                        estimate_value,
                        margin_of_error,
                        source_naics_version,
                        source_row_identifier,
                        raw_source_filename,
                        is_suppressed,
                        raw_payload,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, NULL, ?, ?, 0, ?, ?);
                    """,
                    (
                        manifest_id,
                        run_id,
                        int(row["source_year"]),
                        row["source_geography_id"],
                        row["source_geography_name"],
                        row["variable_id"],
                        row["moe_variable_id"],
                        row["acs_product"],
                        row["control_name"],
                        row["estimate"],
                        row["margin_of_error"],
                        source_row_identifier,
                        path.name,
                        json.dumps(row, sort_keys=True),
                        "Loaded source-native ACS estimate/MOE row; no regional-control transformation applied.",
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
                f"Skipped {skipped} existing ACS raw rows during idempotent rerun."
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

    raw_row_count = connection.execute("SELECT COUNT(*) FROM raw_acs;").fetchone()[0]
    return ACSRawLoadResult(
        manifest_id=manifest_id,
        pipeline_run_id=run_id,
        rows_read=len(rows),
        rows_inserted=inserted,
        rows_skipped_existing=skipped,
        raw_row_count=raw_row_count,
    )


def acs_source_row_identifier(row: dict[str, str]) -> str:
    """Build a deterministic source-native ACS row identifier."""
    return "|".join(
        [
            "acs5_profile",
            f"year={row['source_year']}",
            f"geo={row['source_geography_id']}",
            f"variable={row['variable_id']}",
        ]
    )


def _ensure_acs_manifest(
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
        WHERE source_name = 'American Community Survey (ACS)';
        """
    ).fetchone()[0]
    return insert_source_manifest(
        connection,
        source_id=source_id,
        source_name="American Community Survey (ACS)",
        source_agency="U.S. Census Bureau",
        dataset_name=ACS_PRODUCT,
        access_method="official Census API",
        source_url_or_endpoint=official_source_url,
        source_year=source_year,
        source_version=source_version,
        raw_filename=csv_path.name,
        file_checksum=checksum,
        row_count=row_count,
        notes=(
            "ACS 5-year profile API responses for selected CBSAs, years, "
            "variables, and MOE fields. "
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
    """CLI entry point for ACS raw ingestion."""
    parser = argparse.ArgumentParser(description="Load source-native ACS raw rows.")
    parser.add_argument(
        "--database-path",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=ACS_SAMPLE_PATH,
        help="Path to a source-native ACS sample CSV.",
    )
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        create_schema(connection)
        result = load_acs_raw(connection, args.csv_path)
    print(
        "Loaded ACS raw rows: "
        f"read={result.rows_read}, "
        f"inserted={result.rows_inserted}, "
        f"skipped_existing={result.rows_skipped_existing}, "
        f"raw_acs={result.raw_row_count}, "
        f"manifest_id={result.manifest_id}"
    )


if __name__ == "__main__":
    main()
