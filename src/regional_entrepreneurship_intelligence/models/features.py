"""Preliminary time-safe feature registry, with no transformed matrices."""

from __future__ import annotations

from regional_entrepreneurship_intelligence.models.design import PRIMARY_GROWTH, PRIMARY_OUTCOME

FEATURE_REGISTRY = (
    {"variable": PRIMARY_OUTCOME, "source": "BDS", "role": "current entrepreneurship", "timing": "t", "tier": "primary", "expected_eligible": "response only", "predictive_eligible": "yes", "transformation": "retain source percent units", "missingness": "core outcome observed in accepted panel", "leakage_risk": "high if shifted from t+3", "notes": "Predictor-year observed startup rate; expected model response at outcome year."},
    {"variable": "startup_rate_lag1", "source": "BDS", "role": "prior entrepreneurship", "timing": "t-1", "tier": "primary", "expected_eligible": "yes", "predictive_eligible": "yes", "transformation": "none specified", "missingness": "13.66% in A5 panel", "leakage_risk": "moderate; verify calendar lag", "notes": "Primary lag; do not require lag2/lag3."},
    {"variable": "startup_rate_lag2", "source": "BDS", "role": "prior entrepreneurship", "timing": "t-2", "tier": "sensitivity", "expected_eligible": "sensitivity", "predictive_eligible": "sensitivity", "transformation": "none specified", "missingness": "20.41% in A5 panel", "leakage_risk": "moderate; verify calendar lag", "notes": "Compare only if sample/availability effects are reported."},
    {"variable": "startup_rate_lag3", "source": "BDS", "role": "prior entrepreneurship", "timing": "t-3", "tier": "sensitivity", "expected_eligible": "sensitivity", "predictive_eligible": "sensitivity", "transformation": "none specified", "missingness": "27.01% in A5 panel", "leakage_risk": "moderate; verify calendar lag", "notes": "Compare only if sample/availability effects are reported."},
    {"variable": "establishment_entry", "source": "BDS", "role": "supporting entrepreneurship", "timing": "t", "tier": "sensitivity", "expected_eligible": "sensitivity", "predictive_eligible": "sensitivity", "transformation": "retain source count", "missingness": "source-specific availability", "leakage_risk": "high if future year used", "notes": "Robustness measure; does not replace startup rate."},
    {"variable": "establishment_entry_rate", "source": "BDS", "role": "supporting entrepreneurship", "timing": "t", "tier": "sensitivity", "expected_eligible": "sensitivity", "predictive_eligible": "sensitivity", "transformation": "retain source units", "missingness": "source-specific availability", "leakage_risk": "high if future year used", "notes": "Review definition; A5 flagged values above 100."},
    {"variable": "firm_startups", "source": "BDS", "role": "supporting entrepreneurship", "timing": "t", "tier": "sensitivity", "expected_eligible": "sensitivity", "predictive_eligible": "sensitivity", "transformation": "retain source count", "missingness": "source-specific availability", "leakage_risk": "high if future year used", "notes": "Count robustness measure only."},
    {"variable": "startup_job_creation", "source": "BDS", "role": "supporting entrepreneurship", "timing": "t", "tier": "sensitivity", "expected_eligible": "sensitivity", "predictive_eligible": "sensitivity", "transformation": "retain source count", "missingness": "source-specific availability", "leakage_risk": "high if future year used", "notes": "Count robustness measure only."},
    {"variable": PRIMARY_GROWTH, "source": "QCEW", "role": "industry growth", "timing": "t", "tier": "primary", "expected_eligible": "yes", "predictive_eligible": "yes", "transformation": "retain decimal rate; robust sensitivity only", "missingness": "about 10.17%", "leakage_risk": "high if future year used", "notes": "Primary growth measure; heavy tails and denominators require diagnostics."},
    {"variable": "establishment_growth", "source": "QCEW", "role": "industry growth", "timing": "t", "tier": "supporting/alternative", "expected_eligible": "alternative", "predictive_eligible": "alternative", "transformation": "retain decimal rate", "missingness": "about 10.17%", "leakage_risk": "high if future year used", "notes": "Do not automatically combine with correlated growth measures."},
    {"variable": "payroll_growth", "source": "QCEW", "role": "industry growth", "timing": "t", "tier": "supporting/alternative", "expected_eligible": "alternative", "predictive_eligible": "alternative", "transformation": "retain decimal rate", "missingness": "about 10.17%", "leakage_risk": "high if future year used", "notes": "Pearson association with employment growth is 0.714."},
    {"variable": "wage_growth", "source": "QCEW", "role": "industry growth", "timing": "t", "tier": "supporting/alternative", "expected_eligible": "alternative", "predictive_eligible": "alternative", "transformation": "retain decimal rate", "missingness": "about 10.17%", "leakage_risk": "high if future year used", "notes": "Alternative specification or robustness only."},
    {"variable": "acs_population_growth", "source": "ACS", "role": "regional context", "timing": "t (MSA-year)", "tier": "candidate", "expected_eligible": "candidate", "predictive_eligible": "candidate", "transformation": "retain decimal rate", "missingness": "12.68%", "leakage_risk": "high; MSA-year repeated across sectors", "notes": "Keep MSA-year origin grain in summaries and validation."},
    {"variable": "median_household_income", "source": "ACS", "role": "regional context", "timing": "t (MSA-year)", "tier": "candidate", "expected_eligible": "candidate", "predictive_eligible": "candidate", "transformation": "source dollars; no transform chosen", "missingness": "about 5.56%", "leakage_risk": "high; MSA-year repeated across sectors", "notes": "Correlates 0.613 with educational attainment."},
    {"variable": "educational_attainment_pct", "source": "ACS", "role": "regional context", "timing": "t (MSA-year)", "tier": "candidate", "expected_eligible": "candidate", "predictive_eligible": "candidate", "transformation": "retain percent units", "missingness": "about 5.56%", "leakage_risk": "high; MSA-year repeated across sectors", "notes": "Check redundancy with income."},
    {"variable": "labor_force_participation_pct", "source": "ACS", "role": "regional context", "timing": "t (MSA-year)", "tier": "candidate", "expected_eligible": "candidate", "predictive_eligible": "candidate", "transformation": "retain percent units", "missingness": "about 5.56%", "leakage_risk": "high; MSA-year repeated across sectors", "notes": "Candidate regional control."},
    {"variable": "unemployment_rate", "source": "ACS", "role": "regional context", "timing": "t (MSA-year)", "tier": "candidate", "expected_eligible": "candidate", "predictive_eligible": "candidate", "transformation": "retain percent units", "missingness": "about 5.56%", "leakage_risk": "high; MSA-year repeated across sectors", "notes": "Candidate regional control."},
    {"variable": "sector_code", "source": "NAICS reference", "role": "sector context", "timing": "fixed panel classification", "tier": "mandatory effect", "expected_eligible": "yes", "predictive_eligible": "yes", "transformation": "categorical fixed effects", "missingness": "none in analysis panel", "leakage_risk": "low", "notes": "19 sectors; growth-by-sector interaction compared, not forced."},
    {"variable": "year", "source": "panel key", "role": "year context", "timing": "t", "tier": "mandatory effect", "expected_eligible": "yes", "predictive_eligible": "yes", "transformation": "categorical/time effect", "missingness": "none", "leakage_risk": "moderate; preserve temporal ordering", "notes": "Retain COVID years in primary data."},
    {"variable": "cbsa_code", "source": "Census geography reference", "role": "geographic identity", "timing": "fixed geography", "tier": "sensitivity/grouping", "expected_eligible": "sensitivity only", "predictive_eligible": "grouping/robustness, not primary FE", "transformation": "no primary MSA fixed effects", "missingness": "none in analysis panel", "leakage_risk": "high for geographic holdout", "notes": "Use MSA holdout only as A6.6 robustness."},
)

PROHIBITED_FEATURES = frozenset(
    {"startup_rate_t_plus_1", "startup_rate_t_plus_2", "startup_rate_t_plus_3", "gap_status_t_plus_3", "alignment_residual_t_plus_3", "expected_startup_rate_t_plus_3"}
)


def validate_feature_timing(feature_names: tuple[str, ...] | list[str]) -> None:
    registry_names = {row["variable"] for row in FEATURE_REGISTRY}
    forbidden = sorted(set(feature_names) & PROHIBITED_FEATURES)
    unknown = sorted(set(feature_names) - registry_names)
    if forbidden:
        raise ValueError(f"Future outcome or target fields are prohibited predictors: {forbidden}")
    if unknown:
        raise ValueError(f"Features are absent from the preliminary registry: {unknown}")


def validate_feature_years(feature_years: dict[str, int], predictor_year: int) -> None:
    future = {name: year for name, year in feature_years.items() if year > predictor_year}
    if future:
        raise ValueError(f"Feature values occur after prediction year {predictor_year}: {future}")
