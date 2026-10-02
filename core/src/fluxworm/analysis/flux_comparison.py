"""Assembles cross-genotype flux and growth comparison tables from FBA results."""

from __future__ import annotations

import numpy as np
import pandas as pd

from fluxworm.fba.genotype_fba import FBAResult


def growth_comparison_table(results: dict[str, FBAResult], reference_genotype: str) -> pd.DataFrame:
    """One row per genotype: status, biomass flux, and fold-change vs. WT."""
    wt_growth = results[reference_genotype].objective_value

    rows = []
    for genotype, result in results.items():
        growth = result.objective_value
        fold_change = (growth / wt_growth) if (growth is not None and wt_growth) else np.nan
        rows.append(
            {
                "genotype": genotype,
                "status": result.status,
                "biomass_flux": growth,
                "fold_change_vs_wt": fold_change,
            }
        )
    return pd.DataFrame(rows).set_index("genotype")


def flux_table(results: dict[str, FBAResult]) -> pd.DataFrame:
    """reaction_id x genotype matrix of flux values (NaN for non-optimal runs)."""
    series = {}
    for genotype, result in results.items():
        series[genotype] = result.fluxes if result.fluxes is not None else pd.Series(dtype=float)
    return pd.DataFrame(series)


def flux_fold_change_vs_wt(flux_df: pd.DataFrame, reference_genotype: str, epsilon: float = 1e-6) -> pd.DataFrame:
    """Per-reaction |flux| fold-change of each mutant vs. WT, using an epsilon
    floor on the denominator so near-zero WT fluxes don't blow up the ratio
    into an uninterpretable value.

    The default epsilon (1e-6) is chosen relative to this model's actual
    flux scale, not an arbitrary numerical-stability constant: iCEL1314's
    optimal-growth flux magnitudes run roughly 1e-3 to 1e-6 (see
    `fluxworm.constraints.reference_flux` for how this was established), so
    a floor several orders of magnitude smaller than that (e.g. 1e-9) still
    lets reactions with a genuinely negligible WT flux produce enormous,
    uninterpretable fold-change values.
    """
    wt = flux_df[reference_genotype].abs()
    result = pd.DataFrame(index=flux_df.index)
    for genotype in flux_df.columns:
        if genotype == reference_genotype:
            continue
        result[genotype] = flux_df[genotype].abs() / (wt + epsilon)
    return result
