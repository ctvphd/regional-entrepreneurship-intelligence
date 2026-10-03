"""Acquire and run the 2010-2023 national BDS source pipeline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import time
import urllib.request
from pathlib import Path

from regional_entrepreneurship_intelligence.database.connection import (
    PROJECT_ROOT,
    connect_database,
)
from regional_entrepreneurship_intelligence.database.metadata import insert_source_manifest
from regional_entrepreneurship_intelligence.database.reference import seed_reference_data
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_bds import (
    BDS_MSA_SECTOR_BULK_URL,
    BDS_MSA_SECTOR_FIRM_AGE_BULK_URL,
    BDS_MSA_SECTOR_FIRM_AGE_PRODUCT,
    BDS_MSA_SECTOR_PRODUCT,
    BDS_MSA_SECTOR_RELEASE,
    load_bds_firm_age_raw,
    load_bds_raw,
)
from regional_entrepreneurship_intelligence.etl.transform_bds import build_bds_standardized_layers


PRODUCTION_DIR = PROJECT_ROOT / "data" / "raw" / "bds" / "production"
PRODUCTION_DATABASE = PROJECT_ROOT / "database" / "assignment4_production.sqlite"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _acquire(url: str, destination: Path) -> None:
    if destination.is_file() and destination.stat().st_size:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output, 1024 * 1024)
    temporary.replace(destination)


def _extract(source: Path, destination: Path, *, age_zero_only: bool) -> tuple[int, int]:
    total = 0
    selected = 0
    with source.open("r", encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)
        if not reader.fieldnames:
            raise ValueError(f"Empty source: {source}")
        with destination.open("w", encoding="utf-8", newline="") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                total += 1
                if not 2010 <= int(row["year"]) <= 2023:
                    continue
                if age_zero_only and row["fagecoarse"] != "a) 0":
                    continue
                writer.writerow(row)
                selected += 1
    return total, selected


def _manifest(connection, source: Path, url: str, product: str, rows: int) -> None:
    checksum = _sha256(source)
    existing = connection.execute(
        """SELECT manifest_id FROM metadata_source_manifest
           WHERE raw_filename = ? AND file_checksum = ? AND source_url_or_endpoint = ?""",
        (source.name, checksum, url),
    ).fetchone()
    if existing:
        connection.execute(
            "UPDATE metadata_source_manifest SET notes = ? WHERE manifest_id = ?",
            ("Original 2023 BDS release file covers 1978-2023; local production ingestion selects 2010-2023.", existing[0]),
        )
        connection.commit()
        return
    source_id = connection.execute(
        "SELECT source_id FROM ref_source WHERE source_name = 'Census Business Dynamics Statistics (BDS)'"
    ).fetchone()[0]
    insert_source_manifest(
        connection,
        source_id=source_id,
        source_name="Census Business Dynamics Statistics (BDS)",
        source_agency="U.S. Census Bureau",
        dataset_name=product,
        access_method="official bulk CSV",
        source_url_or_endpoint=url,
        source_year=2023,
        source_version=BDS_MSA_SECTOR_RELEASE,
        raw_filename=source.name,
        file_checksum=checksum,
        row_count=rows,
        notes="Original 2023 BDS release file covers 1978-2023; local production ingestion selects 2010-2023.",
    )


def _annotate_extract_manifest(connection, extract: Path, url: str, selected: int, age_zero_only: bool) -> None:
    connection.execute(
        """UPDATE metadata_source_manifest
           SET access_method = ?, notes = ?
           WHERE raw_filename = ? AND source_url_or_endpoint = ?""",
        (
            "local study-window extract of official Census bulk CSV",
            f"2010-2023 {'age-0 firm' if age_zero_only else 'MSA-sector'} rows; "
            f"{selected} rows selected from the locally retained original file. No source values recoded.",
            extract.name,
            url,
        ),
    )
    connection.commit()


def run(database_path: Path = PRODUCTION_DATABASE) -> dict:
    started = time.monotonic()
    specs = (
        (BDS_MSA_SECTOR_BULK_URL, BDS_MSA_SECTOR_PRODUCT, False),
        (BDS_MSA_SECTOR_FIRM_AGE_BULK_URL, BDS_MSA_SECTOR_FIRM_AGE_PRODUCT, True),
    )
    acquisition = []
    for url, product, age_zero_only in specs:
        original = PRODUCTION_DIR / url.rsplit("/", 1)[-1]
        _acquire(url, original)
        extract = PRODUCTION_DIR / f"study_{original.name}"
        total, selected = _extract(original, extract, age_zero_only=age_zero_only)
        acquisition.append((url, product, original, extract, total, selected, age_zero_only))

    with connect_database(database_path) as connection:
        create_schema(connection)
        seed_reference_data(connection)
        for url, product, original, extract, total, selected, age_zero_only in acquisition:
            _manifest(connection, original, url, product, total)
            if age_zero_only:
                load_bds_firm_age_raw(
                    connection, extract, official_source_url=url,
                    source_version=BDS_MSA_SECTOR_RELEASE,
                )
            else:
                load_bds_raw(
                    connection, extract, official_source_url=url,
                    source_version=BDS_MSA_SECTOR_RELEASE,
                )
            _annotate_extract_manifest(connection, extract, url, selected, age_zero_only)
        result = build_bds_standardized_layers(connection, load_raw_if_missing=False)
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("raw_bds", "raw_bds_firm_age", "stg_bds", "int_entrepreneurship")
        }
        metrics = {
            "source_files": [
                {
                    "filename": original.name,
                    "url": url,
                    "sha256": _sha256(original),
                    "bytes": original.stat().st_size,
                    "source_rows": total,
                    "selected_rows": selected,
                    "selection": "2010-2023 age 0" if age_zero_only else "2010-2023 all sectors",
                }
                for url, _product, original, _extract_path, total, selected, age_zero_only in acquisition
            ],
            "counts": counts,
            "geography_status_counts": result.geography_audit.status_counts,
            "industry_status_counts": result.industry_audit.status_counts,
            "rejected_rows": result.rejected_rows,
            "missing_startup_rows": result.missing_startup_measure_rows,
            "lag1_available": result.lag1_available,
            "lag2_available": result.lag2_available,
            "lag3_available": result.lag3_available,
            "runtime_seconds": round(time.monotonic() - started, 1),
        }
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-path", type=Path, default=PRODUCTION_DATABASE)
    args = parser.parse_args()
    print(json.dumps(run(args.database_path), indent=2))


if __name__ == "__main__":
    main()
