"""Read-only foundations and variable groups for Assignment 5 EDA."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
import re

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EDA_DATABASE = PROJECT_ROOT / "database" / "assignment4_production.sqlite"
ANALYTICAL_VIEW = "v_analytics_msa_industry_year"
STUDY_YEARS = (2010, 2023)
PANEL_KEYS = ("geography_id", "industry_id", "year")
REQUIRED_EDA_FIELDS = frozenset(
    {
        *PANEL_KEYS,
        "cbsa_code",
        "sector_code",
        "startup_rate",
        "employment_growth",
        "acs_population_growth",
        "median_household_income",
        "educational_attainment_pct",
        "labor_force_participation_pct",
        "unemployment_rate",
    }
)
FORBIDDEN_FIELD_FRAGMENTS = (
    "target",
    "label",
    "prediction",
    "expected_entrepreneurship",
    "alignment",
    "entrepreneurial_gap",
    "future_",
    "lead_",
)

VARIABLE_GROUPS: dict[str, frozenset[str]] = {
    "identifier": frozenset(
        {"geography_id", "industry_id", "year", "cbsa_code", "cbsa_name", "sector_code", "sector_title"}
    ),
    "entrepreneurship": frozenset(
        {
            "startup_rate",
            "firm_startups",
            "startup_rate_lag1",
            "startup_rate_lag2",
            "startup_rate_lag3",
            "establishment_entry",
            "establishment_entry_rate",
            "startup_job_creation",
        }
    ),
    "industry_growth": frozenset(
        {
            "qcew_employment",
            "qcew_establishments",
            "qcew_payroll",
            "qcew_average_wage",
            "qcew_total_annual_wages_nominal",
            "qcew_average_annual_pay_nominal",
            "employment_growth",
            "establishment_growth",
            "payroll_growth",
            "wage_growth",
            "employment_growth_lag1",
            "employment_growth_lag2",
            "employment_growth_lag3",
            "establishment_growth_lag1",
            "establishment_growth_lag2",
            "establishment_growth_lag3",
            "payroll_growth_lag1",
            "average_pay_growth_lag1",
        }
    ),
    "regional_control": frozenset(
        {
            "acs_population",
            "acs_population_growth",
            "acs_population_growth_lag1",
            "median_household_income",
            "median_household_income_lag1",
            "educational_attainment_pct",
            "educational_attainment_pct_lag1",
            "labor_force_participation_pct",
            "labor_force_participation_pct_lag1",
            "unemployment_rate",
            "unemployment_rate_lag1",
        }
    ),
    "business_structure": frozenset(
        {"cbp_establishments", "cbp_employment", "cbp_annual_payroll", "cbp_first_quarter_payroll"}
    ),
    "quality_flag": frozenset(
        {
            "bds_has_suppression",
            "bds_startup_available",
            "qcew_has_suppression",
            "qcew_is_complete_county_coverage",
            "qcew_is_real_adjusted",
            "acs_matched",
            "acs_has_suppression",
            "acs_has_missing_controls",
            "cbp_matched",
            "cbp_has_suppression",
            "cbp_is_complete_county_coverage",
            "has_suppression",
        }
    ),
    "metadata_supporting": frozenset({"source_quality_notes"}),
}

_PROHIBITED_NAME_FRAGMENTS = FORBIDDEN_FIELD_FRAGMENTS
_LAG_PATTERN = re.compile(r"_lag(\d+)$")

PATTERN_MEASURES = (
    "startup_rate", "employment_growth", "establishment_growth", "payroll_growth",
    "wage_growth", "acs_population_growth", "unemployment_rate",
    "educational_attainment_pct", "median_household_income",
    "labor_force_participation_pct",
)
ACS_MSA_YEAR_MEASURES = (
    "acs_population_growth", "median_household_income", "educational_attainment_pct",
    "labor_force_participation_pct", "unemployment_rate",
)


def _grouped_measure_summary(frame: pd.DataFrame, keys: list[str], measures: tuple[str, ...]) -> pd.DataFrame:
    """Long-form distribution statistics with explicit observed and missing N."""
    missing = set(keys + list(measures)) - set(frame.columns)
    if missing:
        raise ValueError(f"Summary fields are absent: {sorted(missing)}")
    records: list[dict[str, object]] = []
    for group_key, group in frame.groupby(keys, sort=True, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        labels = dict(zip(keys, group_key))
        for variable in measures:
            values = pd.to_numeric(group[variable], errors="coerce").dropna()
            row: dict[str, object] = {
                **labels, "variable": variable, "row_count": len(group),
                "count": int(values.count()), "missing_count": int(group[variable].isna().sum()),
                "missing_pct": float(group[variable].isna().mean() * 100),
                "mean": float(values.mean()) if len(values) else np.nan,
                "median": float(values.median()) if len(values) else np.nan,
                "std": float(values.std(ddof=1)) if len(values) > 1 else np.nan,
                "p05": float(values.quantile(.05)) if len(values) else np.nan,
                "p25": float(values.quantile(.25)) if len(values) else np.nan,
                "p75": float(values.quantile(.75)) if len(values) else np.nan,
                "p95": float(values.quantile(.95)) if len(values) else np.nan,
                "min": float(values.min()) if len(values) else np.nan,
                "max": float(values.max()) if len(values) else np.nan,
            }
            row["iqr"] = row["p75"] - row["p25"] if len(values) else np.nan
            row["mad"] = float((values - values.median()).abs().median()) if len(values) else np.nan
            row["zero_pct"] = float(values.eq(0).mean() * 100) if len(values) else np.nan
            records.append(row)
    return pd.DataFrame(records)


def summarize_by_year(frame: pd.DataFrame, measures: tuple[str, ...] = PATTERN_MEASURES) -> pd.DataFrame:
    """Summarize annual panel measures; ACS values remain available-case panel rows."""
    return _grouped_measure_summary(frame, ["year"], measures)


def summarize_by_sector(frame: pd.DataFrame, measures: tuple[str, ...] = PATTERN_MEASURES) -> pd.DataFrame:
    """Summarize distributions across the observed sector rows."""
    result = _grouped_measure_summary(frame, ["sector_code"], measures)
    coverage = frame.groupby("sector_code").agg(
        msa_count=("geography_id", "nunique"), year_count=("year", "nunique"),
    )
    return result.join(coverage, on="sector_code")


def summarize_sector_volatility(frame: pd.DataFrame, measures: tuple[str, ...] = (
    "startup_rate", "employment_growth",
)) -> pd.DataFrame:
    """Report robust and conventional sector dispersion measures."""
    return summarize_by_sector(frame, measures)


def collapse_acs_to_msa_year(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate repeated ACS values, then retain one record per MSA-year."""
    keys = ["geography_id", "year"]
    columns = keys + [c for c in ("cbsa_code", "cbsa_name", *ACS_MSA_YEAR_MEASURES) if c in frame]
    acs = frame[columns].copy()
    for column in ACS_MSA_YEAR_MEASURES:
        if column in acs:
            inconsistent = acs.groupby(keys, dropna=False)[column].nunique(dropna=False).gt(1)
            if inconsistent.any():
                raise ValueError(f"Conflicting repeated MSA-year ACS values: {column}")
    return acs.drop_duplicates(keys, keep="first").sort_values(keys).reset_index(drop=True)


