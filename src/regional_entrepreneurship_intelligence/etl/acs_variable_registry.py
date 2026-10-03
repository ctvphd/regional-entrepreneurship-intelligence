"""Year-specific ACS 5-year Data Profile variable definitions."""

from __future__ import annotations

import csv
import json
import urllib.request
from pathlib import Path

from regional_entrepreneurship_intelligence.database.connection import PROJECT_ROOT


REGISTRY_PATH = PROJECT_ROOT / "data" / "external" / "reference" / "acs_variable_registry.csv"
PRODUCT = "ACS 5-year Data Profile"
CONCEPTS = {
    "population": ("DP05_0001E", "DP05_0001M", "Total population", "estimate"),
    "median_household_income": ("DP03_0062E", "DP03_0062M", "Total households", "estimate"),
    "educational_attainment_pct": (None, None, "Population 25 years and over", "percent"),
    "labor_force_participation_pct": ("DP03_0002PE", "DP03_0002PM", "Population 16 years and over", "percent"),
    "unemployment_rate": ("DP03_0009PE", "DP03_0009PM", "Civilian labor force", "percent"),
}
FIELDS = (
    "year", "acs_product", "concept_name", "variable_id", "variable_label",
    "universe", "estimate_type", "moe_variable_id", "moe_variable_label",
    "comparable_to_previous_year", "source_metadata_url", "notes",
)


def ids_for(concept: str, year: int) -> tuple[str, str]:
    if concept not in CONCEPTS or not 2010 <= year <= 2023:
        raise ValueError(f"Unknown ACS concept/year: {concept}/{year}")
    if concept == "educational_attainment_pct":
        base = "DP02_0067" if year <= 2018 else "DP02_0068"
        return base + "PE", base + "PM"
    estimate, moe = CONCEPTS[concept][:2]
    assert estimate is not None and moe is not None
    return estimate, moe


def validate_label(concept: str, label: str) -> None:
    lower = label.lower()
    required = {
        "population": ("total population",),
        "median_household_income": ("income and benefits", "median household income"),
        "educational_attainment_pct": ("educational attainment", "bachelor's degree or higher"),
        "labor_force_participation_pct": ("employment status", "in labor force"),
        "unemployment_rate": ("employment status",),
    }[concept]
    if not all(token in lower for token in required):
        raise ValueError(f"ACS variable definition mismatch for {concept}: {label}")
    if concept == "unemployment_rate" and not any(
        token in lower for token in ("percent unemployed", "unemployment rate")
    ):
        raise ValueError(f"ACS unemployment definition mismatch: {label}")


def build_registry() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for year in range(2010, 2024):
        endpoint = f"https://api.census.gov/data/{year}/acs/acs5/profile/variables.json"
        with urllib.request.urlopen(endpoint, timeout=60) as response:
            variables = json.load(response)["variables"]
        groups = {}
        for concept, (_estimate, _moe, universe, estimate_type) in CONCEPTS.items():
            variable_id, moe_id = ids_for(concept, year)
            label = variables[variable_id]["label"]
            validate_label(concept, label)
            if moe_id not in variables[variable_id].get("attributes", "").split(","):
                raise ValueError(f"ACS estimate does not identify its MOE: {year}/{variable_id}")
            group = variable_id.split("_")[0]
            if group not in groups:
                group_url = f"https://api.census.gov/data/{year}/acs/acs5/profile/groups/{group}.json"
                with urllib.request.urlopen(group_url, timeout=60) as response:
                    groups[group] = json.load(response)["variables"]
            moe_label = groups[group][moe_id]["label"]
            if "margin of error" not in moe_label.lower():
                raise ValueError(f"ACS MOE definition mismatch: {year}/{moe_id}")
            rows.append({
                "year": str(year),
                "acs_product": PRODUCT,
                "concept_name": concept,
                "variable_id": variable_id,
                "variable_label": label,
                "universe": universe,
                "estimate_type": estimate_type,
                "moe_variable_id": moe_id,
                "moe_variable_label": moe_label,
                "comparable_to_previous_year": "yes" if year > 2010 else "not_applicable",
                "source_metadata_url": endpoint,
                "notes": (
                    "Education ID changes in 2019; concept remains bachelor's degree or higher."
                    if concept == "educational_attainment_pct" and year == 2019
                    else "Income is expressed in the source ACS year-adjusted dollars."
                    if concept == "median_household_income" else ""
                ),
            })
    return rows


def write_registry(path: Path = REGISTRY_PATH) -> list[dict[str, str]]:
    rows = build_registry()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def load_registry(path: Path = REGISTRY_PATH) -> dict[tuple[int, str], dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result = {(int(row["year"]), row["concept_name"]): row for row in rows}
    expected = {(year, concept) for year in range(2010, 2024) for concept in CONCEPTS}
    if set(result) != expected or len(rows) != len(expected):
        raise ValueError("ACS registry must contain one row per concept and study year")
    for (year, concept), row in result.items():
        if (row["variable_id"], row["moe_variable_id"]) != ids_for(concept, year):
            raise ValueError(f"Incorrect ACS registry IDs for {concept}/{year}")
        validate_label(concept, row["variable_label"])
    return result


if __name__ == "__main__":
    print(f"Wrote {len(write_registry())} ACS concept-year definitions to {REGISTRY_PATH}")
