"""Acquire national county-sector CBP rows and build source-specific layers."""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

from regional_entrepreneurship_intelligence.database.connection import PROJECT_ROOT, connect_database
from regional_entrepreneurship_intelligence.database.naics_versions import (
    PRIVATE_BROAD_SECTORS, classify_sector, source_year_naics,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.extract_cbp import (
    CBP_PRODUCT, REQUIRED_CBP_COLUMNS, CBP_FLAG_COLUMNS, load_cbp_raw,
)
from regional_entrepreneurship_intelligence.etl.run_bds_production import PRODUCTION_DATABASE
from regional_entrepreneurship_intelligence.etl.transform_cbp import build_cbp_business_structure


PRODUCTION_DIR = PROJECT_ROOT / "data" / "raw" / "cbp" / "production"
SECTORS = PRIVATE_BROAD_SECTORS
MEASURES = ("ESTAB", "EMP", "PAYANN", "PAYQTR1")
FIELDS = sorted(REQUIRED_CBP_COLUMNS | CBP_FLAG_COLUMNS)


def acquire_year(year: int, destination: Path, key: str, *, refresh: bool = False) -> dict:
    vintage = source_year_naics("CBP", year).native_version
    industry_field = f"NAICS{vintage}"
    if destination.exists() and not (refresh and year >= 2012):
        with destination.open("r", encoding="utf-8", newline="") as handle:
            rows = sum(1 for _ in handle) - 1
        return {"year": year, "native_naics": vintage, "rows": rows}
    if not key:
        raise RuntimeError(f"CENSUS_API_KEY is required for CBP {year}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(".csv.part")
    count = 0
    with temp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for sector in SECTORS:
            status, target = classify_sector(vintage, sector)
            if status == "unresolved" or target is None:
                raise ValueError(f"Unresolved official sector concordance: {year}/{sector}")
            endpoint = f"https://api.census.gov/data/{year}/cbp"
            params = {
                "get": ",".join((
                    *MEASURES, *(f"{name}_F" for name in MEASURES),
                    *((f"{name}_N" for name in ("EMP", "PAYANN", "PAYQTR1")) if year >= 2012 else ()),
                )),
                "for": "county:*", industry_field: sector,
                "LFO": "001", "EMPSZES": "001",
            }
            public_url = endpoint + "?" + urllib.parse.urlencode(params)
            request_url = public_url + "&key=" + urllib.parse.quote(key)
            data = None
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(request_url, timeout=120) as response:
                        data = json.load(response)
                    break
                except Exception:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
            if data is None:
                raise RuntimeError(f"CBP API failed for {year}/{sector}; year left incomplete")
            if not isinstance(data, list) or not data:
                raise ValueError(f"Empty CBP response: {year}/{sector}")
            for values in data[1:]:
                row = dict(zip(data[0], values))
                native = row[industry_field].strip()
                if native != sector:
                    raise ValueError(f"Unexpected CBP sector for {year}/{sector}: {native}")
                flags = {name: row.get(f"{source}_F") or "" for name, source in (
                    ("establishments_flag", "ESTAB"), ("employment_flag", "EMP"),
                    ("annual_payroll_flag", "PAYANN"), ("first_quarter_payroll_flag", "PAYQTR1"),
                )}
                writer.writerow({
                    "source_year": year, "cbp_product": CBP_PRODUCT,
                    "state_fips": row["state"], "county_fips": row["county"],
                    "county_geoid": row["state"] + row["county"],
                    "county_name": "", "source_industry_id": native,
                    "source_industry_label": native, "source_naics_version": vintage,
                    "legal_form_code": row["LFO"], "employment_size_code": row["EMPSZES"],
                    "establishments": row.get("ESTAB", ""),
                    "employment": row.get("EMP", ""),
                    "annual_payroll": row.get("PAYANN", ""),
                    "first_quarter_payroll": row.get("PAYQTR1", ""),
                    "official_api_url": public_url,
                    "raw_response": json.dumps(row, sort_keys=True),
                    **flags,
                })
                count += 1
    if count == 0:
        temp.unlink()
        raise ValueError(f"No county-sector CBP rows: {year}")
    temp.replace(destination)
    return {"year": year, "native_naics": vintage, "rows": count}


def run(database_path: Path = PRODUCTION_DATABASE, *, acquire_only: bool = False,
        refresh: bool = False) -> dict:
    started = time.monotonic()
    key = os.environ.get("CENSUS_API_KEY", "")
    files = [acquire_year(year, PRODUCTION_DIR / f"cbp_county_sector_{year}.csv", key, refresh=refresh)
             for year in range(2010, 2024)]
    if acquire_only:
        return {"files": files, "runtime_seconds": round(time.monotonic() - started, 1)}
    with connect_database(database_path) as connection:
        create_schema(connection)
        for file in files:
            load_cbp_raw(
                connection, PRODUCTION_DIR / f"cbp_county_sector_{file['year']}.csv",
                source_version=f"CBP {file['year']} {file['native_naics']} NAICS",
            )
        result = build_cbp_business_structure(connection, load_raw_if_missing=False)
        counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                  for table in ("raw_cbp", "stg_cbp", "int_business_structure")}
    return {
        "files": files, "counts": counts, "rejected_rows": result.rejected_rows,
        "incomplete_aggregation_rows": result.incomplete_aggregation_rows,
        "runtime_seconds": round(time.monotonic() - started, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-path", type=Path, default=PRODUCTION_DATABASE)
    parser.add_argument("--acquire-only", action="store_true")
    parser.add_argument("--refresh", action="store_true", help="Refresh 2012+ files to include noise indicators")
    args = parser.parse_args()
    print(json.dumps(run(args.database_path, acquire_only=args.acquire_only, refresh=args.refresh), indent=2))


if __name__ == "__main__":
    main()