def summarize_msa_coverage(frame: pd.DataFrame, *, min_rows: int = 100,
                           min_sectors: int = 5, min_years: int = 10) -> pd.DataFrame:
    """Keep all MSAs and flag comparison eligibility using explicit coverage rules."""
    coverage = frame.groupby(["geography_id", "cbsa_code", "cbsa_name"], dropna=False).agg(
        row_count=("year", "size"), sector_count=("sector_code", "nunique"),
        year_count=("year", "nunique"), panel_count=("industry_id", "nunique"),
    ).reset_index()
    coverage["eligible_for_comparison"] = (
        coverage.row_count.ge(min_rows) & coverage.sector_count.ge(min_sectors)
        & coverage.year_count.ge(min_years)
    )
    return coverage


def summarize_by_msa(frame: pd.DataFrame, measures: tuple[str, ...] = PATTERN_MEASURES,
                     *, min_rows: int = 100, min_sectors: int = 5,
                     min_years: int = 10) -> pd.DataFrame:
    """Summarize MSA panel distributions and attach non-replicated ACS context."""
    coverage = summarize_msa_coverage(frame, min_rows=min_rows, min_sectors=min_sectors,
                                      min_years=min_years)
    result = _grouped_measure_summary(frame, ["geography_id", "cbsa_code", "cbsa_name"], measures)
    result = result.merge(coverage, on=["geography_id", "cbsa_code", "cbsa_name"],
                          validate="many_to_one")
    acs = collapse_acs_to_msa_year(frame)
    acs_summary = _grouped_measure_summary(acs, ["geography_id"], ACS_MSA_YEAR_MEASURES)
    # Keep one transparent regional median per MSA and control, without industry replication.
    medians = acs_summary[["geography_id", "variable", "median"]]
    medians = medians.pivot(index="geography_id", columns="variable", values="median").reset_index()
    return result.merge(medians, on="geography_id", how="left", validate="many_to_one",
                       suffixes=("", "_acs"))


