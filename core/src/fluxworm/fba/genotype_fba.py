"""Runs constrained FBA for a single genotype.

Uses cobrapy's `with model:` context manager so that bound changes applied
for one genotype are automatically rolled back before the next genotype is
evaluated -- this is what the old project code's `with model as mutant_model:`
pattern was reaching for, except here the context actually contains real
bound edits (`flux_constraint_builder.apply_bounds`) rather than a knockout
call that always silently no-op'd.
"""

from __future__ import annotations

from dataclasses import dataclass

import cobra
import pandas as pd

from fluxworm.constraints.flux_constraint_builder import apply_bounds


@dataclass
class FBAResult:
    genotype: str
    status: str
    objective_value: float | None
    fluxes: pd.Series | None


def run_single(model: cobra.Model, genotype: str, bounds_table: pd.DataFrame | None) -> FBAResult:
    """Run FBA for one genotype. `bounds_table` is None for the wild-type
    reference run (no scaling applied, i.e. the model's original bounds).
    """
    with model:
        if bounds_table is not None:
            apply_bounds(model, bounds_table)
        solution = model.optimize()

        if solution.status != "optimal":
            return FBAResult(genotype=genotype, status=solution.status, objective_value=None, fluxes=None)

        return FBAResult(
            genotype=genotype,
            status=solution.status,
            objective_value=solution.objective_value,
            fluxes=solution.fluxes.copy(),
        )
