"""Orchestrates constrained FBA across all five genotypes.

On an infeasible/non-optimal result for a mutant genotype, this logs the
failure (genotype, min/max applied scale factors) and continues with the
remaining genotypes rather than crashing the whole pipeline run -- an
overly aggressive constraint scaling for one genotype should not prevent
reporting results for the others.
"""

from __future__ import annotations

import logging

import cobra
import pandas as pd

from fluxworm.fba.genotype_fba import FBAResult, run_single

logger = logging.getLogger(__name__)


def run_all_genotypes(
    model: cobra.Model,
    reference_genotype: str,
    bounds_by_genotype: dict[str, pd.DataFrame],
) -> dict[str, FBAResult]:
    results: dict[str, FBAResult] = {}

    results[reference_genotype] = run_single(model, reference_genotype, bounds_table=None)
    if results[reference_genotype].status != "optimal":
        raise RuntimeError(
            f"Wild-type reference FBA failed with status={results[reference_genotype].status}. "
            "Cannot proceed to mutant genotypes without a working WT baseline."
        )

    for genotype, bounds_table in bounds_by_genotype.items():
        result = run_single(model, genotype, bounds_table)
        if result.status != "optimal":
            scored = bounds_table["score"].dropna()
            logger.warning(
                "Genotype '%s' FBA did not reach optimality (status=%s). "
                "Applied score range: min=%.4f max=%.4f (n_scaled_reactions=%d).",
                genotype,
                result.status,
                scored.min() if not scored.empty else float("nan"),
                scored.max() if not scored.empty else float("nan"),
                len(scored),
            )
        results[genotype] = result

    return results