def build_descriptive_quadrants(
    frame: pd.DataFrame,
    *,
    group_by: tuple[str, ...] = ("year", "sector_code"),
) -> pd.DataFrame:
    """Aggregate contemporaneous sector-year median quadrants; no leads/targets."""
    required = {"year", "sector_code", "geography_id", "cbsa_code", "cbsa_name",
                "startup_rate", "employment_growth"}
    if missing := required - set(frame.columns):
        raise ValueError(f"Quadrant fields are absent: {sorted(missing)}")
    dimensions = list(group_by)
    if not dimensions or set(dimensions) - required:
        raise ValueError("Quadrant grouping must use available year/sector/MSA dimensions")
    rows = frame[[*dict.fromkeys(["year", "sector_code", *dimensions, "geography_id",
                                  "cbsa_code", "cbsa_name", "startup_rate",
                                  "employment_growth"]) ]].copy()
    rows["startup_cutoff"] = rows.groupby(["year", "sector_code"])["startup_rate"].transform("median")
    rows["growth_cutoff"] = rows.groupby(["year", "sector_code"])["employment_growth"].transform("median")
    rows = rows.dropna(subset=["startup_rate", "employment_growth"])
    rows["startup_level"] = np.where(rows.startup_rate.ge(rows.startup_cutoff), "high", "low")
    rows["growth_level"] = np.where(rows.employment_growth.ge(rows.growth_cutoff), "high", "low")
    rows["quadrant"] = rows.growth_level + "_growth_" + rows.startup_level + "_startup"
    grouped = rows.groupby([*dimensions, "quadrant"], as_index=False).agg(
        observation_count=("geography_id", "size"), msa_count=("geography_id", "nunique"),
    )
    totals = grouped.groupby(dimensions)["observation_count"].transform("sum")
    grouped["percent_within_group"] = grouped.observation_count / totals * 100
    return grouped


def calculate_pairwise_relationship(frame: pd.DataFrame, x: str, y: str,
                                    method: str = "pearson") -> dict[str, object]:
    """Return an available-case correlation with its usable sample size."""
    if method not in {"pearson", "spearman"}:
        raise ValueError("method must be 'pearson' or 'spearman'")
    if x not in frame or y not in frame:
        raise ValueError(f"Relationship fields are absent: {x}, {y}")
    from scipy import stats

    data = frame[[x, y]].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    coefficient = p_value = np.nan
    if len(data) >= 3 and data[x].nunique() > 1 and data[y].nunique() > 1:
        result = stats.pearsonr(data[x], data[y]) if method == "pearson" else stats.spearmanr(data[x], data[y])
        coefficient, p_value = float(result.statistic), float(result.pvalue)
    return {"x": x, "y": y, "method": method, "coefficient": coefficient,
            "p_value": p_value, "n": len(data)}


def build_correlation_matrix(frame: pd.DataFrame, variables: tuple[str, ...],
                             method: str = "pearson") -> pd.DataFrame:
    """Compute a complete matrix using pairwise available cases."""
    absent = set(variables) - set(frame.columns)
    if absent:
        raise ValueError(f"Correlation fields are absent: {sorted(absent)}")
    numeric = frame[list(variables)].apply(pd.to_numeric, errors="coerce")
    return numeric.corr(method=method, min_periods=3)


