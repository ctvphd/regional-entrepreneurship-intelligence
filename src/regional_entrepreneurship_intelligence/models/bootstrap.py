"""Paired cluster-bootstrap uncertainty for frozen model predictions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score


@dataclass(frozen=True)
class BootstrapResult:
    summary: pd.DataFrame
    diagnostics: dict[str, float | int]
    replications: pd.DataFrame | None = None


def _cluster_row_indices(frame: pd.DataFrame, cluster_column: str) -> list[np.ndarray]:
    return [group.index.to_numpy(dtype=int) for _, group in frame.groupby(cluster_column, sort=True)]


def _draw_cluster_rows(cluster_rows: list[np.ndarray], rng: np.random.Generator) -> np.ndarray:
    draws = rng.integers(0, len(cluster_rows), size=len(cluster_rows))
    return np.concatenate([cluster_rows[index] for index in draws])


def _validate_inputs(
    frame: pd.DataFrame,
    *,
    cluster_column: str,
    label_column: str,
    prediction_columns: dict[str, str],
    comparison: tuple[str, str],
    replications: int,
) -> pd.DataFrame:
    required = {cluster_column, label_column, *prediction_columns.values()}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Bootstrap fields are missing: {missing}")
    if replications < 1:
        raise ValueError("Bootstrap replications must be positive")
    if len(prediction_columns) < 2 or comparison[0] not in prediction_columns or comparison[1] not in prediction_columns:
        raise ValueError("The paired comparison must name two registered prediction columns")
    data = frame[[cluster_column, label_column, *prediction_columns.values()]].copy()
    if data.isna().any().any():
        raise ValueError("Bootstrap inputs cannot contain missing clusters, labels, or predictions")
    labels = pd.to_numeric(data[label_column], errors="raise")
    if not labels.isin([0, 1]).all() or labels.nunique() != 2:
        raise ValueError("Observed bootstrap labels must be binary and contain both classes")
    for name, column in prediction_columns.items():
        values = pd.to_numeric(data[column], errors="raise")
        if not np.isfinite(values).all() or not values.between(0, 1).all():
            raise ValueError(f"Prediction column {name} must contain finite probabilities in [0, 1]")
    data[label_column] = labels.astype("int8")
    return data.reset_index(drop=True)


def paired_cluster_bootstrap_ap(
    frame: pd.DataFrame,
    *,
    cluster_column: str,
    label_column: str,
    prediction_columns: dict[str, str],
    comparison: tuple[str, str],
    replications: int = 5_000,
    seed: int = 754,
    return_replications: bool = False,
) -> BootstrapResult:
    """Bootstrap AP by resampling whole clusters and comparing models on paired draws."""
    data = _validate_inputs(
        frame,
        cluster_column=cluster_column,
        label_column=label_column,
        prediction_columns=prediction_columns,
        comparison=comparison,
        replications=replications,
    )
    labels = data[label_column].to_numpy(dtype=int)
    predictions = {
        name: data[column].to_numpy(dtype=float) for name, column in prediction_columns.items()
    }
    observed = {
        name: float(average_precision_score(labels, values))
        for name, values in predictions.items()
    }
    cluster_rows = _cluster_row_indices(data, cluster_column)
    rng = np.random.default_rng(seed)
    values: dict[str, list[float]] = {name: [] for name in prediction_columns}
    invalid = 0
    for _ in range(replications):
        rows = _draw_cluster_rows(cluster_rows, rng)
        sampled_labels = labels[rows]
        if np.unique(sampled_labels).size != 2:
            invalid += 1
            continue
        for name, model_predictions in predictions.items():
            values[name].append(
                float(average_precision_score(sampled_labels, model_predictions[rows]))
            )
    valid = replications - invalid
    if valid < 2:
        raise ValueError("Fewer than two valid bootstrap replications contain both target classes")

    replications_frame = pd.DataFrame(values)
    higher, lower = comparison
    difference_name = f"{higher}_minus_{lower}"
    replications_frame[difference_name] = replications_frame[higher] - replications_frame[lower]
    observed_difference = observed[higher] - observed[lower]
    summary_rows = []
    for name, estimate in (*observed.items(), (difference_name, observed_difference)):
        distribution = replications_frame[name].to_numpy(dtype=float)
        summary_rows.append(
            {
                "estimand": name,
                "observed": estimate,
                "bootstrap_mean": float(distribution.mean()),
                "bootstrap_median": float(np.median(distribution)),
                "bootstrap_se": float(distribution.std(ddof=1)),
                "ci_low": float(np.quantile(distribution, 0.025)),
                "ci_high": float(np.quantile(distribution, 0.975)),
            }
        )
    difference = replications_frame[difference_name]
    diagnostics: dict[str, float | int] = {
        "seed": seed,
        "requested_replications": replications,
        "valid_replications": valid,
        "invalid_replications": invalid,
        "cluster_count": len(cluster_rows),
        f"proportion_{higher}_greater_{lower}": float((difference > 0).mean()),
        f"proportion_{lower}_greater_{higher}": float((difference < 0).mean()),
        "proportion_difference_equal_zero": float((difference == 0).mean()),
        "proportion_difference_gt_0_01": float((difference > 0.01).mean()),
        "proportion_difference_gt_0_02": float((difference > 0.02).mean()),
        "proportion_difference_gt_0_05": float((difference > 0.05).mean()),
    }
    return BootstrapResult(
        summary=pd.DataFrame(summary_rows),
        diagnostics=diagnostics,
        replications=replications_frame if return_replications else None,
    )
