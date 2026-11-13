"""Compares the model's predicted lifespans with lifespans measured in the lab.

Reads `core/data/lifespan_reference.csv` (mean lifespan change vs wild type
per genotype, with sources) and reports, for every genotype with a measured
value, the model's prediction and its error. It also reports what the
lifespan exponent would be if it were fitted to these measurements, and the
leave-one-out error of that fit, so the cost of calibrating on so few data
points is visible. The pipeline itself uses the fixed exponent from the
config, not the fitted one.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from fluxworm.aging.survival_model import AgingProxyResult


def load_lifespan_reference(path: str | Path) -> pd.Series:
    """Return measured lifespan as a multiple of wild type, indexed by genotype.

    Genotypes whose change is blank in the file (no published number) are dropped.
    """
    table = pd.read_csv(path, index_col="genotype")
    measured = 1.0 + table["mean_lifespan_change_pct"].dropna() / 100.0
    measured.name = "measured_scale"
    return measured


def _fit_exponent(x: np.ndarray, y: np.ndarray) -> float:
    """Least-squares exponent k for log(lifespan) = k * (-log(growth)), through the origin."""
    denom = float(np.sum(x * x))
    return float(np.sum(x * y) / denom) if denom > 0 else float("nan")


def validate_against_reference(
    proxies: dict[str, AgingProxyResult],
    measured: pd.Series,
    reference_genotype: str,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Return (per-genotype comparison table, summary numbers)."""
    rows = []
    for genotype, proxy in proxies.items():
        if genotype == reference_genotype or genotype not in measured.index:
            continue
        lab = float(measured[genotype])
        rows.append(
            {
                "genotype": genotype,
                "growth_ratio": proxy.growth_ratio,
                "predicted_scale": proxy.lifespan_scale,
                "measured_scale": lab,
                "error_pct": (proxy.lifespan_scale / lab - 1.0) * 100.0,
            }
        )
    table = pd.DataFrame(rows).set_index("genotype") if rows else pd.DataFrame()
    if table.empty:
        return table, {}

    x = -np.log(table["growth_ratio"].to_numpy())
    y = np.log(table["measured_scale"].to_numpy())
    fitted = _fit_exponent(x, y)

    # Leave-one-out: refit without each genotype, then predict it
    loo_errors = []
    for i in range(len(table)):
        keep = np.arange(len(table)) != i
        k = _fit_exponent(x[keep], y[keep])
        if np.isfinite(k):
            loo_errors.append(abs(np.exp(k * x[i]) / np.exp(y[i]) - 1.0) * 100.0)
    table["fitted_exponent_loo_error_pct"] = loo_errors if len(loo_errors) == len(table) else np.nan

    summary = {
        "n_genotypes": float(len(table)),
        "mean_abs_error_pct": float(table["error_pct"].abs().mean()),
        "fitted_exponent": fitted,
        "fitted_exponent_loo_mean_abs_error_pct": float(np.mean(loo_errors)) if loo_errors else float("nan"),
    }
    return table, summary