def fit_exploratory_regression(frame: pd.DataFrame, outcome: str,
                               predictors: tuple[str, ...], *,
                               categorical: tuple[str, ...] = (),
                               cluster_keys: tuple[str, ...] = ("geography_id", "industry_id"),
                               model_name: str = "exploratory") -> pd.DataFrame:
    """Fit available-case OLS with panel-clustered covariance; never predicts or labels."""
    import statsmodels.api as sm

    fields = tuple(dict.fromkeys((outcome, *predictors, *categorical, *cluster_keys)))
    absent = set(fields) - set(frame.columns)
    if absent:
        raise ValueError(f"Regression fields are absent: {sorted(absent)}")
    data = frame[list(fields)].copy()
    data[outcome] = pd.to_numeric(data[outcome], errors="coerce")
    data = data.replace([np.inf, -np.inf], np.nan).dropna(subset=[outcome, *predictors, *categorical])
    x = data[list(predictors)].apply(pd.to_numeric, errors="coerce")
    if categorical:
        x = pd.concat([x, pd.get_dummies(data[list(categorical)].astype(str), drop_first=True, dtype=float)], axis=1)
    x = sm.add_constant(x.astype(float), has_constant="add")
    valid = np.isfinite(x).all(axis=1) & np.isfinite(data[outcome])
    x, data = x.loc[valid], data.loc[valid]
    y = data[outcome]
    if len(data) <= x.shape[1] or len(data) < 3:
        raise ValueError(f"Insufficient observations for regression {model_name}: {len(data)}")
    model = sm.OLS(y, x)
    if cluster_keys:
        groups = pd.MultiIndex.from_frame(data[list(cluster_keys)]).factorize()[0]
        fitted = model.fit(cov_type="cluster", cov_kwds={"groups": groups, "use_correction": True})
    else:
        fitted = model.fit(cov_type="HC3")
    ci = fitted.conf_int()
    return pd.DataFrame({
        "model": model_name, "term": fitted.params.index, "coefficient": fitted.params.values,
        "std_error": fitted.bse.values, "ci_lower": ci.iloc[:, 0].values,
        "ci_upper": ci.iloc[:, 1].values, "p_value": fitted.pvalues.values,
        "n": int(fitted.nobs), "r_squared": float(fitted.rsquared),
        "covariance": "panel_clustered" if cluster_keys else "HC3",
    })


def summarize_sector_relationships(frame: pd.DataFrame, *, min_n: int = 10) -> pd.DataFrame:
    """Summarize primary growth/startup correlations and slopes by sector."""
    rows = []
    for sector, group in frame.groupby("sector_code", sort=True):
        pair = group[["startup_rate", "employment_growth"]].dropna()
        pearson = calculate_pairwise_relationship(group, "employment_growth", "startup_rate", "pearson")
        spearman = calculate_pairwise_relationship(group, "employment_growth", "startup_rate", "spearman")
        slope = float(np.polyfit(pair.employment_growth, pair.startup_rate, 1)[0]) if len(pair) >= min_n and pair.employment_growth.nunique() > 1 else np.nan
        rows.append({"sector_code": sector, "n": len(pair), "pearson": pearson["coefficient"],
                     "pearson_p": pearson["p_value"], "spearman": spearman["coefficient"],
                     "spearman_p": spearman["p_value"], "slope": slope,
                     "slope_eligible": len(pair) >= min_n})
    return pd.DataFrame(rows)


