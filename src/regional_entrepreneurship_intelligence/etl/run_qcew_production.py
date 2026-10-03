"""Acquire official QCEW annual by-area archives and extract county private sectors."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shutil
import time
import urllib.request
import zipfile
from pathlib import Path

from regional_entrepreneurship_intelligence.database.connection import PROJECT_ROOT, connect_database
from regional_entrepreneurship_intelligence.database.naics_versions import (
    PRIVATE_BROAD_SECTORS, classify_sector, source_year_naics,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_qcew import (
    QCEW_ANNUAL_BY_AREA_URL_PATTERN, REQUIRED_QCEW_COLUMNS, load_qcew_raw,
)
from regional_entrepreneurship_intelligence.etl.run_bds_production import PRODUCTION_DATABASE
from regional_entrepreneurship_intelligence.etl.transform_qcew import build_qcew_standardized_layers


PRODUCTION_DIR = PROJECT_ROOT / "data" / "raw" / "qcew" / "production"
COUNTY_FILE = re.compile(r"/\d{4}\.annual (\d{5}) .+\.csv$")
SECTORS = PRIVATE_BROAD_SECTORS


def _is_county_area(code: str) -> bool:
    return len(code) == 5 and code.isdigit() and code[2:] not in {"000", "999"}


def _repair_existing_extract(path: Path) -> int:
    temp = path.with_suffix(".csv.part")
    count = 0
    with path.open("r", encoding="utf-8", newline="") as source, temp.open(
        "w", encoding="utf-8", newline=""
    ) as target:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(target, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if _is_county_area(row["area_fips"]):
                writer.writerow(row)
                count += 1
    temp.replace(path)
    return count


def acquire_year(year: int, destination: Path) -> dict:
    vintage = source_year_naics("QCEW", year).native_version
    for sector in SECTORS:
        if classify_sector(vintage, sector)[0] == "unresolved":
            raise ValueError(f"Unresolved QCEW sector concordance: {year}/{sector}")
    url = QCEW_ANNUAL_BY_AREA_URL_PATTERN.format(year=year)
    archive = PRODUCTION_DIR / f"{year}_annual_by_area.zip"
    if not archive.exists():
        archive.parent.mkdir(parents=True, exist_ok=True)
        temp_archive = archive.with_suffix(".zip.part")
        with urllib.request.urlopen(url, timeout=180) as response, temp_archive.open("wb") as output:
            shutil.copyfileobj(response, output, 1024 * 1024)
        temp_archive.replace(archive)
    if destination.exists():
        count = _repair_existing_extract(destination)
        return {"year": year, "native_naics": vintage, "rows": count, "archive_bytes": archive.stat().st_size}
    temp = destination.with_suffix(".csv.part")
    count = 0
    counties = 0
    with zipfile.ZipFile(archive) as package, temp.open("w", encoding="utf-8", newline="") as handle:
        writer = None
        for member in package.namelist():
            match = COUNTY_FILE.search(member)
            if not match or not _is_county_area(match.group(1)):
                continue
            counties += 1
            with package.open(member) as raw:
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
                if not reader.fieldnames:
                    continue
                if writer is None:
                    fields = list(reader.fieldnames)
                    if "annual_avg_estabs_count" in fields:
                        fields.append("annual_avg_estabs")
                    if REQUIRED_QCEW_COLUMNS - set(fields):
                        raise ValueError(f"QCEW required fields missing for {year}: {member}")
                    writer = csv.DictWriter(handle, fieldnames=fields)
                    writer.writeheader()
                for row in reader:
                    sector = row["industry_code"].strip()
                    if row["own_code"] != "5" or row["size_code"] != "0" or row["qtr"] != "A":
                        continue
                    if sector not in SECTORS:
                        continue
                    if "annual_avg_estabs_count" in row:
                        row["annual_avg_estabs"] = row["annual_avg_estabs_count"]
                    writer.writerow(row)
                    count += 1
    if count == 0:
        temp.unlink()
        raise ValueError(f"QCEW county private sector extract empty for {year}")
    temp.replace(destination)
    return {"year": year, "native_naics": vintage, "rows": count,
            "county_files": counties, "archive_bytes": archive.stat().st_size}


def run(database_path: Path = PRODUCTION_DATABASE, *, acquire_only: bool = False) -> dict:
    started = time.monotonic()
    files = [acquire_year(year, PRODUCTION_DIR / f"qcew_private_county_sector_{year}.csv")
             for year in range(2010, 2024)]
    if acquire_only:
        return {"files": files, "runtime_seconds": round(time.monotonic() - started, 1)}
    with connect_database(database_path) as connection:
        create_schema(connection)
        for file in files:
            load_qcew_raw(
                connection, PRODUCTION_DIR / f"qcew_private_county_sector_{file['year']}.csv",
                official_source_url=QCEW_ANNUAL_BY_AREA_URL_PATTERN.format(year=file["year"]),
                source_version=f"QCEW {file['year']} {file['native_naics']} NAICS",
            )
        result = build_qcew_standardized_layers(connection, load_raw_if_missing=False)
        counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                  for table in ("raw_qcew", "stg_qcew", "int_industry_growth")}
    return {"files": files, "counts": counts, "rejected_rows": result.rejected_rows,
            "incomplete_aggregation_rows": result.incomplete_aggregation_rows,
            "runtime_seconds": round(time.monotonic() - started, 1)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-path", type=Path, default=PRODUCTION_DATABASE)
    parser.add_argument("--acquire-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.database_path, acquire_only=args.acquire_only), indent=2))


if __name__ == "__main__":
    main()
