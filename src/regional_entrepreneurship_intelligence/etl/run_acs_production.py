"""Acquire ACS profile controls using the audited concept-year registry."""

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
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.acs_variable_registry import (
    CONCEPTS, load_registry,
)
from regional_entrepreneurship_intelligence.etl.extract_acs import (
    ACS_PRODUCT, REQUIRED_ACS_COLUMNS, load_acs_raw,
)
from regional_entrepreneurship_intelligence.etl.run_bds_production import PRODUCTION_DATABASE
from regional_entrepreneurship_intelligence.etl.transform_acs import build_acs_regional_controls


PRODUCTION_DIR = PROJECT_ROOT / "data" / "raw" / "acs" / "production"
GEOGRAPHY = "metropolitan statistical area/micropolitan statistical area:*"


def acquire_year(year: int, output: Path, registry: dict, key: str) -> dict:
    definitions = [registry[(year, concept)] for concept in CONCEPTS]
    names = ["NAME"] + [id for definition in definitions for id in (
        definition["variable_id"], definition["moe_variable_id"]
    )]
    endpoint = f"https://api.census.gov/data/{year}/acs/acs5/profile"
    public_query = urllib.parse.urlencode({"get": ",".join(names), "for": GEOGRAPHY})
    public_url = f"{endpoint}?{public_query}"
    if not output.exists():
        request_url = public_url + ("&key=" + urllib.parse.quote(key) if key else "")
        try:
            with urllib.request.urlopen(request_url, timeout=120) as response:
                source = json.load(response)
        except Exception as exc:
            raise RuntimeError(f"ACS API request failed for {year}; inspect key and source availability") from None
        if not isinstance(source, list) or len(source) < 2:
            raise ValueError(f"ACS source returned no rows for {year}")
        headers = source[0]
        geo_field = headers[-1]
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_suffix(".csv.part")
        with temp.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=sorted(REQUIRED_ACS_COLUMNS))
            writer.writeheader()
            source_metros = 0
            for values in source[1:]:
                record = dict(zip(headers, values))
                name = record["NAME"]
                if "Metro Area" not in name and "Metropolitan Statistical Area" not in name:
                    continue
                source_metros += 1
                for definition in definitions:
                    variable_id = definition["variable_id"]
                    moe_id = definition["moe_variable_id"]
                    writer.writerow({
                        "source_year": year,
                        "acs_product": ACS_PRODUCT,
                        "source_geography_id": record[geo_field],
                        "source_geography_name": name,
                        "control_name": definition["concept_name"],
                        "variable_id": variable_id,
                        "moe_variable_id": moe_id,
                        "estimate": record.get(variable_id, ""),
                        "margin_of_error": record.get(moe_id, ""),
                        "variable_label": definition["variable_label"],
                        "official_api_url": public_url,
                        "raw_response": json.dumps(record, sort_keys=True),
                    })
        if source_metros == 0:
            temp.unlink()
            raise ValueError(f"No metropolitan ACS source rows identified for {year}")
        temp.replace(output)
    with output.open("r", encoding="utf-8", newline="") as handle:
        rows = sum(1 for _ in handle) - 1
    return {"year": year, "rows": rows, "metro_geographies": rows // len(CONCEPTS), "file": str(output)}


def run(database_path: Path = PRODUCTION_DATABASE) -> dict:
    started = time.monotonic()
    registry = load_registry()
    key = os.environ.get("CENSUS_API_KEY", "")
    files = [acquire_year(year, PRODUCTION_DIR / f"acs5_profile_metro_{year}.csv", registry, key)
             for year in range(2010, 2024)]
    with connect_database(database_path) as connection:
        create_schema(connection)
        for file in files:
            load_acs_raw(connection, file["file"], source_version=f"ACS 5-year Data Profile {file['year']}")
        result = build_acs_regional_controls(connection, load_raw_if_missing=False)
        counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                  for table in ("raw_acs", "stg_acs", "int_regional_controls")}
    return {
        "files": files, "counts": counts,
        "geography_audit": result.geography_audit.row_counts,
        "rejected_rows": result.rejected_rows,
        "income_lag1_available": result.income_lag1_available,
        "population_growth_lag1_available": result.population_growth_lag1_available,
        "runtime_seconds": round(time.monotonic() - started, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-path", type=Path, default=PRODUCTION_DATABASE)
    args = parser.parse_args()
    print(json.dumps(run(args.database_path), indent=2))


if __name__ == "__main__":
    main()