def summarize_quadrant_context(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize regional controls after collapsing each MSA-year-quadrant once."""
    dimensions = ["geography_id", "year", "sector_code", "startup_rate", "employment_growth",
                  *ACS_MSA_YEAR_MEASURES]
    absent = set(dimensions) - set(frame.columns)
    if absent:
        raise ValueError(f"Quadrant context fields are absent: {sorted(absent)}")
    work = frame[dimensions].copy()
    work["startup_cutoff"] = work.groupby(["year", "sector_code"]).startup_rate.transform("median")
    work["growth_cutoff"] = work.groupby(["year", "sector_code"]).employment_growth.transform("median")
    work = work.dropna(subset=["startup_rate", "employment_growth"])
    work["quadrant"] = np.where(work.employment_growth.ge(work.growth_cutoff), "high_growth_", "low_growth_") + np.where(
        work.startup_rate.ge(work.startup_cutoff), "high_startup", "low_startup")
    values = ["startup_rate", "employment_growth", *ACS_MSA_YEAR_MEASURES]
    msa_year_quadrant = work.groupby(["geography_id", "year", "quadrant"], as_index=False).agg(
        **{f"{name}_mean": (name, "mean") for name in values}
    )
    return msa_year_quadrant.groupby("quadrant").agg(
        msa_year_count=("geography_id", "size"), msa_count=("geography_id", "nunique"),
        **{f"{name}_mean": (f"{name}_mean", "mean") for name in values},
        **{f"{name}_median": (f"{name}_mean", "median") for name in ACS_MSA_YEAR_MEASURES},
    ).reset_index()


def summarize_lag_relationships(frame: pd.DataFrame) -> pd.DataFrame:
    """Correlate current startup rates with each available historical lag."""
    rows = []
    for lag in (1, 2, 3):
        variable = f"startup_rate_lag{lag}"
        for method in ("pearson", "spearman"):
            result = calculate_pairwise_relationship(frame, variable, "startup_rate", method)
            result["lag"] = lag
            rows.append(result)
    return pd.DataFrame(rows)


def run_covid_sensitivity(frame: pd.DataFrame) -> pd.DataFrame:
    """Compare the primary association on full, exclude-2020, and exclude-2020/21 samples."""
    definitions = (("full", ()), ("exclude_2020", (2020,)), ("exclude_2020_2021", (2020, 2021)))
    rows = []
    for label, excluded in definitions:
        sample = frame.loc[~frame.year.isin(excluded)]
        for method in ("pearson", "spearman"):
            row = calculate_pairwise_relationship(sample, "employment_growth", "startup_rate", method)
            row.update(sensitivity=label, excluded_years=",".join(map(str, excluded)))
            rows.append(row)
    return pd.DataFrame(rows)


def run_outlier_sensitivity(frame: pd.DataFrame) -> pd.DataFrame:
    """Compare full Pearson, full Spearman, and non-destructive P01/P99-trimmed Pearson."""
    pair = frame[["employment_growth", "startup_rate"]].replace([np.inf, -np.inf], np.nan).dropna()
    low, high = pair.employment_growth.quantile([.01, .99])
    trimmed = pair[pair.employment_growth.between(low, high)]
    rows = []
    for label, sample, method in (
        ("full_pearson", pair, "pearson"), ("full_spearman", pair, "spearman"),
        ("exclude_employment_growth_p01_p99", trimmed, "pearson"),
    ):
        row = calculate_pairwise_relationship(sample, "employment_growth", "startup_rate", method)
        row["sensitivity"] = label
        rows.append(row)
    return pd.DataFrame(rows)


def _connect_read_only(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"EDA database does not exist: {path}")
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def validate_eda_schema(connection: sqlite3.Connection) -> set[str]:
    """Check the active analytical view for required fields and leakage names."""
    objects = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
        )
    }
    if ANALYTICAL_VIEW not in objects:
        raise ValueError(f"Required analytical view is missing: {ANALYTICAL_VIEW}")
    columns = {
        row[1] for row in connection.execute(f"PRAGMA table_info({ANALYTICAL_VIEW})")
    }
    missing = REQUIRED_EDA_FIELDS - columns
    if missing:
        raise ValueError(f"Required EDA fields are missing: {sorted(missing)}")
    forbidden = sorted(
        name
        for name in columns
        if any(fragment in name.lower() for fragment in FORBIDDEN_FIELD_FRAGMENTS)
    )
    if forbidden:
        raise ValueError(f"Potential target or leakage fields found: {forbidden}")
    grouped = set().union(*VARIABLE_GROUPS.values())
    invalid = sorted(grouped - columns)
    if invalid:
        raise ValueError(f"EDA variable groups reference absent fields: {invalid}")
    return columns


def load_analytical_panel(
    database_path: str | Path = DEFAULT_EDA_DATABASE,
    *,
    validate: bool = True,
) -> pd.DataFrame:
    """Load the active Assignment 4 panel from SQLite without writing to it."""
    with closing(_connect_read_only(database_path)) as connection:
        columns = validate_eda_schema(connection) if validate else None
        frame = pd.read_sql_query(f"SELECT * FROM {ANALYTICAL_VIEW}", connection)
        if validate:
            assert columns is not None
            if frame.empty:
                raise ValueError("The analytical panel is empty")
            if frame["year"].min() != STUDY_YEARS[0] or frame["year"].max() != STUDY_YEARS[1]:
                raise ValueError(f"Unexpected analytical year range: {frame['year'].min()}-{frame['year'].max()}")
            if frame.duplicated(list(PANEL_KEYS)).any():
                raise ValueError("Duplicate analytical panel keys found")
            non_msa = connection.execute(
                """SELECT COUNT(*) FROM analytics_msa_industry_year AS a
                   JOIN ref_geography AS g USING (geography_id)
                   WHERE g.geography_type IS NOT 'MSA'"""
            ).fetchone()[0]
            if non_msa:
                raise ValueError(f"Non-metropolitan rows found in analytical panel: {non_msa}")
        return frame


def _analysis_columns(
    frame: pd.DataFrame, columns: list[str] | tuple[str, ...] | None
) -> list[str]:
    candidates = list(columns) if columns is not None else list(frame.columns)
    missing = sorted(set(candidates) - set(frame.columns))
    if missing:
        raise ValueError(f"Requested columns are absent: {missing}")
    return [
        name
        for name in candidates
        if not any(fragment in name.lower() for fragment in _PROHIBITED_NAME_FRAGMENTS)
    ]


def summarize_numeric_variables(
    frame: pd.DataFrame,
    variables: list[str] | tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Return non-destructive distribution summaries for numeric fields."""
    columns = _analysis_columns(frame, variables)
    rows: list[dict[str, object]] = []
    for name in columns:
        if not pd.api.types.is_numeric_dtype(frame[name]):
            if variables is not None:
                raise TypeError(f"Requested summary field is not numeric: {name}")
            continue
        series = frame[name]
        finite = series[np.isfinite(series.astype(float))].astype(float)
        values = finite.to_numpy()
        missing_count = int(series.isna().sum())
        row: dict[str, object] = {
            "variable": name,
            "count": int(series.notna().sum()),
            "missing_count": missing_count,
            "missing_pct": float(missing_count / len(frame) * 100) if len(frame) else np.nan,
            "nonfinite_count": int((series.notna() & ~np.isfinite(series.astype(float))).sum()),
            "mean": float(finite.mean()) if len(finite) else np.nan,
            "std": float(finite.std(ddof=1)) if len(finite) > 1 else np.nan,
            "min": float(finite.min()) if len(finite) else np.nan,
        }
        for label, percentile in (
            ("p01", 1), ("p05", 5), ("p25", 25), ("median", 50),
            ("p75", 75), ("p95", 95), ("p99", 99),
        ):
            row[label] = float(np.percentile(values, percentile)) if len(values) else np.nan
        row["max"] = float(finite.max()) if len(finite) else np.nan
        row["skewness"] = float(finite.skew()) if len(finite) >= 3 else np.nan
        row["excess_kurtosis"] = float(finite.kurt()) if len(finite) >= 4 else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_missingness(
    frame: pd.DataFrame,
    variables: list[str] | tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Report present/missing observations for every selected active field."""
    columns = _analysis_columns(frame, variables)
    total = len(frame)
    rows = []
    for name in columns:
        missing = int(frame[name].isna().sum())
        rows.append(
            {
                "variable": name,
                "dtype": str(frame[name].dtype),
                "total_count": total,
                "non_missing_count": total - missing,
                "missing_count": missing,
                "missing_pct": missing / total * 100 if total else np.nan,
            }
        )
    return pd.DataFrame(rows)


def summarize_missingness_by_year(
    frame: pd.DataFrame,
    variables: list[str] | tuple[str, ...],
    *,
    year_column: str = "year",
) -> pd.DataFrame:
    """Return long-form missingness counts and percentages by calendar year."""
    columns = _analysis_columns(frame, variables)
    if year_column not in frame:
        raise ValueError(f"Year field is absent: {year_column}")
    rows: list[dict[str, object]] = []
    for year, group in frame.groupby(year_column, sort=True, dropna=False):
        for name in columns:
            missing = int(group[name].isna().sum())
            rows.append(
                {
                    "year": year,
                    "variable": name,
                    "total_count": len(group),
                    "non_missing_count": len(group) - missing,
                    "missing_count": missing,
                    "missing_pct": missing / len(group) * 100 if len(group) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def summarize_distribution_shape(
    frame: pd.DataFrame,
    variables: list[str] | tuple[str, ...],
) -> pd.DataFrame:
    """Summarize tails, zeros, negatives, and non-destructive IQR/3-SD flags."""
    columns = _analysis_columns(frame, variables)
    rows = []
    for name in columns:
        if not pd.api.types.is_numeric_dtype(frame[name]):
            raise TypeError(f"Distribution field is not numeric: {name}")
        original = frame[name]
        values = original[np.isfinite(original.astype(float))].astype(float)
        if values.empty:
            q1 = q3 = iqr = mean = std = np.nan
            iqr_count = sd_count = 0
        else:
            q1, q3 = values.quantile([0.25, 0.75]).tolist()
            iqr = q3 - q1
            iqr_count = int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum())
            mean = float(values.mean())
            std = float(values.std(ddof=1)) if len(values) > 1 else np.nan
            sd_count = int(((values - mean).abs() > 3 * std).sum()) if np.isfinite(std) and std > 0 else 0
        skewness = float(values.skew()) if len(values) >= 3 else np.nan
        excess_kurtosis = float(values.kurt()) if len(values) >= 4 else np.nan
        zero_count = int((values == 0).sum())
        notes = []
        if np.isfinite(skewness):
            if abs(skewness) >= 2:
                notes.append("highly skewed")
            elif abs(skewness) >= 1:
                notes.append("moderately skewed")
            else:
                notes.append("roughly symmetric by skewness")
        if np.isfinite(excess_kurtosis) and excess_kurtosis > 3:
            notes.append("heavy-tailed screening signal")
        if len(values) and zero_count / len(values) >= 0.05:
            notes.append("zero-concentrated")
        if name in {
            "startup_rate", "establishment_entry_rate", "educational_attainment_pct",
            "labor_force_participation_pct", "unemployment_rate",
        }:
            if len(values) and values.min() >= 0 and values.max() <= 100:
                notes.append("bounded percentage/rate; observed within 0-100 review range")
            else:
                notes.append("percentage/rate; observed range requires definition review")
        if (values < 0).any():
            notes.append("includes negative values; interpretation depends on measure")
        rows.append(
            {
                "variable": name,
                "count": int(original.notna().sum()),
                "missing_count": int(original.isna().sum()),
                "skewness": skewness,
                "excess_kurtosis": excess_kurtosis,
                "min": float(values.min()) if len(values) else np.nan,
                "p01": float(values.quantile(0.01)) if len(values) else np.nan,
                "p99": float(values.quantile(0.99)) if len(values) else np.nan,
                "max": float(values.max()) if len(values) else np.nan,
                "iqr_outlier_count": iqr_count,
                "three_sd_count": sd_count,
                "zero_count": zero_count,
                "negative_count": int((values < 0).sum()),
                "nonfinite_count": int((original.notna() & ~np.isfinite(original.astype(float))).sum()),
                "notes": "; ".join(notes) if notes else "no prominent shape flag from these diagnostics",
            }
        )
    return pd.DataFrame(rows)


def summarize_structural_missingness(
    frame: pd.DataFrame,
    variables: list[str] | tuple[str, ...],
) -> pd.DataFrame:
    """Partition missing values using panel predecessors and source QA flags.

    A lag is structurally unavailable when the required prior calendar-year
    panel key is absent. Source flags are used only for the documented source
    families; any remainder stays explicitly unexplained.
    """
    columns = _analysis_columns(frame, variables)
    work = frame.reset_index(drop=True)
    keys = pd.MultiIndex.from_frame(work[["geography_id", "industry_id", "year"]])
    geography_year_keys = pd.MultiIndex.from_frame(
        work[["geography_id", "year"]].drop_duplicates()
    )
    acs_fields = {
        "median_household_income", "median_household_income_lag1",
        "educational_attainment_pct", "educational_attainment_pct_lag1",
        "labor_force_participation_pct", "labor_force_participation_pct_lag1",
        "unemployment_rate", "unemployment_rate_lag1",
    }
    growth_fields = {
        "employment_growth", "establishment_growth", "payroll_growth", "wage_growth",
        "acs_population_growth",
    }
    rows: list[dict[str, object]] = []
    for name in columns:
        missing = work[name].isna()
        categories = pd.Series(index=work.index, dtype="object")
        lag_match = _LAG_PATTERN.search(name)
        if lag_match:
            lag = int(lag_match.group(1))
            if name.startswith("acs_") or name in acs_fields:
                prior = work[["geography_id", "year"]].copy()
                prior["year"] = prior["year"] - lag
                predecessor_exists = pd.MultiIndex.from_frame(prior).isin(geography_year_keys)
            else:
                prior = work[["geography_id", "industry_id", "year"]].copy()
                prior["year"] = prior["year"] - lag
                predecessor_exists = pd.MultiIndex.from_frame(prior).isin(keys)
            points_to_boundary_growth = name.removesuffix(f"_lag{lag}") in growth_fields
            boundary_missing = (work["year"] - lag).eq(STUDY_YEARS[0]) if points_to_boundary_growth else False
            categories.loc[missing & (~predecessor_exists | boundary_missing)] = "expected_structural_missing"
        elif name in growth_fields:
            categories.loc[missing & work["year"].eq(STUDY_YEARS[0])] = "expected_structural_missing"

        unresolved = missing & categories.isna()

        def flag_category(flag: str, category: str, *, expected: bool) -> None:
            nonlocal unresolved
            if flag not in work:
                return
            flagged = work[flag].eq(1 if expected else 0)
            selected = unresolved & flagged
            categories.loc[selected] = category
            unresolved = unresolved & ~selected

        if name.startswith("cbp_"):
            flag_category("cbp_has_suppression", "source_data_quality_missing", expected=True)
            flag_category("cbp_is_complete_county_coverage", "source_data_quality_missing", expected=False)
            flag_category("cbp_matched", "support_source_missing", expected=False)
        elif name.startswith("acs_") or name in {
            "median_household_income", "median_household_income_lag1",
            "educational_attainment_pct", "educational_attainment_pct_lag1",
            "labor_force_participation_pct", "labor_force_participation_pct_lag1",
            "unemployment_rate", "unemployment_rate_lag1",
        }:
            flag_category("acs_has_suppression", "source_data_quality_missing", expected=True)
            flag_category("acs_matched", "support_source_missing", expected=False)
            flag_category("acs_has_missing_controls", "source_data_quality_missing", expected=True)
        elif name.startswith("qcew_") or name in {
            "employment_growth", "establishment_growth", "payroll_growth", "wage_growth",
            "employment_growth_lag1", "employment_growth_lag2", "employment_growth_lag3",
            "establishment_growth_lag1", "establishment_growth_lag2", "establishment_growth_lag3",
            "payroll_growth_lag1", "average_pay_growth_lag1",
        }:
            flag_category("qcew_has_suppression", "source_data_quality_missing", expected=True)
        elif name.startswith("startup_") or name in {
            "firm_startups", "establishment_entry", "establishment_entry_rate", "startup_job_creation",
        }:
            flag_category("bds_has_suppression", "source_data_quality_missing", expected=True)
            flag_category("bds_startup_available", "source_data_quality_missing", expected=False)

        categories.loc[unresolved] = "unexplained_missing"
        counts = categories.loc[missing].value_counts()
        for category, count in counts.items():
            rows.append({"variable": name, "cause_category": category, "missing_count": count})
        for category in (
            "expected_structural_missing", "source_data_quality_missing",
            "support_source_missing", "unexplained_missing",
        ):
            if category not in counts:
                rows.append({"variable": name, "cause_category": category, "missing_count": 0})
    return pd.DataFrame(rows)


def summarize_economic_plausibility(frame: pd.DataFrame) -> pd.DataFrame:
    """Count clearly impossible or review-worthy values without altering rows."""
    rules: dict[str, tuple[str, str]] = {}
    for name in (
        "firm_startups", "establishment_entry", "startup_job_creation", "qcew_employment",
        "qcew_establishments", "qcew_payroll", "qcew_average_wage",
        "qcew_total_annual_wages_nominal", "qcew_average_annual_pay_nominal",
        "acs_population", "median_household_income", "cbp_establishments", "cbp_employment",
        "cbp_annual_payroll", "cbp_first_quarter_payroll",
    ):
        rules[name] = ("negative_value", "Nonnegative level/count expected; review source and definition")
    for name in (
        "startup_rate", "educational_attainment_pct", "labor_force_participation_pct",
        "unemployment_rate", "establishment_entry_rate",
    ):
        rules[name] = (
            "outside_0_100",
            "Rate outside 0 to 100; review source definition and denominator before calling invalid",
        )
    rows = []
    for name, (rule, note) in rules.items():
        if name not in frame:
            continue
        values = frame[name]
        flagged = values.lt(0) if rule == "negative_value" else (values.lt(0) | values.gt(100))
        rows.append({"variable": name, "rule": rule, "flagged_count": int(flagged.sum()), "notes": note})
    for name in ("employment_growth", "establishment_growth", "payroll_growth", "wage_growth"):
        if name in frame:
            rows.append(
                {
                    "variable": name,
                    "rule": "nonfinite_growth",
                    "flagged_count": int((frame[name].notna() & ~np.isfinite(frame[name].astype(float))).sum()),
                    "notes": "Infinite/NaN numeric growth values require review; large finite values are not automatically invalid",
                }
            )
    return pd.DataFrame(rows)
