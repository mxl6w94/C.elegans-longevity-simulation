"""Turns per-gene differential expression into per-reaction flux bound scalings.

This is the heart of the transcriptomics-constrained FBA approach and the
step that most needs its assumptions stated plainly (this is a fold-change
-referenced adaptation of E-Flux, Colijn et al. 2009 -- see the architecture
document, section 1, for the full justification versus iMAT/GIMME).

Pipeline, per mutant genotype:

1. gene score = clip(2^log2fc, min_scale, max_scale) for genes with
   expression evidence (see `differential_expression`); genes without
   evidence get a neutral score of 1.0.
2. reaction score S_r = GPR-weighted combination of its genes' scores
   (`gpr_scoring.evaluate_gpr_score`); reactions with no GPR get S_r = None
   and are excluded from scaling entirely.
3. new_bound = sign(bound) * reference_capacity_r * S_r, applied to both lb
   and ub.

Reactions excluded from scaling (no GPR: exchanges, transport, spontaneous
reactions, and the biomass reaction `BIO0010` itself) keep their original
bounds unconditionally -- this is a documented modeling choice, not a gap:
scaling the biomass objective's own bounds directly, or arbitrarily
constraining reactions with no gene-level evidence, would misattribute the
mutation's actual mechanism.

`reference_capacity_r` -- the magnitude scaled against -- defaults to the
reaction's own model bound (`max(|lb|, |ub|)`), matching a literal reading
of E-Flux. In practice, for iCEL1314, that default was verified to be a
mathematical no-op: the model uses a placeholder bound of +-1000 on nearly
every reaction while actual optimal-growth flux magnitudes run ~1e-3 to
1e-6, so no realistic fold-change can shrink 1000 down far enough to bind.
`fluxworm.pipeline` therefore passes `reference_capacities` computed by
`fluxworm.constraints.reference_flux.compute_wt_reference_capacities`
(wild-type FVA range per reaction) instead -- see that module's docstring
for the full diagnosis and justification. The parameter stays optional here
(falling back to the model-bound behavior) so this function's unit tests
can exercise the scaling logic in isolation without running FVA.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from fluxworm.constraints.gpr_scoring import score_all_reactions


def gene_scores_from_de(de_table: pd.DataFrame, min_scale: float, max_scale: float) -> dict[str, float]:
    """Convert a differential-expression table (see
    `differential_expression.differential_expression`) into
    {gene_id: score}. Only genes with evidence=True get a non-neutral score.
    """
    scores: dict[str, float] = {}
    evidenced = de_table[de_table["evidence"]]
    for gene_id, row in evidenced.iterrows():
        raw_score = 2.0 ** row["log2fc"]
        scores[gene_id] = float(np.clip(raw_score, min_scale, max_scale))
    return scores


def build_reaction_bounds(
    model,
    gene_scores: dict[str, float],
    reference_capacities: pd.Series | None = None,
) -> pd.DataFrame:
    """Return a DataFrame indexed by reaction_id with columns:
    original_lb, original_ub, score (NaN if unscaled), reference_capacity,
    new_lb, new_ub.

    `reference_capacities`, if given, is a Series indexed by reaction_id
    (e.g. from `reference_flux.compute_wt_reference_capacities`) giving the
    magnitude each reaction's scaled bound is computed against, in place of
    that reaction's own model bound.
    """
    reaction_scores = score_all_reactions(model, gene_scores)

    records = []
    for rxn in model.reactions:
        score = reaction_scores[rxn.id]
        lb, ub = rxn.bounds
        if reference_capacities is not None:
            reference_lb = reference_ub = float(reference_capacities.get(rxn.id, max(abs(lb), abs(ub))))
        else:
            # Fall back to each direction's own model bound magnitude
            # (the originally approved formula), so callers that don't
            # supply FVA-derived reference capacities -- e.g. this
            # function's own unit tests -- see unchanged behavior.
            reference_lb, reference_ub = abs(lb), abs(ub)
        if score is None:
            new_lb, new_ub = lb, ub
        else:
            new_lb = np.sign(lb) * reference_lb * score
            new_ub = np.sign(ub) * reference_ub * score
        records.append(
            {
                "reaction_id": rxn.id,
                "original_lb": lb,
                "original_ub": ub,
                "score": score if score is not None else np.nan,
                "reference_capacity": max(reference_lb, reference_ub),
                "new_lb": new_lb,
                "new_ub": new_ub,
            }
        )

    df = pd.DataFrame.from_records(records).set_index("reaction_id")

    assert not df["new_lb"].isna().any() and not df["new_ub"].isna().any(), "NaN bound produced during scaling"
    new_infs = np.isinf(df["new_lb"]) & ~np.isinf(df["original_lb"])
    assert not new_infs.any(), "scaling introduced an infinite bound that was not already infinite"

    return df


def apply_bounds(model, bounds_table: pd.DataFrame) -> None:
    """Apply new_lb/new_ub from `bounds_table` onto `model` in place.

    Callers are expected to invoke this inside a `with model:` context so
    changes are automatically reverted before the next genotype is run
    (see `fluxworm.fba.genotype_fba`).
    """
    for reaction_id, row in bounds_table.iterrows():
        model.reactions.get_by_id(reaction_id).bounds = (row["new_lb"], row["new_ub"])
