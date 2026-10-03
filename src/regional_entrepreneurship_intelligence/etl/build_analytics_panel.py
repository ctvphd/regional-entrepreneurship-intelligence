"""Build and audit the Assignment 4 metropolitan industry-year panel."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import sqlite3
import statistics
from pathlib import Path
from typing import Any

from regional_entrepreneurship_intelligence.database.connection import (
    PROJECT_ROOT,
    connect_database,
)
from regional_entrepreneurship_intelligence.database.metadata import (
    finish_pipeline_run,
    insert_quality_metric,
    start_pipeline_run,
)
from regional_entrepreneurship_intelligence.database.schema import create_schema
from regional_entrepreneurship_intelligence.etl.run_bds_production import PRODUCTION_DATABASE


SOURCE_TABLES = {
    "BDS": ("int_entrepreneurship", True),
    "QCEW": ("int_industry_growth", True),
    "ACS": ("int_regional_controls", False),
    "CBP": ("int_business_structure", True),
}
YEARS = (2010, 2023)
MISSINGNESS_COLUMNS = (
    "startup_rate", "startup_rate_lag1", "startup_rate_lag2", "startup_rate_lag3",
    "firm_startups", "establishment_entry", "establishment_entry_rate", "startup_job_creation",
    "qcew_employment", "qcew_establishments", "qcew_payroll", "qcew_average_wage",
    "qcew_total_annual_wages_nominal", "qcew_average_annual_pay_nominal",
    "employment_growth", "establishment_growth", "payroll_growth", "wage_growth",
    "employment_growth_lag1", "employment_growth_lag2", "employment_growth_lag3",
    "establishment_growth_lag1", "establishment_growth_lag2", "establishment_growth_lag3",
    "payroll_growth_lag1", "average_pay_growth_lag1", "acs_population", "acs_population_growth",
    "acs_population_growth_lag1", "median_household_income", "median_household_income_lag1",
    "educational_attainment_pct", "educational_attainment_pct_lag1",
    "labor_force_participation_pct", "labor_force_participation_pct_lag1",
    "unemployment_rate", "unemployment_rate_lag1", "cbp_establishments", "cbp_employment",
    "cbp_annual_payroll", "cbp_first_quarter_payroll",
)


def _assert_unique_keys(connection: sqlite3.Connection) -> dict[str, int]:
    duplicates: dict[str, int] = {}
    for source, (table, has_industry) in SOURCE_TABLES.items():
        columns = "geography_id, industry_id, year" if has_industry else "geography_id, year"
        count = connection.execute(
            f"SELECT COUNT(*) FROM (SELECT {columns}, COUNT(*) AS n FROM {table} "
            f"GROUP BY {columns} HAVING n > 1)"
        ).fetchone()[0]
        duplicates[source] = count
    if any(duplicates.values()):
        raise ValueError(f"Source intermediate key duplicates found; panel not rebuilt: {duplicates}")
    return duplicates


def _source_sectors(connection: sqlite3.Connection) -> dict[str, set[str]]:
    result = {}
    for source, (table, has_industry) in SOURCE_TABLES.items():
        if not has_industry:
            continue
        result[source] = {
            row[0]
            for row in connection.execute(
                f"""SELECT DISTINCT i.naics_code
                    FROM {table} AS t
                    JOIN ref_industry AS i ON i.industry_id = t.industry_id
                    WHERE i.naics_level = 2"""
            )
        }
    common = set.intersection(*result.values())
    if not common:
        raise ValueError("No valid common broad-sector scope")
    return result


def _keys(connection: sqlite3.Connection, table: str, include_industry: bool) -> set[tuple[int, ...]]:
    fields = "geography_id, industry_id, year" if include_industry else "geography_id, year"
    return {tuple(row) for row in connection.execute(f"SELECT {fields} FROM {table}")}


def _percent(numerator: int, denominator: int) -> float:
    return round(100 * numerator / denominator, 4) if denominator else 0.0


def _median_or_none(values: list[float]) -> float | None:
    return float(statistics.median(values)) if values else None


def _comparison_summary(rows: list[tuple[float | None, float | None]]) -> dict[str, Any]:
    pairs = [(float(a), float(b)) for a, b in rows if a is not None and b is not None]
    ratios = [b / a for a, b in pairs if a != 0]
    apd = [abs(b - a) / abs(a) for a, b in pairs if a != 0]
    if len(pairs) > 1:
        mean_a = statistics.fmean(a for a, _ in pairs)
        mean_b = statistics.fmean(b for _, b in pairs)
        cov = sum((a - mean_a) * (b - mean_b) for a, b in pairs)
        var_a = sum((a - mean_a) ** 2 for a, _ in pairs)
        var_b = sum((b - mean_b) ** 2 for _, b in pairs)
        corr = cov / math.sqrt(var_a * var_b) if var_a and var_b else None
    else:
        corr = None
    return {
        "matched_observations": len(pairs),
        "nonzero_qcew_denominator_observations": len(ratios),
        "correlation": round(corr, 6) if corr is not None else None,
        "median_cbp_to_qcew_ratio": round(_median_or_none(ratios), 6) if ratios else None,
        "median_absolute_percentage_difference": round(_median_or_none(apd), 6) if apd else None,
        "major_disagreement_over_100pct": sum(diff > 1 for diff in apd),
    }


def _cross_source_diagnostics(connection: sqlite3.Connection) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    for measure, qcol, ccol in (
        ("employment", "qcew_employment", "cbp_employment"),
        ("establishments", "qcew_establishments", "cbp_establishments"),
        ("payroll", "qcew_payroll", "cbp_annual_payroll"),
    ):
        cbp_scale = 1000 if measure == "payroll" else 1
        rows = connection.execute(
            f"SELECT {qcol}, {ccol} * {cbp_scale} FROM analytics_msa_industry_year WHERE cbp_matched = 1"
        ).fetchall()
        by_year: dict[str, list[tuple[float | None, float | None]]] = {}
        by_sector: dict[str, list[tuple[float | None, float | None]]] = {}
        by_msa: dict[str, list[tuple[float | None, float | None]]] = {}
        grouped = connection.execute(
            f"""SELECT a.year, i.naics_code, g.cbsa_code, a.{qcol}, a.{ccol} * {cbp_scale}
                FROM analytics_msa_industry_year AS a
                JOIN ref_industry AS i ON i.industry_id = a.industry_id
                JOIN ref_geography AS g ON g.geography_id = a.geography_id
                WHERE a.cbp_matched = 1"""
        ).fetchall()
        pairs = [(row[0], row[1]) for row in rows]
        for year, sector, msa, qval, cval in grouped:
            pair = (qval, cval)
            by_year.setdefault(str(year), []).append(pair)
            by_sector.setdefault(sector, []).append(pair)
            by_msa.setdefault(msa, []).append(pair)
        breakdowns = {
            "by_year": {k: _comparison_summary(v) for k, v in sorted(by_year.items())},
            "by_sector": {k: _comparison_summary(v) for k, v in sorted(by_sector.items())},
            "by_msa": {k: _comparison_summary(v) for k, v in sorted(by_msa.items())},
        }
        major_by_msa = sorted(
            ((code, row["major_disagreement_over_100pct"], row["matched_observations"])
             for code, row in breakdowns["by_msa"].items()),
            key=lambda item: (-item[1], item[0]),
        )
        diagnostics[measure] = {
            **_comparison_summary(pairs),
            **breakdowns,
            "highest_major_disagreement_msas": [
                {"cbsa_code": code, "rows_over_100pct": count, "matched": matched}
                for code, count, matched in major_by_msa[:10] if count
            ],
        }
    return diagnostics


def _insert_panel(connection: sqlite3.Connection, run_id: str, sectors: set[str]) -> int:
    industry_ids = [
        row[0] for row in connection.execute(
            f"SELECT industry_id FROM ref_industry WHERE naics_level = 2 AND naics_code IN ({','.join('?' for _ in sectors)})",
            sorted(sectors),
        )
    ]
    if not industry_ids:
        raise ValueError("No common authoritative industry IDs found")
    placeholders = ",".join("?" for _ in industry_ids)
    cbp_staged_group = "EXISTS(SELECT 1 FROM stg_cbp s WHERE s.geography_id=b.geography_id AND s.industry_id=b.industry_id AND s.year=b.year)"
    cbp_staged_suppression = "EXISTS(SELECT 1 FROM stg_cbp s WHERE s.geography_id=b.geography_id AND s.industry_id=b.industry_id AND s.year=b.year AND s.is_suppressed=1)"
    cbp_suppression = f"CASE WHEN c.geography_id IS NOT NULL THEN COALESCE(c.has_suppression,0) WHEN {cbp_staged_suppression} THEN 1 ELSE 0 END"
    cbp_complete = f"CASE WHEN c.geography_id IS NOT NULL THEN c.is_complete_county_coverage WHEN {cbp_staged_group} THEN 0 ELSE NULL END"
    target_select = [
        "b.firm_startups", "b.startup_rate", "b.startup_rate_lag1", "b.startup_rate_lag2",
        "b.startup_rate_lag3", "b.lagged_startup_rate", "b.establishment_entry",
        "b.establishment_entry_rate", "b.startup_job_creation",
        "q.employment", "q.establishments", "q.payroll", "q.average_wage",
        "q.total_annual_wages_nominal", "q.average_annual_pay_nominal",
        "q.employment_growth", "q.establishment_growth", "q.payroll_growth", "q.wage_growth",
        "q.employment_growth_lag1", "q.employment_growth_lag2", "q.employment_growth_lag3",
        "q.establishment_growth_lag1", "q.establishment_growth_lag2", "q.establishment_growth_lag3",
        "q.payroll_growth_lag1", "q.average_pay_growth_lag1",
        "a.population", "a.population_growth", "a.population_growth_lag1",
        "a.median_household_income", "a.educational_attainment_pct",
        "a.labor_force_participation_pct", "a.unemployment_rate",
        "a.median_household_income_lag1", "a.educational_attainment_pct_lag1",
        "a.labor_force_participation_pct_lag1", "a.unemployment_rate_lag1",
        "c.establishments", "c.employment", "c.annual_payroll", "c.first_quarter_payroll",
        "COALESCE(b.has_suppression, 0)", "CASE WHEN b.startup_rate IS NULL THEN 0 ELSE 1 END",
        "COALESCE(q.has_suppression, 0)", "q.is_complete_county_coverage", "COALESCE(q.is_real_adjusted, 0)",
        "CASE WHEN a.geography_id IS NULL THEN 0 ELSE 1 END", "COALESCE(a.has_suppression, 0)",
        "CASE WHEN a.geography_id IS NULL OR a.population IS NULL OR a.median_household_income IS NULL "
        "OR a.educational_attainment_pct IS NULL OR a.labor_force_participation_pct IS NULL "
        "OR a.unemployment_rate IS NULL THEN 1 ELSE 0 END",
        "CASE WHEN c.geography_id IS NULL THEN 0 ELSE 1 END", cbp_suppression,
        cbp_complete,
        f"CASE WHEN COALESCE(b.has_suppression,0)=1 OR COALESCE(q.has_suppression,0)=1 "
        f"OR COALESCE(a.has_suppression,0)=1 OR ({cbp_suppression})=1 THEN 1 ELSE 0 END",
        "trim("
        "CASE WHEN a.geography_id IS NULL THEN 'acs_unmatched;' ELSE '' END || "
        "CASE WHEN a.geography_id IS NOT NULL AND (a.population IS NULL OR a.median_household_income IS NULL "
        "OR a.educational_attainment_pct IS NULL OR a.labor_force_participation_pct IS NULL "
        "OR a.unemployment_rate IS NULL) THEN 'acs_missing_controls;' ELSE '' END || "
        "CASE WHEN c.geography_id IS NULL THEN 'cbp_unmatched;' ELSE '' END || "
        "CASE WHEN COALESCE(b.has_suppression,0)=1 THEN 'bds_suppression;' ELSE '' END || "
        "CASE WHEN COALESCE(q.has_suppression,0)=1 THEN 'qcew_suppression;' ELSE '' END || "
        "CASE WHEN q.is_complete_county_coverage=0 THEN 'qcew_incomplete_county_coverage;' ELSE '' END || "
        f"CASE WHEN ({cbp_suppression})=1 THEN 'cbp_suppression;' ELSE '' END || "
        f"CASE WHEN ({cbp_complete})=0 THEN 'cbp_incomplete_county_coverage;' ELSE '' END, ';')",
        "?",
    ]
    insert_columns = [
        "geography_id", "industry_id", "year", "firm_startups", "startup_rate",
        "startup_rate_lag1", "startup_rate_lag2", "startup_rate_lag3", "lagged_startup_rate",
        "establishment_entry", "establishment_entry_rate", "startup_job_creation",
        "qcew_employment", "qcew_establishments", "qcew_payroll", "qcew_average_wage",
        "qcew_total_annual_wages_nominal", "qcew_average_annual_pay_nominal", "employment_growth",
        "establishment_growth", "payroll_growth", "wage_growth", "employment_growth_lag1",
        "employment_growth_lag2", "employment_growth_lag3", "establishment_growth_lag1",
        "establishment_growth_lag2", "establishment_growth_lag3", "payroll_growth_lag1",
        "average_pay_growth_lag1", "acs_population", "acs_population_growth",
        "acs_population_growth_lag1", "median_household_income", "educational_attainment_pct",
        "labor_force_participation_pct", "unemployment_rate", "median_household_income_lag1",
        "educational_attainment_pct_lag1", "labor_force_participation_pct_lag1",
        "unemployment_rate_lag1", "cbp_establishments", "cbp_employment", "cbp_annual_payroll",
        "cbp_first_quarter_payroll", "bds_has_suppression", "bds_startup_available",
        "qcew_has_suppression", "qcew_is_complete_county_coverage", "qcew_is_real_adjusted",
        "acs_matched", "acs_has_suppression", "acs_has_missing_controls", "cbp_matched",
        "cbp_has_suppression", "cbp_is_complete_county_coverage", "has_suppression",
        "source_quality_notes", "pipeline_run_id",
    ]
    select_columns = ["b.geography_id", "b.industry_id", "b.year", *target_select]
    sql = f"""INSERT INTO analytics_msa_industry_year ({','.join(insert_columns)})
        SELECT {','.join(select_columns)}
        FROM int_entrepreneurship AS b
        JOIN int_industry_growth AS q
          ON q.geography_id=b.geography_id AND q.industry_id=b.industry_id AND q.year=b.year
        JOIN ref_geography AS g ON g.geography_id=b.geography_id
        JOIN ref_industry AS i ON i.industry_id=b.industry_id
        LEFT JOIN int_regional_controls AS a
          ON a.geography_id=b.geography_id AND a.year=b.year
        LEFT JOIN int_business_structure AS c
          ON c.geography_id=b.geography_id AND c.industry_id=b.industry_id AND c.year=b.year
        WHERE g.geography_type='MSA' AND b.year BETWEEN ? AND ?
          AND b.industry_id IN ({placeholders})
        ORDER BY b.geography_id,b.industry_id,b.year"""
    connection.execute("DELETE FROM analytics_msa_industry_year")
    connection.execute(sql, [run_id, YEARS[0], YEARS[1], *industry_ids])
    return connection.execute("SELECT COUNT(*) FROM analytics_msa_industry_year").fetchone()[0]


def _panel_audits(connection: sqlite3.Connection) -> dict[str, Any]:
    total = connection.execute("SELECT COUNT(*) FROM analytics_msa_industry_year").fetchone()[0]
    panel = connection.execute("""SELECT COUNT(DISTINCT geography_id), COUNT(DISTINCT industry_id),
        COUNT(DISTINCT year), MIN(year), MAX(year), COUNT(*)*1.0/COUNT(DISTINCT geography_id||':'||industry_id)
        FROM analytics_msa_industry_year""").fetchone()
    panels = connection.execute("""SELECT COUNT(*) AS n FROM (
        SELECT geography_id,industry_id,COUNT(*) AS years FROM analytics_msa_industry_year
        GROUP BY geography_id,industry_id)""").fetchone()[0]
    balanced = connection.execute("""SELECT COUNT(*) FROM (
        SELECT geography_id,industry_id FROM analytics_msa_industry_year
        GROUP BY geography_id,industry_id HAVING COUNT(*)=14)""").fetchone()[0]
    duplicate_count = connection.execute("""SELECT COUNT(*) FROM (
        SELECT geography_id,industry_id,year,COUNT(*) n FROM analytics_msa_industry_year
        GROUP BY geography_id,industry_id,year HAVING n>1)""").fetchone()[0]
    years = []
    for row in connection.execute("""SELECT year,COUNT(*) rows,COUNT(DISTINCT geography_id) msas,
        COUNT(DISTINCT industry_id) industries,SUM(startup_rate IS NOT NULL) startup,
        SUM(employment_growth IS NOT NULL) qcew_growth,SUM(acs_matched=1 AND acs_has_missing_controls=0) acs,
        SUM(cbp_matched=1) cbp FROM analytics_msa_industry_year GROUP BY year ORDER BY year"""):
        years.append(dict(row))
    industries = []
    for row in connection.execute("""SELECT i.naics_code sector,COUNT(*) rows,
        COUNT(DISTINCT a.geography_id) msas,COUNT(DISTINCT a.year) years,
        SUM(a.startup_rate IS NOT NULL) startup,SUM(a.employment_growth IS NOT NULL) qcew_growth,
        SUM(a.acs_matched=1 AND a.acs_has_missing_controls=0) acs,SUM(a.cbp_matched=1) cbp
        FROM analytics_msa_industry_year a JOIN ref_industry i USING(industry_id)
        GROUP BY i.naics_code ORDER BY i.naics_code"""):
        industries.append(dict(row))
    msa_coverage = [dict(row) for row in connection.execute("""SELECT g.cbsa_code,g.cbsa_name,
        COUNT(*) rows,COUNT(DISTINCT a.industry_id) industries,COUNT(DISTINCT a.year) years
        FROM analytics_msa_industry_year a JOIN ref_geography g USING(geography_id)
        GROUP BY g.cbsa_code,g.cbsa_name ORDER BY rows,g.cbsa_code""")]
    missingness = {}
    for column in MISSINGNESS_COLUMNS:
        missing = connection.execute(
            f"SELECT COUNT(*) FROM analytics_msa_industry_year WHERE {column} IS NULL"
        ).fetchone()[0]
        missingness[column] = {"missing": missing, "percent": _percent(missing, total)}
    flags = {
        name: connection.execute(
            f"SELECT SUM({name}=1) FROM analytics_msa_industry_year"
        ).fetchone()[0] or 0
        for name in (
            "bds_has_suppression", "bds_startup_available", "qcew_has_suppression",
            "acs_matched", "acs_has_suppression", "acs_has_missing_controls",
            "cbp_matched", "cbp_has_suppression", "has_suppression",
        )
    }
    flags["qcew_incomplete_county_coverage"] = connection.execute(
        "SELECT SUM(qcew_is_complete_county_coverage=0) FROM analytics_msa_industry_year"
    ).fetchone()[0] or 0
    flags["cbp_incomplete_county_coverage"] = connection.execute(
        "SELECT SUM(cbp_is_complete_county_coverage=0) FROM analytics_msa_industry_year"
    ).fetchone()[0] or 0
    return {
        "final_rows": total,
        "metropolitan_msas": panel[0], "industries": panel[1], "years": panel[2],
        "minimum_year": panel[3], "maximum_year": panel[4],
        "msa_industry_panels": panels, "balanced_panels_14_years": balanced,
        "unbalanced_panels": panels-balanced,
        "average_rows_per_panel": round(total/panels, 4) if panels else 0,
        "duplicate_keys": duplicate_count,
        "year_coverage": years, "industry_coverage": industries,
        "msa_coverage": msa_coverage,
        "extreme_low_coverage_msas": msa_coverage[:10],
        "missingness": missingness, "quality_flags": flags,
    }


def _write_export(connection: sqlite3.Connection, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [row[1] for row in connection.execute("PRAGMA table_info(v_analytics_msa_industry_year)")]
    cursor = connection.execute("SELECT * FROM v_analytics_msa_industry_year ORDER BY year,cbsa_code,sector_code")
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as zipped:
            import io
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as text:
                writer = csv.writer(text)
                writer.writerow(columns)
                writer.writerows(cursor)


def _write_report(result: dict[str, Any], path: Path) -> None:
    merge = result["merge_audit"]
    lines = [
        "# Assignment 4.12 Merge Audit", "",
        "## Scope", "",
        f"Primary panel: metropolitan MSA x 2022 NAICS sector x year; {result['panel']['minimum_year']}-"
        f"{result['panel']['maximum_year']}. BDS micropolitan intermediate rows excluded: "
        f"{result['geography']['micropolitan_bds_intermediate_rows_excluded']:,}. Metropolitan codes in BDS: "
        f"{result['geography']['bds_msa_count']:,}.", "",
        "Industry codes are official standardized 2022 broad sectors. Unresolved source sectors: "
        f"{', '.join(result['industry']['unresolved_sectors']) or 'none'}.", "",
        "## Source Key Checks", "",
        "| Source | Rows | Duplicate keys |", "| --- | ---: | ---: |",
    ]
    for source, data in result["source_key_checks"].items():
        lines.append(f"| {source} | {data['rows']:,} | {data['duplicates']:,} |")
    lines += ["", "## Common Industries", "", "| Source | Sectors |", "| --- | --- |"]
    for source, values in result["industry"]["source_sectors"].items():
        lines.append(f"| {source} | {', '.join(values)} |")
    lines += [
        "", f"Common sectors: {', '.join(result['industry']['common_sectors'])}.",
        f"Sectors missing from one or more sources: {', '.join(result['industry']['not_common']) or 'none'}.",
        "", "## Merge Audits", "",
        "| Merge | Before rows | Matched | Left-only | Right-only | After rows | Match rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| BDS inner QCEW | BDS {merge['bds_rows']:,}; QCEW {merge['qcew_rows']:,} | "
        f"{merge['bds_qcew_matched']:,} | BDS {merge['bds_only']:,} | QCEW {merge['qcew_only']:,} | "
        f"{merge['bds_qcew_matched']:,} | {merge['bds_match_percent']:.2f}% of BDS; "
        f"{merge['qcew_match_percent']:.2f}% of QCEW |",
        f"| + ACS left | {merge['bds_qcew_matched']:,} | {merge['acs_matched']:,} | "
        f"{merge['acs_unmatched']:,} | 0 | {merge['after_acs']:,} | {merge['acs_match_percent']:.2f}% |",
        f"| + CBP left | {merge['after_acs']:,} | {merge['cbp_matched']:,} | "
        f"{merge['cbp_unmatched']:,} | 0 | {merge['after_cbp']:,} | {merge['cbp_match_percent']:.2f}% |",
        "", "The core uses an inner BDS-QCEW join because both accepted BDS startup and QCEW growth "
        "observations define the primary research relationship. ACS and CBP are left-joined so missing "
        "controls/support measures do not remove core observations. ACS and source key uniqueness are "
        "checked before integration.",
        "", "## Final Panel", "",
        f"Rows: {result['panel']['final_rows']:,}; MSAs: {result['panel']['metropolitan_msas']:,}; "
        f"industries: {result['panel']['industries']:,}; years: {result['panel']['minimum_year']}-"
        f"{result['panel']['maximum_year']}; MSA-industry panels: {result['panel']['msa_industry_panels']:,}; "
        f"14-year balanced panels: {result['panel']['balanced_panels_14_years']:,}; unbalanced panels: "
        f"{result['panel']['unbalanced_panels']:,}; average rows/panel: "
        f"{result['panel']['average_rows_per_panel']:.2f}; duplicate keys: {result['panel']['duplicate_keys']:,}.",
        "",
    ]
    lines += ["", "### Source Quality Flags", "", "| Flag | Rows flagged |", "| --- | ---: |"]
    for name, count in result["panel"]["quality_flags"].items():
        lines.append(f"| `{name}` | {count:,} |")
    lines += ["", "### Year Coverage", "", "| Year | Rows | MSAs | Sectors | Startup rate | QCEW growth | ACS complete | CBP matched |", "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in result["panel"]["year_coverage"]:
        lines.append(f"| {row['year']} | {row['rows']:,} | {row['msas']:,} | {row['industries']:,} | {row['startup']:,} | {row['qcew_growth']:,} | {row['acs']:,} | {row['cbp']:,} |")
    if result["panel"]["minimum_year"] == 2010:
        lines += ["", "QCEW 2010 levels are present, but 2010 growth fields lack a prior-year observation within the source window. 2010 remains in the panel rather than being silently removed."]
    lines += ["", "### Sector Coverage", "", "| Sector | Rows | MSAs | Years | Startup | QCEW growth | ACS complete | CBP matched |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in result["panel"]["industry_coverage"]:
        lines.append(f"| {row['sector']} | {row['rows']:,} | {row['msas']:,} | {row['years']:,} | {row['startup']:,} | {row['qcew_growth']:,} | {row['acs']:,} | {row['cbp']:,} |")
    lines += ["", "### MSA Coverage", "", "Every MSA's row, industry, and year counts are listed; the lowest-coverage MSAs are shown first.", "", "| CBSA | Name | Rows | Sectors | Years |", "| --- | --- | ---: | ---: | ---: |"]
    for row in result["panel"]["msa_coverage"]:
        lines.append(f"| {row['cbsa_code']} | {row['cbsa_name']} | {row['rows']:,} | {row['industries']:,} | {row['years']:,} |")
    lines += ["", "## Variable Missingness", "", "| Variable | Missing | Percent |", "| --- | ---: | ---: |"]
    for name, row in result["panel"]["missingness"].items():
        lines.append(f"| `{name}` | {row['missing']:,} | {row['percent']:.2f}% |")
    lines += ["", "## QCEW-CBP Consistency Diagnostics", "", "These are descriptive comparisons, not equality requirements. QCEW employment is an annual average while CBP employment is a March reference-period count. QCEW payroll is in dollars and CBP payroll fields are in $1,000; CBP payroll is multiplied by 1,000 for these diagnostics only. Stored source values retain their native units. Coverage and reporting conventions may also differ.", "", "| Measure | Matched | Correlation | Median CBP/QCEW | Median absolute pct. difference | >100% differences |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for name, row in result["cross_source_validation"].items():
        corr = "NA" if row['correlation'] is None else f"{row['correlation']:.4f}"
        ratio = "NA" if row['median_cbp_to_qcew_ratio'] is None else f"{row['median_cbp_to_qcew_ratio']:.4f}"
        apd = "NA" if row['median_absolute_percentage_difference'] is None else f"{row['median_absolute_percentage_difference']:.4f}"
        lines.append(f"| {name} | {row['matched_observations']:,} | {corr} | {ratio} | {apd} | {row['major_disagreement_over_100pct']:,} |")
    lines += ["", "For observations with more than 100% absolute difference, the year/sector/MSA breakdowns and the ten highest-count MSAs are available in the ignored generated JSON audit `reports/generated/a412_panel_audit.json`.", "", "## Idempotency And Leakage Boundary", "", f"Build run {result['pipeline_run_id']} wrote {result['panel']['final_rows']:,} rows. The runner clears and deterministically rebuilds only the analytics table; it refuses duplicate source keys and records run-scoped metrics. No expected entrepreneurship, alignment residual, gap label, future lead, or modeling field is created.", ""]
    lines += ["", "### Major Differences By Year, Sector, And MSA", ""]
    for measure, validation in result["cross_source_validation"].items():
        lines += [f"**{measure.title()}** (groups ranked by observations with >100% absolute difference)", ""]
        for dimension in ("by_year", "by_sector", "by_msa"):
            top = sorted(
                ((key, value["major_disagreement_over_100pct"], value["matched_observations"])
                 for key, value in validation[dimension].items()),
                key=lambda row: (-row[1], row[0]),
            )[:5]
            lines.append(f"{dimension.replace('_', ' ').title()}: " + "; ".join(
                f"{key} ({count}/{matched})" for key, count, matched in top if count
            ) if any(row[1] for row in top) else f"{dimension.replace('_', ' ').title()}: no >100% differences")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _persist_metrics(connection: sqlite3.Connection, run_id: str, result: dict[str, Any]) -> None:
    metrics: dict[str, tuple[float, str]] = {
        "analytical_row_count": (result["panel"]["final_rows"], "MSA x sector x year"),
        "msa_count": (result["panel"]["metropolitan_msas"], "MSAs"),
        "industry_count": (result["panel"]["industries"], "2022 NAICS sectors"),
        "panel_count": (result["panel"]["msa_industry_panels"], "MSA-sector panels"),
        "balanced_panel_count": (result["panel"]["balanced_panels_14_years"], "14-year balanced panels"),
        "duplicate_key_count": (result["panel"]["duplicate_keys"], "analytics primary key"),
        "missing_bds_startup_rate_count": (result["panel"]["missingness"]["startup_rate"]["missing"], "accepted BDS core rows"),
        "missing_qcew_employment_count": (result["panel"]["missingness"]["qcew_employment"]["missing"], "core rows"),
        "missing_acs_control_row_count": (result["merge_audit"]["acs_unmatched"], "core rows without ACS MSA-year match"),
        "missing_cbp_support_row_count": (result["merge_audit"]["cbp_unmatched"], "core rows without CBP match"),
        "bds_qcew_match_rate": (result["merge_audit"]["bds_match_percent"], "percent of metropolitan BDS keys"),
        "acs_match_rate": (result["merge_audit"]["acs_match_percent"], "percent of BDS-QCEW core rows"),
        "cbp_match_rate": (result["merge_audit"]["cbp_match_percent"], "percent of BDS-QCEW core rows"),
        "bds_qcew_matched_rows": (result["merge_audit"]["bds_qcew_matched"], "core rows"),
        "bds_only_rows": (result["merge_audit"]["bds_only"], "unmatched metropolitan BDS keys"),
        "qcew_only_rows": (result["merge_audit"]["qcew_only"], "unmatched metropolitan QCEW keys"),
        "acs_matched_rows": (result["merge_audit"]["acs_matched"], "core rows with ACS key"),
        "acs_unmatched_rows": (result["merge_audit"]["acs_unmatched"], "core rows without ACS key"),
        "cbp_matched_rows": (result["merge_audit"]["cbp_matched"], "core rows with CBP key"),
        "cbp_unmatched_rows": (result["merge_audit"]["cbp_unmatched"], "core rows without CBP key"),
    }
    for source, count in result["source_key_checks"].items():
        metrics[f"{source.lower()}_source_key_duplicates"] = (count["duplicates"], "source intermediate keys")
    for name, item in result["panel"]["missingness"].items():
        metrics[f"missing_{name}"] = (item["missing"], "analytical variable missing count")
    for name, count in result["panel"]["quality_flags"].items():
        metrics[f"rows_flagged_{name}"] = (count, "analytical row quality flag")
    for metric, (value, scope) in metrics.items():
        insert_quality_metric(
            connection, pipeline_run_id=run_id, table_name="analytics_msa_industry_year",
            metric_name=metric, metric_value=float(value), scope=scope,
        )


def build_panel(
    connection: sqlite3.Connection,
    *,
    export_path: Path | None = None,
    report_path: Path | None = None,
) -> dict[str, Any]:
    """Validate inputs, rebuild analytics panel, and persist audit outputs."""
    connection.row_factory = sqlite3.Row
    create_schema(connection)
    keys_before = _assert_unique_keys(connection)
    run_id = start_pipeline_run(connection, stage="build_analytics_msa_industry_year")
    try:
        source_keys = {}
        for source, (table, include_industry) in SOURCE_TABLES.items():
            source_keys[source] = _keys(connection, table, include_industry)
        msa_ids = {
            row[0] for row in connection.execute("SELECT geography_id FROM ref_geography WHERE geography_type='MSA'")
        }
        source_keys["BDS"] = {k for k in source_keys["BDS"] if k[0] in msa_ids and YEARS[0] <= k[2] <= YEARS[1]}
        source_keys["QCEW"] = {k for k in source_keys["QCEW"] if k[0] in msa_ids and YEARS[0] <= k[2] <= YEARS[1]}
        source_keys["CBP"] = {k for k in source_keys["CBP"] if k[0] in msa_ids and YEARS[0] <= k[2] <= YEARS[1]}
        source_keys["ACS"] = {k for k in source_keys["ACS"] if k[0] in msa_ids and YEARS[0] <= k[1] <= YEARS[1]}
        sectors = _source_sectors(connection)
        common = set.intersection(*sectors.values())
        all_sectors = set.union(*sectors.values())
        industry_ids = {
            row[0]: row[1] for row in connection.execute(
                f"SELECT industry_id,naics_code FROM ref_industry WHERE naics_level=2 AND naics_code IN ({','.join('?' for _ in common)})",
                sorted(common),
            )
        }
        valid_ids = set(industry_ids)
        for source in ("BDS", "QCEW", "CBP"):
            source_keys[source] = {k for k in source_keys[source] if k[1] in valid_ids}
        bds, qcew = source_keys["BDS"], source_keys["QCEW"]
        core = bds & qcew
        acs_keys = {(g, y) for g, y in source_keys["ACS"]}
        acs_matches = sum((g, y) in acs_keys for g, _, y in core)
        cbp = source_keys["CBP"]
        cbp_matches = len(core & cbp)
        # Full geography/industry source scope is validated before the first write.
        with connection:
            # _insert_panel owns the delete and enforces the documented inner/left merge order.
            written = _insert_panel(connection, run_id, common)
            if written != len(core):
                raise AssertionError(f"Expected {len(core)} core rows but inserted {written}")
            duplicates = connection.execute("""SELECT COUNT(*) FROM (
                SELECT geography_id,industry_id,year,COUNT(*) n FROM analytics_msa_industry_year
                GROUP BY geography_id,industry_id,year HAVING n>1)""").fetchone()[0]
            if duplicates:
                raise AssertionError(f"Analytics primary key has {duplicates} duplicate groups")
        merge_audit = {
            "bds_rows": len(bds), "qcew_rows": len(qcew), "bds_unique_keys": len(bds),
            "qcew_unique_keys": len(qcew), "bds_qcew_matched": len(core),
            "bds_only": len(bds-core), "qcew_only": len(qcew-bds),
            "bds_match_percent": _percent(len(core),len(bds)),
            "qcew_match_percent": _percent(len(core),len(qcew)),
            "acs_matched": acs_matches, "acs_unmatched": len(core)-acs_matches,
            "acs_match_percent": _percent(acs_matches,len(core)), "after_acs": written,
            "cbp_matched": cbp_matches, "cbp_unmatched": len(core)-cbp_matches,
            "cbp_match_percent": _percent(cbp_matches,len(core)), "after_cbp": written,
        }
        panel = _panel_audits(connection)
        if panel["duplicate_keys"] != 0:
            raise AssertionError("Analytics primary key uniqueness failed")
        diagnostics = _cross_source_diagnostics(connection)
        source_key_checks = {
            source: {"rows": len(_keys(connection, table, include_industry)), "duplicates": keys_before[source]}
            for source, (table, include_industry) in SOURCE_TABLES.items()
        }
        raw_staged_counts = {
            "bds_msa_rows": len(bds),
            "micropolitan_bds_intermediate_rows_excluded": connection.execute("""SELECT COUNT(*)
                FROM int_entrepreneurship e JOIN ref_geography g USING(geography_id)
                WHERE g.geography_type='MICROPOLITAN' AND e.year BETWEEN ? AND ?""", YEARS).fetchone()[0],
            "bds_msa_count": len({k[0] for k in bds}),
        }
        result: dict[str, Any] = {
            "pipeline_run_id": run_id,
            "source_key_checks": source_key_checks,
            "geography": raw_staged_counts,
            "industry": {
                "source_sectors": {k: sorted(v) for k,v in sectors.items()},
                "common_sectors": sorted(common),
                "not_common": sorted(all_sectors-common),
                "unresolved_sectors": [],
            },
            "merge_audit": merge_audit,
            "panel": panel,
            "cross_source_validation": diagnostics,
        }
        with connection:
            _persist_metrics(connection, run_id, result)
        finish_pipeline_run(
            connection, run_id, records_read=sum(x["rows"] for x in source_key_checks.values()),
            records_written=written, records_rejected=merge_audit["bds_only"]+merge_audit["qcew_only"],
        )
        if export_path is not None:
            _write_export(connection, export_path)
            result["export_path"] = str(export_path)
        if report_path is not None:
            _write_report(result, report_path)
            result["report_path"] = str(report_path)
        return result
    except Exception as exc:
        finish_pipeline_run(connection, run_id, status="failed", error_message=str(exc))
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-path", type=Path, default=PRODUCTION_DATABASE)
    parser.add_argument("--export-path", type=Path, default=PROJECT_ROOT / "data/processed/analytics_msa_industry_year.csv.gz")
    parser.add_argument("--report-path", type=Path, default=PROJECT_ROOT / "reports/assignment4_merge_audit.md")
    parser.add_argument("--json-output", type=Path, default=PROJECT_ROOT / "reports/generated/a412_panel_audit.json")
    args = parser.parse_args()
    with connect_database(args.database_path) as connection:
        result = build_panel(connection, export_path=args.export_path, report_path=args.report_path)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "pipeline_run_id": result["pipeline_run_id"],
        "merge_audit": result["merge_audit"],
        "panel": {k:v for k,v in result["panel"].items() if k not in {"year_coverage","industry_coverage","msa_coverage","extreme_low_coverage_msas","missingness"}},
        "cross_source_validation": {k:{x:y for x,y in v.items() if x not in {"by_year","by_sector","by_msa","highest_major_disagreement_msas"}} for k,v in result["cross_source_validation"].items()},
        "export_path": result["export_path"], "report_path": result["report_path"],
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
